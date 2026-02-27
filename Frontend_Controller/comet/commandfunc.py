# robot_commands.py

import asyncio
from queue import Queue, Empty
from typing import Any, Dict
import sportfunc
import threading

# === Globals ===
command_queue = Queue()
command_running = False
_original_loop: asyncio.AbstractEventLoop = None   # will hold main loop

AVAILABLE_COMMANDS = {
    "damp": sportfunc.damp,
    "balance_stand": sportfunc.balance_stand,
    "stop_move": sportfunc.stop_move,
    "stand_up": sportfunc.stand_up,
    "stand_down": sportfunc.stand_down,
    "recovery_stand": sportfunc.recovery_stand,
    "euler": sportfunc.euler,
    "move": sportfunc.move,
    "sit": sportfunc.sit,
    "rise_sit": sportfunc.rise_sit,
    "hello": sportfunc.hello,
    "stretch": sportfunc.stretch,
    "content": sportfunc.content,
    "dance1": sportfunc.dance1,
    "dance2": sportfunc.dance2,
    "scrape": sportfunc.scrape,
    "frontflip": sportfunc.frontflip,
    "front_jump": sportfunc.front_jump,
    "front_pounce": sportfunc.front_pounce,
    "heart": sportfunc.heart,
    "staticwalk": sportfunc.staticwalk,
    "trotrun": sportfunc.trotrun,
    "economicgate": sportfunc.economicgate,
    "leftflip": sportfunc.leftflip,
    "rightflip": sportfunc.rightflip,
    "backflip": sportfunc.backflip,
    "handstand": sportfunc.handstand,
    "classicwalk": sportfunc.classicwalk,
    "walkupright": sportfunc.walkupright,
    "crossstep": sportfunc.crossstep,
}


def start_command_processor(conn):
    """Capture the main loop and spawn a worker thread."""
    global command_running, _original_loop
    if command_running:
        print("[COMMAND] already running")
        return

    # grab whichever loop we're currently in (the one where we connected)
    _original_loop = asyncio.get_event_loop()
    command_running = True
    threading.Thread(target=_command_worker, args=(conn,), daemon=True).start()
    print("[COMMAND] processor started on loop", _original_loop)

def stop_command_processor():
    global command_running
    command_running = False
    cleared = 0
    while not command_queue.empty():
        try:
            command_queue.get_nowait()
            cleared += 1
        except Empty:
            break
    print(f"[COMMAND] processor stopped, cleared {cleared} queued commands")

def add_command(data: Dict[str, Any]) -> Dict[str, Any]:
    if not command_running:
        return {"status": "error", "message": "processor not running"}
    name = data.get("command")
    if name not in AVAILABLE_COMMANDS:
        return {"status": "error", "message": f"Unknown command: {name}"}
    command_queue.put(data)
    size = command_queue.qsize()
    print(f"[COMMAND] queued '{name}' (size={size})")
    return {"status":"success","message":f"'{name}' queued","queue_size":size}

def clear_command_queue() -> Dict[str, Any]:
    count = 0
    while not command_queue.empty():
        try:
            command_queue.get_nowait()
            count += 1
        except Empty:
            break
    print(f"[COMMAND] cleared {count} commands")
    return {"status":"success","message":f"Cleared {count} commands"}

def get_queue_status() -> Dict[str, Any]:
    return {
        "status":"success",
        "queue_size": command_queue.qsize(),
        "processor_running": command_running,
        "available_commands": list(AVAILABLE_COMMANDS.keys())
    }

def handle_server_command(msg: Dict[str, Any]) -> Dict[str, Any]:
    t = msg.get("type")
    if t == "execute_command":
        return add_command(msg.get("data", {}))
    if t == "clear_queue":
        return clear_command_queue()
    if t == "queue_status":
        return get_queue_status()
    return {"status":"error","message":f"Unknown command type: {t}"}


def _command_worker(conn):
    print("[COMMAND] worker thread starting")
    try:
        while command_running:
            try:
                cmd = command_queue.get(timeout=0.1)
            except Empty:
                continue

            name = cmd["command"]
            params = cmd.get("parameters", {}) or {}
            print(f"[COMMAND] dispatching '{name}' with {params}")

            coro = _run_single(cmd_name=name, params=params, conn=conn)
            # Schedule on the original loop
            fut = asyncio.run_coroutine_threadsafe(coro, _original_loop)
            try:
                fut.result()  # wait for it
            except Exception as e:
                print(f"[COMMAND] '{name}' failed: {e}")

            command_queue.task_done()

    finally:
        print("[COMMAND] worker thread exiting")


async def _run_single(cmd_name: str, params: Dict[str,Any], conn) -> None:
    fn = AVAILABLE_COMMANDS.get(cmd_name)
    if not fn:
        print(f"[COMMAND] No such command '{cmd_name}'")
        return

    print(f"[COMMAND] executing '{cmd_name}'…")
    try:
        if cmd_name == "euler":
            await fn(conn, params.get("angles", [0,0,0]))
        elif cmd_name == "move":
            await fn(conn, params.get("movement", [0,0,0]))
            duration = params.get("duration")
            if duration:
                await asyncio.sleep(duration)
            if params.get("stop_after"):
                await sportfunc.stop_move(conn)
        elif cmd_name == "handstand":
            await fn(conn, params.get("length", 3))
        elif cmd_name in ("walkupright","crossstep"):
            await fn(conn, params.get("time", 5))
        elif cmd_name == "sit":
            await fn(conn, params.get("time", 5))
        elif cmd_name == "stand_down":
            await fn(conn, params.get("time", 5))
        else:
            await fn(conn)
        print(f"[COMMAND] '{cmd_name}' complete")
    except Exception as e:
        print(f"[COMMAND] exception during '{cmd_name}': {e}")

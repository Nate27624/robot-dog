import json
import logging
import os
import socket
import struct
import threading
import time
from queue import Empty, Queue

from commandfunc import handle_server_command
from logfunc import log_to_file

try:
    import numpy as np
except ImportError:  # pragma: no cover - optional dependency at runtime
    np = None


DEFAULT_SERVER_HOST = "8.tcp.ngrok.io"
DEFAULT_SERVER_PORT = 17400
SERVER_ENDPOINT = os.getenv("COMET_SOCKET_ENDPOINT", "").strip()

if SERVER_ENDPOINT and ":" in SERVER_ENDPOINT:
    host, port_text = SERVER_ENDPOINT.rsplit(":", 1)
    SERVER_HOST = host.strip() or DEFAULT_SERVER_HOST
    try:
        SERVER_PORT = int(port_text.strip())
    except ValueError:
        SERVER_PORT = DEFAULT_SERVER_PORT
else:
    SERVER_HOST = os.getenv("COMET_SERVER_HOST", DEFAULT_SERVER_HOST).strip()
    try:
        SERVER_PORT = int(os.getenv("COMET_SERVER_PORT", str(DEFAULT_SERVER_PORT)))
    except ValueError:
        SERVER_PORT = DEFAULT_SERVER_PORT


message_queue = Queue()
socket_conn = None
socket_running = False


def _json_default(value):
    if np is not None:
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def start_socket_connection():
    """Open the socket and start both send & receive threads."""
    global socket_conn, socket_running

    if socket_running:
        logging.warning("[SOCKET] already running")
        return

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_HOST, SERVER_PORT))
        sock.setblocking(True)
        socket_conn = sock
        socket_running = True
        logging.info(f"[SOCKET] Connected to {SERVER_HOST}:{SERVER_PORT}")

        threading.Thread(target=_send_loop, daemon=True).start()
        threading.Thread(target=_receive_loop, daemon=True).start()

    except Exception as e:
        logging.error(f"[SOCKET] Connection error: {e}")
        socket_running = False


def stop_socket_connection():
    """Signal threads to stop and close the socket."""
    global socket_running, socket_conn
    socket_running = False
    message_queue.put(None)

    if socket_conn:
        try:
            socket_conn.shutdown(socket.SHUT_RDWR)
            socket_conn.close()
        except Exception:
            pass
        socket_conn = None
    logging.info("[SOCKET] Connection closed")


def send_message(payload, message_type="unknown"):
    """Enqueue a payload to be serialized as length-prefixed JSON."""
    if not socket_running:
        logging.error("[SOCKET] not running")
        return False

    import copy

    log_payload = copy.deepcopy(payload)
    log_to_file(log_payload, message_type)
    message_queue.put((payload, message_type))
    return True


def _send_loop():
    """Thread: pull payloads from queue and send length-prefixed JSON."""
    global socket_conn, socket_running
    logging.info("[SOCKET] Send loop started")

    while socket_running:
        try:
            item = message_queue.get(timeout=0.1)
        except Empty:
            continue

        if item is None:
            break

        payload, message_type = item
        try:
            data = json.dumps(payload, default=_json_default, separators=(",", ":")).encode("utf-8")
            header = struct.pack(">I", len(data))
            socket_conn.sendall(header + data)
            logging.info(f"[SOCKET] Sent {message_type} as JSON ({len(data)} bytes)")
        except Exception as e:
            logging.error(f"[SOCKET] send error: {e}")
            socket_running = False
            break
        finally:
            message_queue.task_done()

    logging.info("[SOCKET] Send loop exiting")


def _receive_loop():
    """Thread: recv JSON lines, dispatch to handle_server_command."""
    global socket_conn, socket_running
    buffer = ""

    logging.info("[SOCKET] Receive loop started")
    while socket_running:
        try:
            chunk = socket_conn.recv(4096)
            if not chunk:
                logging.warning("[SOCKET] Server closed connection")
                break

            buffer += chunk.decode("utf-8", errors="ignore")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                _handle_incoming_json(line.strip())

        except Exception as e:
            logging.error(f"[SOCKET] recv error: {e}")
            socket_running = False
            break

    logging.info("[SOCKET] Receive loop exiting")


def _handle_incoming_json(message_str):
    """Parse a JSON command and queue a length-prefixed response payload."""
    try:
        cmd = json.loads(message_str)
        print(f"[SOCKET] Received command: {cmd}")

        resp = handle_server_command(cmd)
        response_type = "command_response" if resp.get("status") == "success" else "error_response"
        response_payload = {
            "type": response_type,
            "message": resp.get("message", ""),
            "response": resp,
            "timestamp": time.time(),
        }
        message_queue.put((response_payload, response_type))
        logging.info(f"[SOCKET] Queued response: {resp}")

    except json.JSONDecodeError as e:
        logging.error(f"[SOCKET] JSON decode error: {e}")
        response_payload = {
            "type": "error_response",
            "message": "Invalid JSON format",
            "timestamp": time.time(),
        }
        message_queue.put((response_payload, "error_response"))
    except Exception as e:
        logging.error(f"[SOCKET] handle command error: {e}")
        response_payload = {
            "type": "error_response",
            "message": f"Error processing command: {str(e)}",
            "timestamp": time.time(),
        }
        message_queue.put((response_payload, "error_response"))

import socket
import json
import time
import logging
import threading
import struct
import pickle
from queue import Queue, Empty
from logfunc import log_to_file
from commandfunc import handle_server_command

# === Connection Settings ===
SERVER_HOST = "8.tcp.ngrok.io"
SERVER_PORT = 17400

# === Globals ===
message_queue = Queue()
socket_conn = None
socket_running = False

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

        # Launch threads
        threading.Thread(target=_send_loop, daemon=True).start()
        threading.Thread(target=_receive_loop, daemon=True).start()

    except Exception as e:
        logging.error(f"[SOCKET] Connection error: {e}")
        socket_running = False

def stop_socket_connection():
    """Signal threads to stop and close the socket."""
    global socket_running, socket_conn
    socket_running = False
    # wake up send loop
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
    """Enqueue a payload to be pickled & sent."""
    if not socket_running:
        logging.error("[SOCKET] not running")
        return False

    import copy
    log_payload = copy.deepcopy(payload)
    log_to_file(log_payload, message_type)

    message_queue.put((payload, message_type))
    return True

def _send_loop():
    """Thread: pull from message_queue, send using appropriate protocol."""
    global socket_conn, socket_running
    logging.info("[SOCKET] Send loop started")

    while socket_running:
        try:
            item = message_queue.get(timeout=0.1)
        except Empty:
            continue

        if item is None:
            break  # shutdown signal

        payload, message_type = item
        try:
            # Command responses and errors should be sent as JSON
            if message_type in ["command_response", "error_response"]:
                data = json.dumps(payload) + '\n'
                socket_conn.sendall(data.encode('utf-8'))
                logging.info(f"[SOCKET] Sent {message_type} as JSON ({len(data)} bytes)")
            else:
                # Robot data sent as pickle with length prefix
                data = pickle.dumps(payload)
                header = struct.pack('>I', len(data))
                socket_conn.sendall(header + data)
                logging.info(f"[SOCKET] Sent {message_type} as pickle ({len(data)} bytes)")
        except Exception as e:
            logging.error(f"[SOCKET] send error: {e}")
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

            buffer += chunk.decode('utf-8', errors='ignore')

            # process all full lines
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                _handle_incoming_json(line.strip())

        except Exception as e:
            logging.error(f"[SOCKET] recv error: {e}")
            break

    logging.info("[SOCKET] Receive loop exiting")

def _handle_incoming_json(message_str):
    """Parse a JSON command and queue the response."""
    try:
        cmd = json.loads(message_str)
        print(f"[SOCKET] Received command: {cmd}")

        resp = handle_server_command(cmd)
        
        # Queue the response instead of sending directly
        # This prevents interference with the main send loop
        message_queue.put((resp, "command_response"))
        logging.info(f"[SOCKET] Queued response: {resp}")

    except json.JSONDecodeError as e:
        logging.error(f"[SOCKET] JSON decode error: {e}")
        error_resp = {"status": "error", "message": "Invalid JSON format"}
        message_queue.put((error_resp, "error_response"))
    except Exception as e:
        logging.error(f"[SOCKET] handle command error: {e}")
        error_resp = {"status": "error", "message": f"Error processing command: {str(e)}"}
        message_queue.put((error_resp, "error_response"))
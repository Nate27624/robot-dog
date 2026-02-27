import base64
import json
import socket
import struct
import threading

import cv2
import numpy as np


latest_frame = None
frame_lock = threading.Lock()
latest_robot_data = {}
data_lock = threading.Lock()

active_client_socket = None
active_socket_lock = threading.Lock()


def handle_payload(obj):
    global latest_frame, latest_robot_data

    payload_type = obj.get("type", "")

    if payload_type == "frame_with_data":
        try:
            encoded_data = obj["frame"]["data"]
            jpg_bytes = base64.b64decode(encoded_data)
            np_arr = np.frombuffer(jpg_bytes, dtype=np.uint8)
            decoded_frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"[SERVER ERROR] Failed decoding image frame: {e}")
            decoded_frame = None

        robot_data = obj.get("robot_data")

        with frame_lock:
            if decoded_frame is not None:
                latest_frame = decoded_frame

        if robot_data is not None:
            with data_lock:
                latest_robot_data = robot_data

    elif payload_type == "data_only":
        robot_data = obj.get("robot_data")
        if robot_data is not None:
            with data_lock:
                latest_robot_data = robot_data

    elif payload_type in {"command_response", "error_response"}:
        message = obj.get("message", "")
        print(f"[SERVER] Client response ({payload_type}): {message}")

    else:
        print(f"[SERVER] Unknown payload type: {payload_type}")


def handle_client(client_socket, addr):
    global active_client_socket
    print(f"[SERVER] Connected to {addr}")

    with active_socket_lock:
        active_client_socket = client_socket

    buffer = b""

    while True:
        try:
            while len(buffer) < 4:
                data = client_socket.recv(4096)
                if not data:
                    print("[SERVER] Client disconnected during length prefix")
                    return
                buffer += data

            msg_len = struct.unpack(">I", buffer[:4])[0]
            buffer = buffer[4:]

            while len(buffer) < msg_len:
                data = client_socket.recv(4096)
                if not data:
                    print("[SERVER] Client disconnected during payload reception")
                    return
                buffer += data

            payload = buffer[:msg_len]
            buffer = buffer[msg_len:]

            try:
                obj = json.loads(payload.decode("utf-8"))
            except Exception as e:
                print(f"[SERVER ERROR] Failed to decode JSON payload from {addr}: {e}")
                continue

            handle_payload(obj)
            print(f"[SERVER] Received data from {addr}")

        except Exception as e:
            print(f"[SERVER ERROR] Client {addr} disconnected or errored: {e}")
            break

    client_socket.close()
    print(f"[SERVER] Connection to {addr} closed")

    with active_socket_lock:
        if active_client_socket == client_socket:
            active_client_socket = None


def start_data_reception(host="0.0.0.0", port=5021):
    """Start the server to receive robot dog data (video frames + telemetry)."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"[SERVER] Listening on {host}:{port}")

    while True:
        client_socket, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()


def send_json_command_to_client(command_dict):
    """Send a JSON command message to the robot client over the active socket."""
    global active_client_socket

    message = json.dumps(command_dict) + "\n"

    with active_socket_lock:
        client_socket = active_client_socket

    if client_socket is None:
        print("[SERVER ERROR] No active client socket to send command")
        return {"status": "error", "message": "No active robot connection"}

    try:
        client_socket.sendall(message.encode("utf-8"))
        print(f"[SERVER] Sent command: {message.strip()}")
        command_name = command_dict.get("data", {}).get("command", command_dict.get("type", "unknown"))
        return {"status": "success", "message": f"Command sent: {command_name}"}
    except Exception as e:
        with active_socket_lock:
            if active_client_socket is client_socket:
                active_client_socket = None
        print(f"[SERVER ERROR] Failed to send command: {e}")
        return {"status": "error", "message": str(e)}


def get_latest_robot_data_threadsafe():
    with data_lock:
        return dict(latest_robot_data)

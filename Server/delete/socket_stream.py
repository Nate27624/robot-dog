import os
import json
import time
import socket
from PIL import Image
from queue import Queue
import numpy as np
import cv2
import threading
import base64
from robot_data_parser import RobotDataParser
from robot_ui import RobotDataUI

# === Globals ===
frame_lock = threading.Lock()
latest_frame = None
robot_parser = RobotDataParser()
robot_ui = RobotDataUI(robot_parser)
client_connection = None  # Store the client connection for sending commands
connection_lock = threading.Lock()  # Lock for thread-safe connection access
command_queue = Queue()  # Queue for outgoing commands
connection_active = threading.Event()  # Event to track connection status

# === Configuration ===
# Set this to True to enable logging of all robot data to file
ENABLE_LOGGING = False  # Disabled for better performance

# Directory for raw message logs
RAW_LOG_DIR = "raw_logs"

# Log only every Nth message to reduce performance impact
LOG_FREQUENCY = 10  # More frequent logging for debugging
message_counter = 0

# Delete old logs on startup
def clean_logs():
    import shutil
    if os.path.exists(RAW_LOG_DIR):
        print(f"[SOCKET] Cleaning old logs from {RAW_LOG_DIR}")
        shutil.rmtree(RAW_LOG_DIR)
    os.makedirs(RAW_LOG_DIR, exist_ok=True)
    
    robot_log_dir = "robot_logs"
    if os.path.exists(robot_log_dir):
        print(f"[SOCKET] Cleaning old logs from {robot_log_dir}")
        shutil.rmtree(robot_log_dir)
    os.makedirs(robot_log_dir, exist_ok=True)

# === Image Receiving Socket Server ===
def image_stream_receiver():
    from app import HOST, SOCKET_PORT
    global latest_frame, ENABLE_LOGGING, message_counter
    
    # Clean old logs on startup
    clean_logs()

    print(f"[SOCKET] Starting image receiver on {HOST}:{SOCKET_PORT}")
    
    # Initialize logging if enabled
    if ENABLE_LOGGING:
        print("[SOCKET] Data logging is ENABLED")
        robot_parser.enable_logging(True)
    else:
        print("[SOCKET] Data logging is DISABLED")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        try:
            # Set socket options to prevent hanging
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.settimeout(None)  # No timeout for accept()
            
            server_socket.bind((HOST, SOCKET_PORT))
            server_socket.listen(1)
            
            # Keep accepting connections in a loop
            while True:
                print(f"[SOCKET] Waiting for client connection...")
                
                try:
                    conn, addr = server_socket.accept()
                    print(f"[SOCKET] Connection established with {addr}")
                    
                    # Handle this connection
                    handle_client_connection(conn, addr)
                    
                except Exception as e:
                    print(f"[SOCKET] Error accepting connection: {e}")
                    time.sleep(1)  # Wait before trying again

        except Exception as e:
            print(f"[SOCKET ERROR] Server error: {e}")

def handle_client_connection(conn, addr):
    """Handle a single client connection"""
    global latest_frame, ENABLE_LOGGING, message_counter
    
    try:
        # Set socket options for the connection
        conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        conn.settimeout(5)  # Shorter timeout to prevent hanging

        with conn:
            buffer = b""
            consecutive_errors = 0
            max_consecutive_errors = 5
            
            print("[SOCKET] Starting receive loop...")
            while True:
                try:
                    chunk = conn.recv(4096)
                    if not chunk:
                        print("[SOCKET] Client disconnected.")
                        # Close log file if we were logging
                        if ENABLE_LOGGING and robot_parser.logging_enabled:
                            robot_parser.enable_logging(False)
                        break

                    buffer += chunk
                    consecutive_errors = 0  # Reset error counter on successful recv
                    
                    # Print periodic receive status
                    if len(buffer) > 0 and message_counter % LOG_FREQUENCY == 0:
                        print(f"[SOCKET] Received {len(chunk)} bytes, buffer size: {len(buffer)}")
                    
                except socket.timeout:
                    print(f"[SOCKET] Receive timeout after 5 seconds - checking connection... (errors: {consecutive_errors})")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        print("[SOCKET] Too many consecutive timeouts, closing connection")
                        break
                    continue
                    
                except ConnectionResetError:
                    print("[SOCKET] Connection reset by peer")
                    break
                    
                except Exception as e:
                    print(f"[SOCKET] Receive error: {e}")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        print("[SOCKET] Too many consecutive errors, closing connection")
                        break
                    time.sleep(0.1)  # Brief pause before retrying
                    continue

                # Process each complete message in the buffer one at a time
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    try:
                        # Parse the message
                        message_str = line.decode('utf-8')
                        message_counter += 1
                        
                        # Parse JSON data
                        data = json.loads(message_str)
                        
                        # Store the data in the parser for UI display
                        robot_parser.latest_data = data
                        
                        # Log raw message occasionally if logging is enabled
                        if ENABLE_LOGGING and message_counter % LOG_FREQUENCY == 0:
                            if not os.path.exists(RAW_LOG_DIR):
                                os.makedirs(RAW_LOG_DIR)
                            timestamp = time.strftime("%Y%m%d_%H%M%S")
                            raw_log_file = os.path.join(RAW_LOG_DIR, f"raw_message_{timestamp}.json")
                            with open(raw_log_file, 'w') as f:
                                f.write(message_str)
                            print(f"[SOCKET] Raw message logged to {raw_log_file}")
                        
                        # Log parsed data if logging is enabled
                        if ENABLE_LOGGING and robot_parser.log_file and message_counter % LOG_FREQUENCY == 0:
                            try:
                                with open(robot_parser.log_file, 'a') as f:
                                    if os.path.getsize(robot_parser.log_file) > 2:
                                        f.write(",\n")
                                    json.dump(data, f, indent=2)
                            except Exception as e:
                                print(f"[SOCKET ERROR] Failed to log data: {e}")
                        
                        # Process frame data if present
                        frame_data = None
                        
                        # Look for frame in different locations
                        if 'frame' in data:
                            frame_info = data['frame']
                            if isinstance(frame_info, dict) and 'data' in frame_info:
                                frame_data = frame_info['data']
                            else:
                                frame_data = frame_info
                        elif 'robot_data' in data and isinstance(data['robot_data'], dict) and 'frame' in data['robot_data']:
                            frame_info = data['robot_data']['frame']
                            if isinstance(frame_info, dict) and 'data' in frame_info:
                                frame_data = frame_info['data']
                            else:
                                frame_data = frame_info
                        
                        # Decode and store frame if found
                        if frame_data and isinstance(frame_data, str):
                            if '[BASE64_IMAGE_DATA' in frame_data:
                                # Create placeholder for test data
                                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                                cv2.putText(placeholder, "Robot Dog Camera Feed", (120, 240), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                                with frame_lock:
                                    latest_frame = placeholder
                                if message_counter % LOG_FREQUENCY == 0:
                                    print("[SOCKET] Created placeholder image")
                            else:
                                try:
                                    # Decode actual frame data
                                    frame_bytes = base64.b64decode(frame_data)
                                    np_arr = np.frombuffer(frame_bytes, np.uint8)
                                    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

                                    if frame is not None:
                                        with frame_lock:
                                            latest_frame = frame
                                        if message_counter % LOG_FREQUENCY == 0:
                                            print("[SOCKET] Frame received and processed")
                                    else:
                                        if message_counter % LOG_FREQUENCY == 0:
                                            print("[SOCKET] Failed to decode frame")
                                except Exception as e:
                                    if message_counter % LOG_FREQUENCY == 0:
                                        print(f"[SOCKET ERROR] Frame decode error: {e}")
                        
                        # Print debug info more frequently to track processing
                        if message_counter % LOG_FREQUENCY == 0:
                            print(f"[SOCKET] Processed message {message_counter}, keys: {list(data.keys())}")
                        
                        # Always print frame processing status
                        if 'frame' in data:
                            print(f"[SOCKET] Frame data received in message {message_counter}")
                        elif message_counter % LOG_FREQUENCY == 0:
                            print(f"[SOCKET] No frame in message {message_counter}")

                    except Exception as e:
                        print(f"[SOCKET ERROR] Failed to process message: {e}")
                        if message_counter % LOG_FREQUENCY == 0:
                            import traceback
                            traceback.print_exc()
    
    except Exception as e:
        print(f"[SOCKET ERROR] Connection error with {addr}: {e}")
    finally:
        print(f"[SOCKET] Connection with {addr} closed")

# === Image Processor and Function Executor ===
def process_dog():
    """Process and display robot frames and data one at a time"""
    last_frame_hash = None
    show_ui = True
    frame_counter = 0
    
    # Create default frame
    default_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(default_frame, "Waiting for Robot Dog Camera Feed", (80, 240), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    print("[PROCESS] Starting frame processor...")
    time.sleep(1)  # Allow socket to initialize
    
    try:
        while True:
            try:
                current_frame = None
                frame_changed = False
                
                # Get the latest frame
                with frame_lock:
                    if latest_frame is not None:
                        current_frame = latest_frame.copy()
                        # Simple frame change detection using hash
                        current_hash = hash(current_frame.tobytes())
                        if current_hash != last_frame_hash:
                            frame_changed = True
                            last_frame_hash = current_hash
                            frame_counter += 1
                            print(f"[PROCESS] New frame received #{frame_counter}")
                
                # Use default frame if no data available
                if current_frame is None:
                    current_frame = default_frame
                    if frame_counter % 100 == 0:  # Print occasionally when waiting
                        print("[PROCESS] Still waiting for frames...")
                
                # Display frame and data
                if show_ui:
                    try:
                        key = robot_ui.show_side_by_side()
                    except Exception as e:
                        print(f"[PROCESS ERROR] UI error: {e}")
                        key = cv2.waitKey(1)
                else:
                    cv2.imshow("Robot Dog Feed", current_frame)
                    key = cv2.waitKey(1)
                
                # Exit on 'q' key
                if key == ord('q'):
                    print("[PROCESS] Exiting...")
                    cv2.destroyAllWindows()
                    break
                
                # Print status every few seconds
                if frame_counter > 0 and frame_counter % 100 == 0:
                    print(f"[PROCESS] Processed {frame_counter} frames so far")
                
            except Exception as e:
                print(f"[PROCESS ERROR] {e}")
                import traceback
                traceback.print_exc()
                time.sleep(0.1)
                
            time.sleep(0.03)  # ~30 FPS processing rate
            
    except KeyboardInterrupt:
        print("[PROCESS] Interrupted")
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"[PROCESS FATAL] {e}")
        cv2.destroyAllWindows()
#!/usr/bin/env python3
"""
Simple test client to send frames to the server
"""
import socket
import json
import time
import base64
import numpy as np
import cv2

def create_test_frame(frame_id):
    """Create a simple test frame with frame counter"""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add some visual elements
    cv2.rectangle(frame, (50, 50), (590, 430), (0, 255, 0), 2)
    cv2.putText(frame, f"Test Frame #{frame_id}", (150, 240), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, f"Time: {time.strftime('%H:%M:%S')}", (200, 300), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    # Encode to base64
    _, buffer = cv2.imencode('.jpg', frame)
    frame_b64 = base64.b64encode(buffer).decode('utf-8')
    return frame_b64

def main():
    HOST = '127.0.0.1'
    PORT = 5021
    
    print(f"[CLIENT] Connecting to {HOST}:{PORT}")
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT))
            print("[CLIENT] Connected to server")
            
            frame_counter = 0
            
            while True:
                try:
                    # Create test data with frame and robot data
                    test_data = {
                        "frame": create_test_frame(frame_counter),
                        "robot_data": {
                            "battery": 85.5 - (frame_counter * 0.1) % 20,
                            "temperature": 42.3 + (frame_counter * 0.05) % 10,
                            "position": {
                                "x": 1.2 + (frame_counter * 0.01) % 2,
                                "y": 0.8 + (frame_counter * 0.02) % 1.5,
                                "z": 0.3
                            },
                            "orientation": {
                                "roll": (frame_counter * 0.01) % 0.5,
                                "pitch": (frame_counter * 0.02) % 0.3,
                                "yaw": (frame_counter * 0.03) % 6.28
                            },
                            "status": "active",
                            "frame_id": frame_counter
                        }
                    }
                    
                    # Send the data
                    message = json.dumps(test_data) + '\n'
                    sock.sendall(message.encode('utf-8'))
                    
                    if frame_counter % 30 == 0:  # Print every 30 frames
                        print(f"[CLIENT] Sent frame {frame_counter}")
                    
                    frame_counter += 1
                    time.sleep(0.1)  # 10 FPS
                    
                except KeyboardInterrupt:
                    print("[CLIENT] Stopping...")
                    break
                except Exception as e:
                    print(f"[CLIENT ERROR] {e}")
                    break
                    
    except Exception as e:
        print(f"[CLIENT ERROR] {e}")

if __name__ == "__main__":
    main()
import cv2
import numpy as np
import base64
import json
import asyncio
import logging
import threading
import time
from queue import Queue
from go2_webrtc_driver.webrtc_driver import Go2WebRTCConnection, WebRTCConnectionMethod
from aiortc import MediaStreamTrack

# Import our custom modules
from telemetryfunc import get_telemetry_data, setup_telemetry
from logfunc import initialize_log_file
from socketfunc import SERVER_HOST, SERVER_PORT, start_socket_connection, send_message

# Queue for camera frames
frame_queue = Queue()

async def recv_camera_stream(track: MediaStreamTrack):
    """Callback function to receive camera frames"""
    while True:
        frame = await track.recv()
        img = frame.to_ndarray(format="bgr24")
        frame_queue.put(img)

def run_asyncio_loop(conn, loop):
    """Run the asyncio event loop for WebRTC connection"""
    asyncio.set_event_loop(loop)

    async def setup():
        try:
            # Connection is already established in app.py, just setup video
            logging.info("Setting up video channel...")
            
            # Switch video channel on and start receiving video frames
            conn.video.switchVideoChannel(True)
            conn.video.add_track_callback(recv_camera_stream)
            logging.info("WebRTC video setup complete.")
            
            # Setup telemetry data collection
            await setup_telemetry(conn)
            
        except Exception as e:
            logging.error(f"[WebRTC ERROR] {e}")

    loop.run_until_complete(setup())
    loop.run_forever()

def send_frames(conn):
    """Process camera frames and telemetry data and send to server via socket"""
    # Initialize logging
    initialize_log_file(SERVER_HOST, SERVER_PORT)
    
    # Start socket connection
    start_socket_connection()
    
    # Create a new event loop for the WebRTC connection
    loop = asyncio.new_event_loop()
    
    # Start WebRTC thread with the loop
    webrtc_thread = threading.Thread(target=run_asyncio_loop, args=(conn, loop))
    webrtc_thread.start()

    # Wait a bit for WebRTC connection to establish
    print("[CLIENT] Waiting for WebRTC connection to establish...")
    time.sleep(3)

    # Process frames and send data
    try:
        frame_count = 0
        data_only_count = 0
        last_data_only_time = 0
        
        while True:
            current_time = time.time()
            
            # Get the latest telemetry data
            telemetry_data = get_telemetry_data()
            
            # Always send robot data, with or without frames
            if not frame_queue.empty():
                # Send frame + robot data
                img = frame_queue.get()
                frame_count += 1

                # Encode frame as base64 JSON
                _, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                frame_b64 = base64.b64encode(buffer).decode('utf-8')

                # Process sportmode data to exclude foot data (which only returns 0)
                sportmode_data = telemetry_data['sportmode']
                if sportmode_data:
                    # Create a copy without the excluded fields
                    sportmode_data = {k: v for k, v in sportmode_data.items() 
                                     if k not in ['foot_force', 'foot_position_body', 'foot_speed_body']}
                
                payload = {
                    "timestamp": current_time,
                    "type": "frame_with_data",
                    "frame": {
                        "data": frame_b64,
                        "format": "jpg",
                        "count": frame_count
                    },
                    "robot_data": {
                        "sportmode": sportmode_data,
                        "multiplestate": telemetry_data['multiplestate'],
                        "lidar_state": telemetry_data['lidar_state'],
                        "point_cloud": telemetry_data['point_cloud'],
                        "uwb_state": telemetry_data['uwb_state'],
                        "service_state": telemetry_data['service_state'],
                        "light": telemetry_data['light'],
                        "last_updated": telemetry_data['last_updated'].copy()
                    },
                    "meta": {
                        "camera": "main",
                        "status": "streaming",
                        "frame_count": frame_count,
                        "data_freshness": {
                            key: current_time - timestamp if timestamp else None 
                            for key, timestamp in telemetry_data['last_updated'].items()
                        }
                    }
                }

                # Send the message via socket
                send_message(payload, "frame_with_data")
                print(f"[CLIENT] Frame {frame_count} + robot data sent.")
                
            elif current_time - last_data_only_time >= 0.1:  # Send data-only updates every 100ms
                # Send robot data only
                data_only_count += 1
                last_data_only_time = current_time
                
                # Process sportmode data to exclude foot data
                sportmode_data = telemetry_data['sportmode']
                if sportmode_data:
                    # Create a copy without the excluded fields
                    sportmode_data = {k: v for k, v in sportmode_data.items() 
                                     if k not in ['foot_force', 'foot_position_body', 'foot_speed_body']}
                
                payload = {
                    "timestamp": current_time,
                    "type": "data_only",
                    "robot_data": {
                        "sportmode": sportmode_data,
                        "multiplestate": telemetry_data['multiplestate'],
                        "lidar_state": telemetry_data['lidar_state'],
                        "point_cloud": telemetry_data['point_cloud'],
                        "uwb_state": telemetry_data['uwb_state'],
                        "service_state": telemetry_data['service_state'],
                        "light": telemetry_data['light'],
                        "last_updated": telemetry_data['last_updated'].copy()
                    },
                    "meta": {
                        "status": "data_streaming",
                        "data_count": data_only_count,
                        "data_freshness": {
                            key: current_time - timestamp if timestamp else None 
                            for key, timestamp in telemetry_data['last_updated'].items()
                        }
                    }
                }

                # Send the message via socket
                send_message(payload, "data_only")
                print(f"[CLIENT] Robot data {data_only_count} sent (no frame).")
                
                time.sleep(0.1)  # Send data-only updates every 100ms

    except Exception as e:
        print(f"[CLIENT ERROR] {e}")
    finally:
        print("[CLIENT] Closing connection")
        # Stop the asyncio event loop
        loop.call_soon_threadsafe(loop.stop)

# Main entry point for standalone testing
async def main():
    conn = Go2WebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.1.138")
    await conn.connect()
    
    # Important: Wait for data channel to be ready before proceeding
    print("[STANDALONE] WebRTC connection established, waiting for data channel...")
    await asyncio.sleep(5)  # Give the data channel time to initialize
    
    print("[STANDALONE] Starting frame sending...")
    send_frames(conn)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[CLIENT] Interrupted.")
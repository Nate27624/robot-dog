import asyncio
import base64
import logging
import threading
import time
from queue import Empty, Full, Queue

import cv2
from aiortc import MediaStreamTrack
from go2_webrtc_driver.webrtc_driver import Go2WebRTCConnection, WebRTCConnectionMethod

from logfunc import initialize_log_file
from socketfunc import SERVER_HOST, SERVER_PORT, send_message, start_socket_connection
from telemetryfunc import get_telemetry_data, setup_telemetry


frame_queue = Queue(maxsize=5)
EXCLUDED_SPORTMODE_FIELDS = {"foot_force", "foot_position_body", "foot_speed_body"}


def _filter_sportmode_data(sportmode_data):
    if not sportmode_data:
        return sportmode_data
    return {k: v for k, v in sportmode_data.items() if k not in EXCLUDED_SPORTMODE_FIELDS}


def _build_robot_data_payload(telemetry_data):
    return {
        "sportmode": _filter_sportmode_data(telemetry_data["sportmode"]),
        "multiplestate": telemetry_data["multiplestate"],
        "lidar_state": telemetry_data["lidar_state"],
        "point_cloud": telemetry_data["point_cloud"],
        "uwb_state": telemetry_data["uwb_state"],
        "service_state": telemetry_data["service_state"],
        "light": telemetry_data["light"],
        "last_updated": telemetry_data["last_updated"].copy(),
    }


async def recv_camera_stream(track: MediaStreamTrack):
    """Callback function to receive camera frames."""
    while True:
        frame = await track.recv()
        img = frame.to_ndarray(format="bgr24")

        try:
            frame_queue.put_nowait(img)
        except Full:
            try:
                frame_queue.get_nowait()
            except Empty:
                pass
            try:
                frame_queue.put_nowait(img)
            except Full:
                pass


def run_asyncio_loop(conn, loop):
    """Run the asyncio event loop for WebRTC connection."""
    asyncio.set_event_loop(loop)

    async def setup():
        try:
            logging.info("Setting up video channel...")
            conn.video.switchVideoChannel(True)
            conn.video.add_track_callback(recv_camera_stream)
            logging.info("WebRTC video setup complete.")
            await setup_telemetry(conn)
        except Exception as e:
            logging.error(f"[WebRTC ERROR] {e}")

    loop.run_until_complete(setup())
    loop.run_forever()


def send_frames(conn):
    """Process camera frames and telemetry data and send to server via socket."""
    initialize_log_file(SERVER_HOST, SERVER_PORT)
    start_socket_connection()

    loop = asyncio.new_event_loop()
    webrtc_thread = threading.Thread(target=run_asyncio_loop, args=(conn, loop))
    webrtc_thread.start()

    print("[CLIENT] Waiting for WebRTC connection to establish...")
    time.sleep(3)

    try:
        frame_count = 0
        data_only_count = 0
        last_data_only_time = 0

        while True:
            current_time = time.time()
            telemetry_data = get_telemetry_data()
            robot_data = _build_robot_data_payload(telemetry_data)
            did_send = False

            if not frame_queue.empty():
                img = frame_queue.get()
                frame_count += 1

                _, buffer = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                frame_b64 = base64.b64encode(buffer).decode("ascii")

                payload = {
                    "timestamp": current_time,
                    "type": "frame_with_data",
                    "frame": {
                        "data": frame_b64,
                        "format": "jpg",
                        "count": frame_count,
                    },
                    "robot_data": robot_data,
                    "meta": {
                        "camera": "main",
                        "status": "streaming",
                        "frame_count": frame_count,
                        "data_freshness": {
                            key: current_time - timestamp if timestamp else None
                            for key, timestamp in telemetry_data["last_updated"].items()
                        },
                    },
                }

                send_message(payload, "frame_with_data")
                print(f"[CLIENT] Frame {frame_count} + robot data sent.")
                did_send = True

            elif current_time - last_data_only_time >= 0.1:
                data_only_count += 1
                last_data_only_time = current_time

                payload = {
                    "timestamp": current_time,
                    "type": "data_only",
                    "robot_data": robot_data,
                    "meta": {
                        "status": "data_streaming",
                        "data_count": data_only_count,
                        "data_freshness": {
                            key: current_time - timestamp if timestamp else None
                            for key, timestamp in telemetry_data["last_updated"].items()
                        },
                    },
                }

                send_message(payload, "data_only")
                print(f"[CLIENT] Robot data {data_only_count} sent (no frame).")
                did_send = True

            if not did_send:
                time.sleep(0.01)

    except Exception as e:
        print(f"[CLIENT ERROR] {e}")
    finally:
        print("[CLIENT] Closing connection")
        loop.call_soon_threadsafe(loop.stop)


async def main():
    conn = Go2WebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.1.138")
    await conn.connect()

    print("[STANDALONE] WebRTC connection established, waiting for data channel...")
    await asyncio.sleep(5)

    print("[STANDALONE] Starting frame sending...")
    send_frames(conn)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[CLIENT] Interrupted.")

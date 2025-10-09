import asyncio
import logging
import sys
import threading

# Enable logging for debugging - must be set before any other imports
logging.basicConfig(level=logging.CRITICAL, format='%(asctime)s - %(levelname)s - %(message)s')

from go2_webrtc_driver.webrtc_driver import Go2WebRTCConnection, WebRTCConnectionMethod
from sportfunc import switch_normal
from camerafunc import send_frames
from socketfunc import start_socket_connection, stop_socket_connection
from commandfunc import start_command_processor, stop_command_processor

async def main():
    try:
        # Choose a connection method (uncomment the correct one)
        # conn = Go2WebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.68.60")
        conn = Go2WebRTCConnection(WebRTCConnectionMethod.LocalSTA, serialNumber="B42D1000P5GE828H")
        # conn = Go2WebRTCConnection(WebRTCConnectionMethod.Remote, serialNumber="B42D2000XXXXXXXX", username="email@gmail.com", password="pass")
        # conn = Go2WebRTCConnection(WebRTCConnectionMethod.LocalAP)

        # Connect to the WebRTC service
        await conn.connect()

        # Switch to normal mode if needed
        await switch_normal(conn)

        # Start the command processor thread
        start_command_processor(conn)

        # Start the socket connection
        logging.info("About to start socket connection...")
        start_socket_connection()
        logging.info("Socket connection start function called")

        # Create and start a thread for sending frames and telemetry
        frame_thread = threading.Thread(target=send_frames, args=(conn,), daemon=True)
        frame_thread.start()
        
        
        # Keep the main thread alive
        while True:
            await asyncio.sleep(1)
        
    except ValueError as e:
        # Log any value errors that occur during the process.
        logging.error(f"An error occurred: {e}")
    except Exception as e:
        # Log any other exceptions
        logging.error(f"Unexpected error: {e}")
    finally:
        # Clean up resources
        stop_command_processor()
        stop_socket_connection()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Handle Ctrl+C to exit gracefully.
        print("\nProgram interrupted by user")
        stop_socket_connection()
        sys.exit(0)
import threading
import time
import cv2
from flask import Flask, request, jsonify
from processing.llm.llm_process_question import generate
from processing.socket_server import start_data_reception, get_latest_robot_data_threadsafe
from processing.robot_commands import execute_robot_functions
from robot_data_parser import parser
from robot_ui import RobotDataUI
from pyngrok import ngrok, conf


# === Config ===
HOST = '0.0.0.0'
FLASK_PORT = 5022
SOCKET_PORT = 5021
BUFFER_SIZE = 4096

def ngrok_setup():
    # === ngrok Setup ===
    # Optional: point to your custom config file path
    config = conf.PyngrokConfig(config_path="D:/ixlab/RobotDog/Server/ngrok.yml", ngrok_path="D:/ixLab/RobotDog/Server/ngrok.exe")

    # Kill any existing ngrok processes (prevent session error)
    ngrok.kill()

    # Start the HTTP tunnel
    http_tunnel = ngrok.connect(5022, proto="http", pyngrok_config=config, name="flask_api")
    print(f"HTTP tunnel URL: {http_tunnel.public_url}")

    # Start the TCP tunnel
    tcp_tunnel = ngrok.connect(5021, proto="tcp", pyngrok_config=config, name="socket_server")
    print(f"TCP tunnel URL: {tcp_tunnel.public_url}")

# === Flask App Setup ===
app = Flask(__name__)

@app.route('/test_connection', methods=['GET'])
def test_connection():
    return jsonify({"status": "ok", "message": "Connection to backend successful."}), 200

@app.route('/ask_question', methods=['POST'])
def ask_question():
    try:
        data = request.get_json()
        user_question = data.get('user_question')
        if not user_question:
            return jsonify({"error": "Missing user_question"}), 400

        print(f"[API] Question received: {user_question}")
        result = generate(user_question)
        text, funcs = result

        print(funcs)

        # Execute robot functions if any were returned
        if funcs:
            print(f"[API] Executing {len(funcs)} robot functions")
            robot_results = execute_robot_functions(funcs)
            
            # Log the results but don't return them to the client
            for result in robot_results:
                if "error" in result:
                    print(f"[API ERROR] Function {result['function']}: {result['error']}")
                else:
                    print(f"[API SUCCESS] Function {result['function']} -> Command {result['command']}: {result['result']['status']}")

        # Only return the text response, not the functions
        return jsonify({"response": text})
    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        return jsonify({"error": str(e)}), 500


def start_flask_api():
    app.run(host="0.0.0.0", port=FLASK_PORT, threaded=True)

def main():
    ngrok_setup()

    # Start socket data reception thread
    receiver_thread = threading.Thread(target=start_data_reception, daemon=True)
    receiver_thread.start()
    print("[MAIN] Started data reception thread")

    # Start Flask API in a separate thread
    flask_thread = threading.Thread(target=start_flask_api, daemon=True)
    flask_thread.start()
    print("[MAIN] Started Flask API thread")

    # Give threads time to start
    time.sleep(2)

    # Launch UI
    ui = RobotDataUI(parser)
    print("[MAIN] Starting OpenCV UI - Press 'q' to quit")

    try:
        while True:
            # Get latest robot data and update parser
            latest_data = get_latest_robot_data_threadsafe()
            if latest_data:
                parser.latest_data = latest_data
                # Increment frame counter for UI
                parser._frame_count = getattr(parser, '_frame_count', 0) + 1
                parser._message_count = getattr(parser, '_message_count', 0) + 1
            
            # Show UI
            key = ui.show_side_by_side()
            if key == ord('q'):
                print("[MAIN] Quit key pressed. Exiting...")
                break
                
            time.sleep(0.03)  # ~30 FPS
            
    except KeyboardInterrupt:
        print("[MAIN] Interrupted by user")
    finally:
        cv2.destroyAllWindows()
        print("[MAIN] Clean exit complete")
        

if __name__ == "__main__":
    main()
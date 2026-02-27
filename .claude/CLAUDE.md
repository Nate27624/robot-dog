# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Read [REPO.md](./REPO.md) first** for a quick codebase map: directory structure, component inventory, and key patterns.

## Commands

```bash
# Install Server dependencies
pip install flask google-genai pyngrok opencv-python

# Install Frontend Controller dependencies
pip install go2_webrtc_driver

# Run the Server (starts Flask API + socket server + OpenCV UI)
cd Server && python app.py

# Run the Frontend Controller (connects to robot via WebRTC)
cd Frontend_Controller/comet && python app.py
```

## Repository Scope

This is a **voice-controlled robot dog** system ("Comet") built on a Unitree Go 2 quadruped. Three independently deployed components communicate over HTTP and TCP sockets:

- **Server** (Python/Flask) — LLM processing via Google Gemini, socket server for robot data, OpenCV monitoring UI.
- **Frontend Controller** (Python) — WebRTC connection to the physical robot, executes sport commands, streams video/telemetry to the Server.
- **Unity App** (C#/Android) — Mobile interface with speech-to-text (Meta Wit.AI) and text-to-speech, communicates with Server via HTTP/ngrok.

**Key dependencies:**
- `google-genai` — Gemini 2.5 Flash Lite for natural language understanding + function calling
- `Flask` — REST API (port 5022)
- `pyngrok` — Exposes local ports over public URLs
- `go2_webrtc_driver` — WebRTC driver for Unitree Go 2
- `opencv-python` — Real-time video frame display and monitoring UI

## Architecture

**Three-tier architecture:**
```
Unity App (Android)          # Speech input via Wit.AI
    | HTTP (ngrok)
Server (Flask + Gemini)      # LLM processing + function call extraction
    | TCP Socket (port 5021)
Frontend Controller          # WebRTC commands to robot hardware
    | WebRTC
Unitree Go 2 Robot Dog       # Physical robot
```

### Key Components

| Component | File | Role |
| --- | --- | --- |
| Server Entry | `Server/app.py` | Flask API + socket server + OpenCV UI orchestration |
| LLM Engine | `Server/processing/llm/llm_process_question.py` | Gemini integration — 22 function declarations, system prompt, response parsing |
| Command Mapper | `Server/processing/robot_commands.py` | Maps LLM function names to robot API commands with parameter conversion |
| Socket Server | `Server/processing/socket_server.py` | TCP server (port 5021) — receives robot data, sends JSON commands |
| Data Parser | `Server/robot_data_parser.py` | Decodes incoming robot telemetry and video frames |
| Monitoring UI | `Server/robot_ui.py` | OpenCV-based real-time display of robot video and telemetry |
| Controller Entry | `Frontend_Controller/comet/app.py` | WebRTC connection to robot, thread orchestration |
| Sport Commands | `Frontend_Controller/comet/sportfunc.py` | 50+ robot commands (gaits, flips, dances, poses) |
| Socket Client | `Frontend_Controller/comet/socketfunc.py` | TCP client connecting to Server's socket |
| Command Processor | `Frontend_Controller/comet/commandfunc.py` | FIFO command queue execution |
| Camera Stream | `Frontend_Controller/comet/camerafunc.py` | Video frame capture and streaming |
| LIDAR | `Frontend_Controller/comet/lidarfunc.py` | LIDAR sensor data collection |
| Telemetry | `Frontend_Controller/comet/telemetryfunc.py` | Robot state telemetry |

### Data Flow

1. User speaks into Unity Android app — Wit.AI converts speech to text
2. Text sent via HTTP (ngrok) to Flask API `/ask_question` endpoint
3. Gemini LLM processes question, returns text response + function calls
4. `robot_commands.py` maps function calls to robot API commands (parameter conversion: degrees→radians, etc.)
5. Commands sent as JSON over TCP socket to Frontend Controller
6. Controller executes commands via WebRTC on the physical robot
7. Robot telemetry + video frames streamed back to Server for monitoring

### Networking

| Service | Port | Protocol |
| --- | --- | --- |
| Flask API | 5022 | HTTP |
| Socket Server | 5021 | TCP |
| ngrok | — | Tunnels both ports for remote access |

Robot connection: WebRTC via serial number `B42D1000P5GE828H` (LocalSTA mode).

---

## Project Principles

### Code Organization

- **Three independent processes:** Server, Controller, and Unity app run separately and communicate over network.
- **LLM function calling:** Gemini declares robot capabilities as typed function schemas. The LLM decides which functions to call based on natural language input.
- **Command queue:** Robot commands execute in FIFO order. `clear_queue` stops current command and empties the queue.
- **Parameter mapping:** `robot_commands.py` handles all conversion between LLM function signatures and robot API formats (e.g., `rotation_amount` degrees → `euler` radians).

### Safety

- **Never** commit API keys. `llm_process_question.py` contains the Gemini API key and `ngrok.yml` contains the ngrok auth token — both must be treated as secrets.
- Robot has a `damp` command (kill switch) and `stop_move` (halt movement). Always ensure these remain functional.
- `clear_queue` immediately stops execution — use this as an emergency stop.
- Acrobatic commands (flips, handstand, walkupright) require adequate physical space around the robot.
- The robot auto-calls `balance_stand()` before most commands for safe positioning.

### Performance

- Server runs three concurrent threads: Flask API, socket data reception, and OpenCV UI at ~30 FPS.
- LLM uses `thinking_budget=0` for fastest response time (no chain-of-thought).
- Socket communication uses newline-delimited JSON for simple parsing.

---

## Code Style

### Python (Server + Controller)

- Python 3.x
- `snake_case` for functions and variables
- Threading for concurrency (`threading.Thread` with `daemon=True`)
- `asyncio` in Frontend Controller for WebRTC communication
- JSON for all inter-process communication
- Print-based logging with `[TAG]` prefixes (e.g., `[API]`, `[ROBOT]`, `[MAIN]`)

### C# (Unity App)

- PascalCase for classes and methods
- Unity MonoBehaviour pattern
- Wit.AI SDK for speech processing
- TextMesh Pro for UI text rendering

---

## Before Completing Work

1. **Verify the Server starts** without errors:
   ```bash
   cd Server && python app.py
   ```

2. **Test the API endpoint** responds correctly:
   ```bash
   curl http://localhost:5022/test_connection
   ```

3. **Check API keys are not committed** — `llm_process_question.py` and `ngrok.yml` must not contain real credentials in committed code.

4. **Verify command mappings** — if adding new LLM functions, ensure both `llm_process_question.py` (function declaration) and `robot_commands.py` (mapping + parameter conversion) are updated together.

5. **Test socket communication** — if modifying socket protocol, verify both `Server/processing/socket_server.py` and `Frontend_Controller/comet/socketfunc.py` are compatible.

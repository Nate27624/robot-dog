# REPO.md - Codebase Map

Quick reference for navigating the Comet robot dog codebase.

---

## Root Directory

```
missoula-v1/
├── .claude/                        # Claude Code configuration
├── .context/                       # Workspace context files (gitignored)
├── README.md                       # Project overview
├── name.ipynb                      # Robot naming algorithm notebook
├── rankings_video.mp4              # Demo video
├── Server/                         # AI processing backend
├── Frontend_Controller/            # Robot hardware controller
└── Unity/                          # Android mobile app
```

---

## Server — `Server/`

Flask API + Gemini LLM + socket server + monitoring UI.

### Entry Point & Config

```
app.py                              # Main entry — Flask API (5022), socket server (5021), OpenCV UI
                                    # Threads: flask_thread, receiver_thread, UI loop (~30 FPS)
                                    # ngrok: tunnels both HTTP and TCP ports
ngrok.yml                           # ngrok tunnel configuration (contains auth token)
ngrok.exe                           # ngrok binary (Windows)
```

### Processing Pipeline

```
processing/
├── llm/
│   └── llm_process_question.py     # Gemini 2.5 Flash Lite integration
│                                   # 22 function declarations (kill, move, rotate, pose, flips, dances...)
│                                   # System prompt: Comet personality (docile, lively, humorous)
│                                   # API: generate(question) → (text, function_calls)
│
├── robot_commands.py               # LLM function → robot API command mapper
│                                   # Parameter conversion: degrees→radians, named→array
│                                   # API: execute_robot_functions(functions) → results[]
│
├── socket_server.py                # TCP socket server (port 5021)
│                                   # Receives pickled robot data (video + telemetry)
│                                   # Sends JSON commands to connected controller
│
└── question_processor.py           # Question processing utilities
```

### Monitoring & Parsing

```
robot_data_parser.py                # Decodes incoming robot telemetry and base64 JPG video frames
robot_ui.py                         # OpenCV-based side-by-side display (video + telemetry dashboard)
```

### API Documentation

```
Client_API.md                       # Full robot command API — message format, available commands,
                                    # parameters, response format, queue behavior, safety notes
```

### Test/Debug Scripts

```
delete/
├── simple_test_client.py           # Basic socket test client
└── socket_stream.py                # Socket streaming test
```

---

## Frontend Controller — `Frontend_Controller/comet/`

WebRTC connection to Unitree Go 2, command execution, sensor streaming.

```
app.py                              # Entry point — WebRTC connection (Go2WebRTCConnection)
                                    # Connection: LocalSTA via serial number B42D1000P5GE828H
                                    # Starts: command processor, socket connection, frame streaming

sportfunc.py                        # Robot sport mode commands (~50+ commands)
                                    # Basic: stand_up, stand_down, sit, balance_stand, recovery_stand
                                    # Gestures: hello, stretch, content, heart, scrape
                                    # Acrobatics: frontflip, backflip, leftflip, rightflip, handstand
                                    # Gaits: staticwalk, trotrun, economicgate, classicwalk
                                    # Movement: move (x,y,z), euler (roll,pitch,yaw)

socketfunc.py                       # TCP socket client — connects to Server's socket server
                                    # Bi-directional: sends telemetry/frames, receives commands

commandfunc.py                      # FIFO command queue processor
                                    # Executes robot commands sequentially
                                    # Supports clear_queue for emergency stop

camerafunc.py                       # Camera frame capture via WebRTC pub_sub
                                    # Encodes frames as base64 JPG for socket transmission

lidarfunc.py                        # LIDAR sensor data collection and forwarding

telemetryfunc.py                    # Robot state telemetry (position, battery, joint states)

logfunc.py                          # Logging utilities
```

---

## Unity App — `Unity/`

Android mobile app for voice interaction with Comet.

### Scripts

```
Assets/Scripts/
├── NewSpeechCapture.cs             # Meta Wit.AI speech-to-text — continuous voice capture
├── SpeechOutput.cs                 # Text-to-speech — speaks server responses aloud
├── NgrokConnection.cs              # Manages ngrok HTTP connection to Flask API
├── SimpleEyeMovement.cs            # Robot eye animation on the app UI
└── ...                             # Other UI and interaction scripts
```

### Assets

```
Assets/
├── Audio/                          # Sound effects (button clicks, async completion)
├── Materials/                      # 3D materials and textures (eye iris, body colors)
├── Scenes/                         # Unity scenes
├── Settings/                       # Unity project settings
└── TextMesh Pro/                   # UI text rendering assets
```

---

## Quick Reference

| Need to... | Look in... |
| --- | --- |
| Add a new robot command | `Server/processing/llm/llm_process_question.py` (function declaration) + `Server/processing/robot_commands.py` (mapping) + `Frontend_Controller/comet/sportfunc.py` (implementation) |
| Change Comet's personality | `Server/processing/llm/llm_process_question.py` (system instruction) |
| Modify LLM model or config | `Server/processing/llm/llm_process_question.py` (model name, temperature, thinking_budget) |
| Fix socket communication | `Server/processing/socket_server.py` (server) + `Frontend_Controller/comet/socketfunc.py` (client) |
| Add Flask API endpoint | `Server/app.py` |
| Change robot connection | `Frontend_Controller/comet/app.py` (serial number, connection method) |
| Modify video streaming | `Frontend_Controller/comet/camerafunc.py` (capture) + `Server/robot_data_parser.py` (decode) |
| Update monitoring UI | `Server/robot_ui.py` |
| Change speech processing | `Unity/Assets/Scripts/NewSpeechCapture.cs` (STT) + `Unity/Assets/Scripts/SpeechOutput.cs` (TTS) |
| Modify ngrok tunnels | `Server/app.py` (ngrok_setup function) + `Server/ngrok.yml` (config) |
| View robot command API | `Server/Client_API.md` |

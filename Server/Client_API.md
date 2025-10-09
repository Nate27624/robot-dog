# Robot Dog Command API

This document describes how to send commands to the robot dog via the socket connection.

## Connection Details
- **Host**: 0.tcp.ngrok.io
- **Port**: 10466
- **Protocol**: TCP Socket with JSON messages

## Message Format

All messages should be sent as JSON objects followed by a newline character (`\n`).

### Command Execution
```json
{
  "type": "execute_command",
  "data": {
    "command": "command_name",
    "parameters": {
      // Optional parameters specific to the command
    }
  }
}
```

### Clear Command Queue
```json
{
  "type": "clear_queue"
}
```

### Get Queue Status
```json
{
  "type": "queue_status"
}
```

## Available Commands

### Basic Movement Commands
- `damp` - Kills robot, turns off power but keeps robot on
- `balance_stand` - Unlocks the joints
- `stop_move` - Stop current movement
- `stand_up` - Stands the robot dog up
- `stand_down` - Sets the robot dog down
- `recovery_stand` - Stands robot dog up as fast as possible

### Position Commands (with parameters)
- `euler` - Rotates dog body
  ```json
  {
    "command": "euler",
    "parameters": {
      "angles": [x, y, z]  // Rotation angles in radians
    }
  }
  ```
- `move` - Moves dog body
  ```json
  {
    "command": "move",
    "parameters": {
      "movement": [x, y, z]  // Movement vector
    }
  }
  ```

### Sitting Commands
- `sit` - Sits the robot dog
- `rise_sit` - Stands the dog up from sitting position

### Gesture Commands
- `hello` - Performs a hello movement
- `stretch` - Performs a stretch movement
- `content` - Happy little dance
- `dance1` - Short dance
- `dance2` - Long dance
- `heart` - Performs a heart movement
- `scrape` - Goes on its knees

### Acrobatic Commands
- `frontflip` - Performs a front flip
- `leftflip` - Performs a left flip
- `rightflip` - Performs a right flip
- `backflip` - Performs a back flip
- `front_jump` - Front jump
- `front_pounce` - Front pounce

### Special Movement Commands (with time parameters)
- `handstand` - Performs a handstand for specified time
  ```json
  {
    "command": "handstand",
    "parameters": {
      "length": 5  // Duration in seconds
    }
  }
  ```
- `walkupright` - Walks on feet like a human for specified time
  ```json
  {
    "command": "walkupright",
    "parameters": {
      "time": 10  // Duration in seconds
    }
  }
  ```
- `crossstep` - Performs cross step movement for specified time
  ```json
  {
    "command": "crossstep",
    "parameters": {
      "time": 5  // Duration in seconds
    }
  }
  ```

### Gait Commands
- `staticwalk` - Switches dog to normal walking
- `trotrun` - Switches the dog to run mode
- `economicgate` - Switches to normal walking
- `classicwalk` - Returns to regular walking mode

## Response Format

All commands return a JSON response:

### Success Response
```json
{
  "status": "success",
  "message": "Command 'hello' added to queue",
  "queue_size": 1
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Unknown command: invalid_command"
}
```

### Queue Status Response
```json
{
  "status": "success",
  "queue_size": 2,
  "processor_running": true,
  "current_command_running": true,
  "available_commands": ["damp", "balance_stand", "stop_move", ...]
}
```

## Example Usage

### Python Client Example
```python
import socket
import json

def send_command(host, port, command_data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        
        # Send command
        message = json.dumps(command_data) + '\n'
        sock.sendall(message.encode('utf-8'))
        
        # Receive response
        response = sock.recv(1024).decode('utf-8')
        return json.loads(response.strip())

# Make the dog say hello
response = send_command("0.tcp.ngrok.io", 10466, {
    "type": "execute_command",
    "data": {
        "command": "hello"
    }
})
print(response)

# Make the dog do a handstand for 5 seconds
response = send_command("0.tcp.ngrok.io", 10466, {
    "type": "execute_command",
    "data": {
        "command": "handstand",
        "parameters": {
            "length": 5
        }
    }
})
print(response)

# Clear all commands
response = send_command("0.tcp.ngrok.io", 10466, {
    "type": "clear_queue"
})
print(response)
```

## Command Queue Behavior

1. **Queue Processing**: Commands are executed in FIFO (First In, First Out) order
2. **Current Command Interruption**: When `clear_queue` is called, the currently executing command is stopped and the robot returns to balance_stand position
3. **Error Handling**: If a command fails, the queue continues processing the next command
4. **Automatic Recovery**: After certain commands (like handstand, walkupright, crossstep), the robot automatically returns to classic walk mode

## Safety Notes

- The robot will automatically call `balance_stand()` before executing most commands to ensure safe positioning
- Commands like flips and acrobatic moves may take several seconds to complete
- Always ensure the robot has adequate space before sending movement commands
- Use `clear_queue` to immediately stop all commands if needed

	

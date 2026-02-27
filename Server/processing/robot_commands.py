import math
from processing.socket_server import send_json_command_to_client

def map_function_to_command(func_name, parameters=None):
    """Map LLM function calls to robot API commands"""
    if parameters is None:
        parameters = {}
    
    # Function name to robot command mapping
    function_mapping = {
        "kill": "damp",
        "stop_all": "stop_move",
        "lay_down": "stand_down",
        "pose": "euler",
        "move": "move", 
        "rotate": "move",
        "sit_down": "sit",
        "hello": "hello",
        "stretch": "stretch",
        "content": "content",
        "dance_short": "dance1",
        "dance_long": "dance2",
        "attack": "scrape",  # Closest equivalent
        "love": "heart",
        "switch_walk": "staticwalk",
        "switch_run": "trotrun",
        "front_flip": "frontflip",
        "left_flip": "leftflip",
        "back_flip": "backflip",
        "forward_jump": "front_jump",
        "hand_stand": "handstand",
        "walk_upright": "walkupright",
        "cross_step": "crossstep"
    }
    
    robot_command = function_mapping.get(func_name)
    if not robot_command:
        return None
    
    # Handle special parameter mappings
    robot_params = {}
    
    if func_name == "pose":
        # Map roll, pitch, yaw to angles array
        robot_params["angles"] = [
            parameters.get("roll", 0),
            parameters.get("pitch", 0), 
            parameters.get("yaw", 0)
        ]
    elif func_name == "rotate":
        # Convert target degrees to an in-place yaw movement.
        rotation_rad = math.radians(parameters.get("rotation_amount", 0))
        if rotation_rad == 0:
            yaw_velocity = 0
            duration = 0
        else:
            duration = max(min(abs(rotation_rad) / 0.8, 6.0), 0.2)
            yaw_velocity = max(min(rotation_rad / duration, 1.2), -1.2)
        robot_params["movement"] = [0, 0, yaw_velocity]
        robot_params["duration"] = duration
        robot_params["stop_after"] = True
        robot_command = "move"
    elif func_name == "move":
        # Map x, y to movement array (add z=0)
        robot_params["movement"] = [
            parameters.get("x", 0),
            parameters.get("y", 0),
            0  # z component
        ]
    elif func_name in ["hand_stand", "walk_upright", "cross_step"]:
        # Map time parameter to length for handstand, time for others
        if func_name == "hand_stand":
            robot_params["length"] = parameters.get("time", 5)
        else:
            robot_params["time"] = parameters.get("time", 5)
    elif func_name == "lay_down":
        # Add time parameter to robot_params for stand_down
        robot_params["time"] = parameters.get("time", 5)

    elif func_name == "sit_down":
        # Add time parameter to robot_params for sit_down
        robot_params["time"] = parameters.get("time", 5)

    
    return {
        "type": "execute_command",
        "data": {
            "command": robot_command,
            "parameters": robot_params if robot_params else {}
        }
    }

def send_command_to_robot(command_data):
    """Actually send command to robot over active socket connection."""
    print(f"[ROBOT] Sending command: {command_data}")
    return send_json_command_to_client(command_data)

def execute_robot_functions(functions):
    results = []

    if not functions:
        return results

    for func_call in functions:
        func_name = func_call.name
        parameters = {}

        if hasattr(func_call, 'args') and func_call.args:
            parameters.update(func_call.args)

        print(f"[ROBOT] Executing function: {func_name} with params: {parameters}")

        command_data = map_function_to_command(func_name, parameters)

        if command_data:
            print(f"[ROBOT] Sending command: {command_data}")
            response = send_command_to_robot(command_data)

            if response.get("status") == "success":
                print(f"[ROBOT SUCCESS] {response.get('message')}")
            else:
                print(f"[ROBOT ERROR] {response.get('message')}")

            results.append({
                "function": func_name,
                "command": command_data["data"]["command"],
                "result": response
            })
        else:
            print(f"[ROBOT ERROR] Unknown function: {func_name}")
            results.append({
                "function": func_name,
                "error": f"Unknown function: {func_name}"
            })

    return results

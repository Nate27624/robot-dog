import json
import time
import logging

# Logging configuration
ENABLE_FILE_LOGGING = True  # Set to False to disable file logging
LOG_FILE_PATH = "robot_data_log.txt"
MAX_LOG_ENTRIES = 50  # Maximum number of JSON messages to log

log_entry_count = 0

def log_to_file(payload, message_type="unknown"):
    """Log JSON payload to file if logging is enabled"""
    global log_entry_count
    
    if not ENABLE_FILE_LOGGING:
        return
        
    try:
        # Create a copy of payload without the large frame payload for logging
        log_payload = payload.copy()
        
        # Handle frame data if present
        if "frame" in log_payload and "data" in log_payload["frame"]:
            # Replace the large frame data with a placeholder
            frame_size = len(log_payload["frame"]["data"])
            log_payload["frame"]["data"] = f"[IMAGE_DATA_{frame_size}_BYTES]"
        
        # Handle point cloud data if present
        if "robot_data" in log_payload and "point_cloud" in log_payload["robot_data"] and log_payload["robot_data"]["point_cloud"]:
            point_cloud_size = len(str(log_payload["robot_data"]["point_cloud"]))
            log_payload["robot_data"]["point_cloud"] = f"[POINT_CLOUD_DATA_{point_cloud_size}_BYTES]"
        
        log_entry_count += 1
        
        # Create log entry with metadata
        log_entry = {
            "log_entry": log_entry_count,
            "log_timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "message_type": message_type,
            "payload": log_payload
        }
        
        # Write to file (append mode)
        with open(LOG_FILE_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, indent=2) + '\n')
            f.write("-" * 80 + '\n')  # Separator between entries
            
        # Limit file size by truncating if too many entries
        if log_entry_count > MAX_LOG_ENTRIES:
            truncate_log_file()
            
    except Exception as e:
        print(f"[LOG ERROR] Failed to write to log file: {e}")

def truncate_log_file():
    """Keep only the last MAX_LOG_ENTRIES/2 entries to prevent file from growing too large"""
    try:
        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by separator and keep last half
        entries = content.split("-" * 80 + '\n')
        keep_entries = entries[-(MAX_LOG_ENTRIES//2):]
        
        with open(LOG_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(("-" * 80 + '\n').join(keep_entries))
            
        print(f"[LOG] Truncated log file to last {len(keep_entries)} entries")
        
    except Exception as e:
        print(f"[LOG ERROR] Failed to truncate log file: {e}")

def initialize_log_file(server_host, server_port):
    """Initialize the log file with header information"""
    if not ENABLE_FILE_LOGGING:
        return
        
    try:
        header = {
            "log_session_start": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "robot_ip": "192.168.1.138",
            "server": f"{server_host}:{server_port}",
            "log_info": "Robot dog telemetry data log",
            "data_types": [
                "sportmode - Movement, gait, position data", 
                "multiplestate - System settings and switches",
                "lidar_state - LIDAR sensor status",
                "point_cloud - 3D point cloud data from LIDAR",
                "uwb_state - Ultra-wideband positioning",
                "service_state - System service status",
                "light - Current light color and brightness"
            ]
        }
        
        with open(LOG_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + '\n')
            f.write("ROBOT DOG TELEMETRY LOG SESSION\n")
            f.write("=" * 80 + '\n')
            f.write(json.dumps(header, indent=2) + '\n')
            f.write("=" * 80 + '\n\n')
            
        print(f"[LOG] Initialized log file: {LOG_FILE_PATH}")
        
    except Exception as e:
        print(f"[LOG ERROR] Failed to initialize log file: {e}")

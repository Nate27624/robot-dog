import json
import base64
import numpy as np
import cv2
from datetime import datetime
import math
import os
import time

class RobotDataParser:
    def __init__(self):
        self.latest_data = None
        self.frame_count = 0
        self.logging_enabled = False
        self.log_file = None
        self.log_directory = "robot_logs"
        
    def enable_logging(self, enabled=True):
        """Enable or disable logging of robot data to file"""
        self.logging_enabled = enabled
        if enabled:
            # Create logs directory if it doesn't exist
            if not os.path.exists(self.log_directory):
                os.makedirs(self.log_directory)
                
            # Create a timestamped log file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = os.path.join(self.log_directory, f"robot_data_{timestamp}.json")
            print(f"[PARSER] Logging enabled. Saving data to {self.log_file}")
            
            # Initialize the log file with an empty array
            with open(self.log_file, 'w') as f:
                f.write("[\n")  # Start JSON array
                
            return self.log_file
        else:
            if self.log_file:
                # Close the JSON array properly
                with open(self.log_file, 'a') as f:
                    f.write("\n]\n")  # End JSON array
                print(f"[PARSER] Logging disabled. Data saved to {self.log_file}")
                self.log_file = None
            return None
        
    def parse_message(self, message_str):
        """Parse incoming JSON message and store latest data"""
        try:
            self.latest_data = json.loads(message_str)
            return True
        except json.JSONDecodeError as e:
            print(f"[PARSER ERROR] Failed to parse JSON: {e}")
            return False
    
    def get_latest_frame(self):
        """Extract and decode the latest frame as OpenCV image"""
        if not self.latest_data:
            return None
            
        try:
            # We'll use the frame that was already decoded in socket_stream.py
            # This method is now just a pass-through to get the latest frame
            from socket_stream import latest_frame, frame_lock
            
            with frame_lock:
                if latest_frame is not None:
                    return latest_frame.copy()
                    
            return None
        except Exception as e:
            print(f"[PARSER ERROR] Failed to get latest frame: {e}")
            return None
    
    def get_frame_info(self):
        """Get frame metadata"""
        try:
            # Check if we have frame from socket_frame_recv
            from processing.socket_server import latest_frame, frame_lock
            
            with frame_lock:
                has_frame = latest_frame is not None
            
            if has_frame:
                return {
                    'format': 'jpg',
                    'count': getattr(self, '_frame_count', 0),
                    'camera': 'robot_camera',
                    'status': 'active',
                    'frame_count': getattr(self, '_frame_count', 0)
                }
            else:
                return {
                    'format': 'none',
                    'count': 0,
                    'camera': 'robot_camera',
                    'status': 'no signal',
                    'frame_count': 0
                }
        except Exception as e:
            print(f"[PARSER ERROR] Failed to get frame info: {e}")
            return {
                'format': 'error',
                'count': 0,
                'camera': 'error',
                'status': f'error: {str(e)}',
                'frame_count': 0
            }
    
    def get_orientation_degrees(self):
        """Convert quaternion to Euler angles in degrees"""
        if not self.latest_data:
            return None
            
        try:
            # Handle direct robot_data format from socket_frame_recv
            data = self.latest_data
            
            # Try different possible data structures
            if 'sportmode' in data and 'imu_state' in data['sportmode']:
                imu_state = data['sportmode']['imu_state']
            elif 'imu_state' in data:
                imu_state = data['imu_state']
            elif 'robot_data' in data and 'sportmode' in data['robot_data']:
                imu_state = data['robot_data']['sportmode']['imu_state']
            else:
                return None
                
            # Try to get RPY data
            if 'rpy' in imu_state:
                rpy_rad = imu_state['rpy']
                roll_deg = math.degrees(rpy_rad[0])
                pitch_deg = math.degrees(rpy_rad[1])
                yaw_deg = math.degrees(rpy_rad[2])
                
                return {
                    'roll': round(roll_deg, 2),
                    'pitch': round(pitch_deg, 2),
                    'yaw': round(yaw_deg, 2),
                    'quaternion': imu_state.get('quaternion', [0, 0, 0, 1])
                }
            
            return None
        except Exception as e:
            print(f"[PARSER ERROR] Failed to get orientation: {e}")
            return None
    
    def get_position(self):
        """Get robot position in meters"""
        if not self.latest_data:
            return None
            
        try:
            data = self.latest_data
            
            # Try different possible data structures
            if 'sportmode' in data and 'position' in data['sportmode']:
                pos = data['sportmode']['position']
            elif 'position' in data:
                pos = data['position']
            elif 'robot_data' in data and 'sportmode' in data['robot_data']:
                pos = data['robot_data']['sportmode']['position']
            else:
                return None
                
            return {
                'x': round(pos[0], 3),
                'y': round(pos[1], 3),
                'z': round(pos[2], 3)
            }
        except Exception as e:
            print(f"[PARSER ERROR] Failed to get position: {e}")
            return None
    
    def get_velocity(self):
        """Get robot velocity in m/s"""
        if not self.latest_data:
            return None
            
        try:
            data = self.latest_data
            
            # Try different possible data structures
            if 'sportmode' in data and 'velocity' in data['sportmode']:
                vel = data['sportmode']['velocity']
                yaw_speed = data['sportmode'].get('yaw_speed', 0)
            elif 'velocity' in data:
                vel = data['velocity']
                yaw_speed = data.get('yaw_speed', 0)
            elif 'robot_data' in data and 'sportmode' in data['robot_data']:
                vel = data['robot_data']['sportmode']['velocity']
                yaw_speed = data['robot_data']['sportmode'].get('yaw_speed', 0)
            else:
                return None
                
            return {
                'linear_x': round(vel[0], 3),
                'linear_y': round(vel[1], 3),
                'linear_z': round(vel[2], 3),
                'angular_z': round(yaw_speed, 3)
            }
        except Exception as e:
            print(f"[PARSER ERROR] Failed to get velocity: {e}")
            return None
    
    def get_imu_data(self):
        """Get IMU sensor data"""
        if not self.latest_data:
            return None
            
        try:
            # Check if we have the payload wrapper or direct data
            if 'payload' in self.latest_data:
                data = self.latest_data['payload']
            else:
                data = self.latest_data
                
            if 'robot_data' not in data or 'sportmode' not in data['robot_data']:
                return None
                
            imu = data['robot_data']['sportmode']['imu_state']
            return {
                'gyroscope': {
                    'x': round(imu['gyroscope'][0], 4),
                    'y': round(imu['gyroscope'][1], 4),
                    'z': round(imu['gyroscope'][2], 4)
                },
                'accelerometer': {
                    'x': round(imu['accelerometer'][0], 3),
                    'y': round(imu['accelerometer'][1], 3),
                    'z': round(imu['accelerometer'][2], 3)
                },
                'temperature': imu['temperature']
            }
        except Exception as e:
            print(f"[PARSER ERROR] Failed to get IMU data: {e}")
            return None
    
    def get_robot_status(self):
        """Get robot operational status"""
        if not self.latest_data:
            return None
            
        try:
            data = self.latest_data
            
            # Try different possible data structures
            sport = None
            multi = None
            
            if 'sportmode' in data and 'multiplestate' in data:
                sport = data['sportmode']
                multi = data['multiplestate']
            elif 'robot_data' in data:
                if 'sportmode' in data['robot_data']:
                    sport = data['robot_data']['sportmode']
                if 'multiplestate' in data['robot_data']:
                    multi = data['robot_data']['multiplestate']
            
            if not sport:
                return None
                
            return {
                'mode': sport.get('mode', 0),
                'gait_type': sport.get('gait_type', 0),
                'body_height': round(sport.get('body_height', 0), 3),
                'foot_raise_height': sport.get('foot_raise_height', 0),
                'error_code': sport.get('error_code', 0),
                'brightness': multi.get('brightness', 0) if multi else 0,
                'volume': multi.get('volume', 0) if multi else 0,
                'obstacle_avoidance': multi.get('obstaclesAvoidSwitch', False) if multi else False,
                'uwb_enabled': multi.get('uwbSwitch', False) if multi else False
            }
        except Exception as e:
            print(f"[PARSER ERROR] Failed to get robot status: {e}")
            return None
    
    def get_timestamp_info(self):
        """Get timestamp information"""
        if not self.latest_data:
            return None
            
        try:
            data = self.latest_data
            
            # Get timestamp from the message
            timestamp = data.get('timestamp', time.time())
            
            # Convert timestamp to readable format if it's a number
            if isinstance(timestamp, (int, float)) and timestamp > 0:
                readable_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            else:
                readable_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return {
                'log_entry': getattr(self, '_message_count', 0),
                'log_timestamp': readable_time,
                'payload_timestamp': timestamp,
                'message_type': 'robot_telemetry'
            }
        except Exception as e:
            print(f"[PARSER ERROR] Failed to get timestamp info: {e}")
            return None
    
    def get_all_data_summary(self):
        """Get a comprehensive summary of all current data"""
        return {
            'timestamp': self.get_timestamp_info(),
            'frame_info': self.get_frame_info(),
            'orientation': self.get_orientation_degrees(),
            'position': self.get_position(),
            'velocity': self.get_velocity(),
            'imu': self.get_imu_data(),
            'status': self.get_robot_status()
        }

parser = RobotDataParser()
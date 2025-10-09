import cv2
import numpy as np
from robot_data_parser import RobotDataParser

class RobotDataUI:
    def __init__(self, parser: RobotDataParser):
        self.parser = parser
        self.ui_width = 350  # Reduced width to fit better
        self.ui_height = 600
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.4  # Smaller font to fit more content
        self.font_thickness = 1
        self.line_height = 16  # Reduced line height
        self.last_frame_count = 0  # Track frame count to avoid unnecessary updates
        
    def create_data_overlay(self, frame=None):
        """Create a data overlay that can be shown alongside or on top of the video feed"""
        try:
            # Create a blank canvas for the UI
            ui_canvas = np.zeros((self.ui_height, self.ui_width, 3), dtype=np.uint8)
            ui_canvas.fill(40)  # Dark gray background
            
            y_pos = 30
            
            # Title
            cv2.putText(ui_canvas, "ROBOT DOG STATUS", (10, int(y_pos)), 
                       self.font, 0.6, (255, 255, 255), 2)
            y_pos += 40
            
            # Connection status
            connection_status = "CONNECTED" if self.parser.latest_data else "WAITING FOR CLIENT"
            connection_color = (0, 255, 0) if self.parser.latest_data else (255, 165, 0)
            cv2.putText(ui_canvas, f"Status: {connection_status}", (10, int(y_pos)), 
                       self.font, self.font_scale, connection_color, self.font_thickness)
            y_pos += int(self.line_height * 1.5)
            
            # Timestamp info (only show if we have data)
            if self.parser.latest_data:
                timestamp_info = self.parser.get_timestamp_info()
                if timestamp_info:
                    cv2.putText(ui_canvas, f"Log Entry: {timestamp_info['log_entry']}", 
                               (10, int(y_pos)), self.font, self.font_scale, (200, 200, 200), self.font_thickness)
                    y_pos += self.line_height
                    
                    cv2.putText(ui_canvas, f"Time: {timestamp_info['log_timestamp'][:19]}", 
                               (10, int(y_pos)), self.font, self.font_scale, (200, 200, 200), self.font_thickness)
                    y_pos += int(self.line_height * 1.5)
            
            # Frame info - always show camera section, but only update content when there's a new frame
            cv2.putText(ui_canvas, "CAMERA", (10, int(y_pos)), 
                       self.font, 0.5, (100, 255, 100), 2)
            y_pos += 20
            
            frame_info = self.parser.get_frame_info()
            if frame_info:
                current_frame_count = frame_info.get('frame_count', 0)
                
                # Update camera info if we have frames or if frame count changed
                has_frame_data = (self.parser.latest_data is not None and 
                                'frame' in self.parser.latest_data) if self.parser.latest_data else False
                if has_frame_data or current_frame_count != self.last_frame_count:
                    # Store the updated info
                    self.last_camera_status = frame_info['status']
                    self.last_frame_count = current_frame_count
                
                # Always display camera info (either current or last known)
                status = getattr(self, 'last_camera_status', 'waiting for frames')
                count = getattr(self, 'last_frame_count', 0)
                
                cv2.putText(ui_canvas, f"Status: {status}", 
                           (10, int(y_pos)), self.font, self.font_scale, (255, 255, 255), self.font_thickness)
                y_pos += self.line_height
                
                cv2.putText(ui_canvas, f"Count: {count}", 
                           (10, int(y_pos)), self.font, self.font_scale, (255, 255, 255), self.font_thickness)
                y_pos += int(self.line_height * 1.2)
            else:
                # Show default camera info when no frame info is available
                cv2.putText(ui_canvas, "Status: waiting for frames", 
                           (10, int(y_pos)), self.font, self.font_scale, (200, 200, 200), self.font_thickness)
                y_pos += self.line_height
                
                cv2.putText(ui_canvas, "Count: 0", 
                           (10, int(y_pos)), self.font, self.font_scale, (200, 200, 200), self.font_thickness)
                y_pos += int(self.line_height * 1.2)
            
            # Only show detailed data if we have a connection
            if not self.parser.latest_data:
                cv2.putText(ui_canvas, "Waiting for robot connection...", 
                           (10, int(y_pos)), self.font, self.font_scale, (200, 200, 200), self.font_thickness)
                return ui_canvas
            
            # Orientation
            try:
                orientation = self.parser.get_orientation_degrees()
                if orientation:
                    cv2.putText(ui_canvas, "ORIENTATION (degrees)", (10, int(y_pos)), 
                               self.font, 0.55, (100, 100, 255), 2)
                    y_pos += 25
                    
                    cv2.putText(ui_canvas, f"Roll:  {orientation['roll']:>8.2f}°", 
                               (10, int(y_pos)), self.font, self.font_scale, (255, 255, 255), self.font_thickness)
                    y_pos += self.line_height
                    
                    cv2.putText(ui_canvas, f"Pitch: {orientation['pitch']:>8.2f}°", 
                               (10, int(y_pos)), self.font, self.font_scale, (255, 255, 255), self.font_thickness)
                    y_pos += self.line_height
                    
                    cv2.putText(ui_canvas, f"Yaw:   {orientation['yaw']:>8.2f}°", 
                               (10, int(y_pos)), self.font, self.font_scale, (255, 255, 255), self.font_thickness)
                    y_pos += int(self.line_height * 1.5)
                else:
                    cv2.putText(ui_canvas, "ORIENTATION (degrees)", (10, int(y_pos)), 
                               self.font, 0.55, (100, 100, 255), 2)
                    y_pos += 25
                    cv2.putText(ui_canvas, "No orientation data available", 
                               (10, int(y_pos)), self.font, self.font_scale, (200, 200, 200), self.font_thickness)
                    y_pos += int(self.line_height * 1.5)
            except Exception as e:
                cv2.putText(ui_canvas, "ORIENTATION ERROR", (10, int(y_pos)), 
                           self.font, 0.55, (100, 100, 255), 2)
                y_pos += int(self.line_height * 1.5)
            
            # Position
            try:
                position = self.parser.get_position()
                if position:
                    cv2.putText(ui_canvas, "POSITION (meters)", (10, int(y_pos)), 
                               self.font, 0.55, (255, 100, 100), 2)
                    y_pos += 25
                    
                    cv2.putText(ui_canvas, f"X: {position['x']:>8.3f} m", 
                               (10, int(y_pos)), self.font, self.font_scale, (255, 255, 255), self.font_thickness)
                    y_pos += self.line_height
                    
                    cv2.putText(ui_canvas, f"Y: {position['y']:>8.3f} m", 
                               (10, int(y_pos)), self.font, self.font_scale, (255, 255, 255), self.font_thickness)
                    y_pos += self.line_height
                    
                    cv2.putText(ui_canvas, f"Z: {position['z']:>8.3f} m", 
                               (10, int(y_pos)), self.font, self.font_scale, (255, 255, 255), self.font_thickness)
                    y_pos += int(self.line_height * 1.5)
                else:
                    cv2.putText(ui_canvas, "POSITION (meters)", (10, int(y_pos)), 
                               self.font, 0.55, (255, 100, 100), 2)
                    y_pos += 25
                    cv2.putText(ui_canvas, "No position data available", 
                               (10, int(y_pos)), self.font, self.font_scale, (200, 200, 200), self.font_thickness)
                    y_pos += int(self.line_height * 1.5)
            except Exception as e:
                cv2.putText(ui_canvas, "POSITION ERROR", (10, int(y_pos)), 
                           self.font, 0.55, (255, 100, 100), 2)
                y_pos += int(self.line_height * 1.5)
            
            # Velocity
            try:
                velocity = self.parser.get_velocity()
                if velocity:
                    cv2.putText(ui_canvas, "VELOCITY (m/s)", (10, int(y_pos)), 
                               self.font, 0.55, (255, 255, 100), 2)
                    y_pos += 25
                    
                    cv2.putText(ui_canvas, f"Linear X: {velocity['linear_x']:>6.3f}", 
                               (10, int(y_pos)), self.font, self.font_scale, (255, 255, 255), self.font_thickness)
                    y_pos += self.line_height
                    
                    cv2.putText(ui_canvas, f"Linear Y: {velocity['linear_y']:>6.3f}", 
                               (10, int(y_pos)), self.font, self.font_scale, (255, 255, 255), self.font_thickness)
                    y_pos += self.line_height
                    
                    cv2.putText(ui_canvas, f"Angular: {velocity['angular_z']:>7.3f}", 
                               (10, int(y_pos)), self.font, self.font_scale, (255, 255, 255), self.font_thickness)
                    y_pos += int(self.line_height * 1.5)
                else:
                    cv2.putText(ui_canvas, "VELOCITY (m/s)", (10, int(y_pos)), 
                               self.font, 0.55, (255, 255, 100), 2)
                    y_pos += 25
                    cv2.putText(ui_canvas, "No velocity data available", 
                               (10, int(y_pos)), self.font, self.font_scale, (200, 200, 200), self.font_thickness)
                    y_pos += int(self.line_height * 1.5)
            except Exception as e:
                cv2.putText(ui_canvas, "VELOCITY ERROR", (10, int(y_pos)), 
                           self.font, 0.55, (255, 255, 100), 2)
                y_pos += int(self.line_height * 1.5)
            
            # Robot Status
            try:
                status = self.parser.get_robot_status()
                if status:
                    cv2.putText(ui_canvas, "ROBOT STATUS", (10, int(y_pos)), 
                               self.font, 0.55, (255, 150, 255), 2)
                    y_pos += 25
                    
                    cv2.putText(ui_canvas, f"Mode: {status['mode']}", 
                               (10, int(y_pos)), self.font, self.font_scale, (255, 255, 255), self.font_thickness)
                    y_pos += self.line_height
                    
                    cv2.putText(ui_canvas, f"Body Height: {status['body_height']:.3f}m", 
                               (10, int(y_pos)), self.font, self.font_scale, (255, 255, 255), self.font_thickness)
                    y_pos += self.line_height
                    
                    cv2.putText(ui_canvas, f"Volume: {status['volume']}", 
                               (10, int(y_pos)), self.font, self.font_scale, (255, 255, 255), self.font_thickness)
                    y_pos += self.line_height
                    
                    # Status indicators with colors
                    obstacle_color = (0, 255, 0) if status['obstacle_avoidance'] else (0, 0, 255)
                    cv2.putText(ui_canvas, f"Obstacle Avoid: {'ON' if status['obstacle_avoidance'] else 'OFF'}", 
                               (10, int(y_pos)), self.font, self.font_scale, obstacle_color, self.font_thickness)
                    y_pos += self.line_height
                    
                    uwb_color = (0, 255, 0) if status['uwb_enabled'] else (0, 0, 255)
                    cv2.putText(ui_canvas, f"UWB: {'ON' if status['uwb_enabled'] else 'OFF'}", 
                               (10, int(y_pos)), self.font, self.font_scale, uwb_color, self.font_thickness)
                    y_pos += self.line_height
                    
                    # Error code with warning color if not zero
                    error_color = (0, 255, 255) if status['error_code'] != 0 else (255, 255, 255)
                    cv2.putText(ui_canvas, f"Error Code: {status['error_code']}", 
                               (10, int(y_pos)), self.font, self.font_scale, error_color, self.font_thickness)
                else:
                    cv2.putText(ui_canvas, "ROBOT STATUS", (10, int(y_pos)), 
                               self.font, 0.55, (255, 150, 255), 2)
                    y_pos += 25
                    cv2.putText(ui_canvas, "No robot status data available", 
                               (10, int(y_pos)), self.font, self.font_scale, (200, 200, 200), self.font_thickness)
                    y_pos += self.line_height
            except Exception as e:
                cv2.putText(ui_canvas, "ROBOT STATUS ERROR", (10, int(y_pos)), 
                           self.font, 0.55, (255, 150, 255), 2)
                y_pos += self.line_height
            
            return ui_canvas
            
        except Exception as e:
            print(f"[UI ERROR] Data overlay error: {e}")
            # Return a simple fallback canvas
            fallback_canvas = np.zeros((self.ui_height, self.ui_width, 3), dtype=np.uint8)
            fallback_canvas.fill(40)
            cv2.rectangle(fallback_canvas, (10, 30), (390, 70), (255, 0, 0), -1)
            return fallback_canvas
    
    def show_combined_view(self, show_data_window=True):
        """Show the robot feed with optional data overlay window"""
        try:
            # Get the latest frame from socket_stream directly
            from processing.socket_server import latest_frame, frame_lock

            frame = None
            got_frame = False
            try:
                with frame_lock:
                    if latest_frame is not None:
                        frame = latest_frame.copy()
                        got_frame = True
                    else:
                        print("No frame available")
            except Exception as e:
                print(f"[UI ERROR] Frame grab error: {e}")

            if got_frame and frame is not None:
                cv2.imshow("Robot Dog Feed", frame)
            else:
                # Show placeholder if no new frame
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(placeholder, "Waiting for frame...", (50, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.imshow("Robot Dog Feed", placeholder)
            
            if show_data_window:
                data_overlay = self.create_data_overlay()
                cv2.imshow("Robot Data", data_overlay)
            
            return cv2.waitKey(1) & 0xFF
        except Exception as e:
            print(f"[UI ERROR] Combined view error: {e}")
            # Create a simple fallback window
            fallback = np.zeros((300, 400, 3), dtype=np.uint8)
            cv2.imshow("Robot Dog - Fallback View", fallback)
            return cv2.waitKey(1) & 0xFF
    
    def show_side_by_side(self):
        """Show frame and data side by side in one window"""
        try:
            # Get the latest frame from socket_frame_recv
            from processing.socket_server import latest_frame, frame_lock
            
            # Create data overlay
            data_overlay = self.create_data_overlay()
            
            # Get frame with thread safety
            frame = None
            with frame_lock:
                if latest_frame is not None:
                    frame = latest_frame.copy()
            
            if frame is not None:
                # Resize frame to match data overlay height
                frame_height = data_overlay.shape[0]
                aspect_ratio = frame.shape[1] / frame.shape[0]
                frame_width = int(frame_height * aspect_ratio)
                frame_resized = cv2.resize(frame, (frame_width, frame_height))
                
                # Combine horizontally
                combined = np.hstack([frame_resized, data_overlay])
                cv2.imshow("Robot Dog - Combined View", combined)
            else:
                # Create a placeholder frame
                placeholder = np.zeros((data_overlay.shape[0], data_overlay.shape[0], 3), dtype=np.uint8)
                cv2.putText(placeholder, "No Video Feed", (50, int(placeholder.shape[0]//2)), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # Combine horizontally
                combined = np.hstack([placeholder, data_overlay])
                cv2.imshow("Robot Dog - Combined View", combined)
            
            return cv2.waitKey(1) & 0xFF
        except Exception as e:
            print(f"[UI ERROR] Side-by-side view error: {e}")
            # Create a simple fallback window
            fallback = np.zeros((300, 400, 3), dtype=np.uint8)
            cv2.imshow("Robot Dog - Fallback View", fallback)
            return cv2.waitKey(1) & 0xFF
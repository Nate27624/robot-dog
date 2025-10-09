import numpy as np
import logging
import asyncio
import time
import json
from go2_webrtc_driver.constants import RTC_TOPIC

# Global LIDAR data storage
lidar_data = {
    'point_cloud': None,
    'lidar_state': None,
    'last_updated': {}
}

def lidar_state_callback(message):
    """Callback for LIDAR state updates"""
    lidar_data['lidar_state'] = message['data']
    lidar_data['last_updated']['lidar_state'] = time.time()
    logging.info(f"LIDAR state updated: {message['data']}")

def voxel_map_callback(message):
    """Callback for LIDAR voxel map data"""
    try:
        # Extract point cloud data
        data = message['data']
        
        # Process point cloud data if needed
        positions = data.get('positions', [])
        
        if positions:
            # Store processed data
            lidar_data['point_cloud'] = {
                'points': positions,  # Already in the correct format
                'stamp': data.get('stamp'),
                'frame_id': data.get('frame_id'),
                'resolution': data.get('resolution'),
                'origin': data.get('origin'),
                'width': data.get('width'),
                'point_count': len(positions)
            }
            
            logging.info(f"Point cloud updated: {len(positions)} points")
        else:
            lidar_data['point_cloud'] = {
                'points': [],
                'point_count': 0
            }
            logging.warning("Received empty point cloud data")
            
        lidar_data['last_updated']['point_cloud'] = time.time()
        
    except Exception as e:
        logging.error(f"Error processing voxel map data: {e}")

async def setup_lidar(conn):
    """Setup LIDAR data collection"""
    try:
        logging.info("Setting up LIDAR data collection...")
        
        # Disable traffic saving mode for better LIDAR data
        await conn.datachannel.disableTrafficSaving(True)
        
        # Set the decoder type to libvoxel (from the example)
        conn.datachannel.set_decoder(decoder_type='libvoxel')
        
        # Turn on the LIDAR sensor
        logging.info("Turning on LIDAR sensor...")
        conn.datachannel.pub_sub.publish_without_callback("rt/utlidar/switch", "on")
        
        # Wait for LIDAR to initialize
        await asyncio.sleep(2)
        
        # Subscribe to LIDAR voxel map data (this is the key subscription from the example)
        logging.info("Subscribing to LIDAR voxel map data...")
        conn.datachannel.pub_sub.subscribe("rt/utlidar/voxel_map_compressed", voxel_map_callback)
        
        # Also subscribe to LIDAR state if available
        try:
            conn.datachannel.pub_sub.subscribe(RTC_TOPIC['ULIDAR_STATE'], lidar_state_callback)
        except Exception as e:
            logging.warning(f"Could not subscribe to LIDAR state: {e}")
        
        logging.info("LIDAR setup complete")
        
        # Start a periodic check to ensure LIDAR is still active
        asyncio.create_task(periodic_lidar_check(conn))
        
        return True
        
    except Exception as e:
        logging.error(f"Error setting up LIDAR: {e}")
        return False

async def periodic_lidar_check(conn):
    """Periodically check LIDAR status and reactivate if needed"""
    while True:
        try:
            # Check if we've received any LIDAR data recently
            current_time = time.time()
            last_update = lidar_data['last_updated'].get('point_cloud', 0)
            
            # If no data for more than 10 seconds, try to reactivate
            if current_time - last_update > 10 and last_update > 0:
                logging.warning("No LIDAR data received recently, attempting to reactivate...")
                conn.datachannel.pub_sub.publish_without_callback("rt/utlidar/switch", "on")
                
        except Exception as e:
            logging.error(f"Error in periodic LIDAR check: {e}")
            
        await asyncio.sleep(5)  # Check every 5 seconds

def get_lidar_data():
    """Get the current LIDAR data"""
    return lidar_data
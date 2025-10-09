import json
import time
import logging
import asyncio
from go2_webrtc_driver.constants import RTC_TOPIC, VUI_COLOR

# Import our LIDAR module
from lidarfunc import setup_lidar, get_lidar_data

# Global robot data storage
robot_data = {
    'sportmode': None,
    'multiplestate': None,
    'uwb_state': None,
    'service_state': None,
    'light': {
        'color': None,
        'brightness': None,
        'last_color_set': None
    },
    'last_updated': {}
}

# Data callback functions
def sportmode_callback(message):
    robot_data['sportmode'] = message['data']
    robot_data['last_updated']['sportmode'] = time.time()

def multiplestate_callback(message):
    try:
        robot_data['multiplestate'] = json.loads(message['data'])
        robot_data['last_updated']['multiplestate'] = time.time()
    except json.JSONDecodeError:
        robot_data['multiplestate'] = message['data']
        robot_data['last_updated']['multiplestate'] = time.time()

def uwb_state_callback(message):
    robot_data['uwb_state'] = message['data']
    robot_data['last_updated']['uwb_state'] = time.time()

def service_state_callback(message):
    robot_data['service_state'] = message['data']
    robot_data['last_updated']['service_state'] = time.time()

async def get_light_info(conn):
    """Get current light color and brightness"""
    try:
        # Get the current brightness
        response = await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["VUI"], 
            {"api_id": 1006}
        )
        if response['data']['header']['status']['code'] == 0:
            data = json.loads(response['data']['data'])
            robot_data['light']['brightness'] = data['brightness']
            robot_data['last_updated']['light_brightness'] = time.time()
            logging.info(f"Updated light brightness: {data['brightness']}")
        
        # We don't have a direct way to get current color, so we'll use the last set color
        # or default to white if unknown
        if not robot_data['light']['color']:
            robot_data['light']['color'] = 'white'  # Default color
            
    except Exception as e:
        logging.error(f"Error getting light info: {e}")

async def set_light_color(conn, color, time_seconds=5, flash_cycle=None):
    """Set the light color and optionally make it flash"""
    try:
        params = {
            "color": color,
            "time": time_seconds
        }
        
        if flash_cycle:
            params["flash_cycle"] = flash_cycle
            
        await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["VUI"], 
            {
                "api_id": 1007,
                "parameter": params
            }
        )
        
        # Update our stored color
        robot_data['light']['color'] = color
        robot_data['light']['last_color_set'] = time.time()
        robot_data['last_updated']['light_color'] = time.time()
        
        logging.info(f"Set light color to {color}" + 
                    (f" with flash cycle {flash_cycle}ms" if flash_cycle else ""))
                    
        return True
        
    except Exception as e:
        logging.error(f"Error setting light color: {e}")
        return False

async def setup_telemetry(conn):
    """Setup all telemetry data subscriptions"""
    try:
        logging.info("Setting up telemetry data subscriptions...")
        
        # Subscribe to sport mode state (movement, gait, position, etc.)
        conn.datachannel.pub_sub.subscribe(RTC_TOPIC['LF_SPORT_MOD_STATE'], sportmode_callback)
        
        # Subscribe to multiple state data (settings, switches, etc.)
        conn.datachannel.pub_sub.subscribe(RTC_TOPIC['MULTIPLE_STATE'], multiplestate_callback)
        
        # Setup LIDAR data collection
        await setup_lidar(conn)
        
        # Subscribe to UWB state
        conn.datachannel.pub_sub.subscribe(RTC_TOPIC['UWB_STATE'], uwb_state_callback)
        
        # Subscribe to service state
        conn.datachannel.pub_sub.subscribe(RTC_TOPIC['SERVICE_STATE'], service_state_callback)
        
        # Get initial light info
        await get_light_info(conn)
        
        # Schedule periodic light update
        asyncio.create_task(periodic_light_update(conn))
        
        logging.info("All telemetry subscriptions complete.")
        
    except Exception as e:
        logging.error(f"Error setting up telemetry: {e}")

async def periodic_light_update(conn):
    """Periodically update light information"""
    while True:
        try:
            await get_light_info(conn)
        except Exception as e:
            logging.error(f"Error in periodic light update: {e}")
            
        await asyncio.sleep(5)  # Update every 5 seconds

def get_telemetry_data():
    """Get the current telemetry data including LIDAR data"""
    # Get the latest LIDAR data
    lidar_data = get_lidar_data()
    
    # Combine all data
    combined_data = robot_data.copy()
    combined_data['lidar_state'] = lidar_data.get('lidar_state')
    combined_data['point_cloud'] = lidar_data.get('point_cloud')
    
    # Combine last_updated timestamps
    for key, value in lidar_data.get('last_updated', {}).items():
        combined_data['last_updated'][key] = value
        
    return combined_data
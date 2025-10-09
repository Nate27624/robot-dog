import asyncio
import logging
import json
import sys
from go2_webrtc_driver.webrtc_driver import Go2WebRTCConnection, WebRTCConnectionMethod
from go2_webrtc_driver.constants import RTC_TOPIC, SPORT_CMD

# Logging is configured in app.py
    
# Switches to normal mode so that the dog can perform the necessary task
async def switch_normal(conn:Go2WebRTCConnection):
        # Get the current motion_switcher status
        response = await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["MOTION_SWITCHER"], 
            {"api_id": 1001}
        )

        if response['data']['header']['status']['code'] == 0:
            data = json.loads(response['data']['data'])
            current_motion_switcher_mode = data['name']
            print(f"Current motion mode: {current_motion_switcher_mode}")

        # Switch # 1002 - BalanceStand implemented aboveto "normal" mode if not already
        if current_motion_switcher_mode != "normal":
            print(f"Switching motion mode from {current_motion_switcher_mode} to 'normal'...")
            await conn.datachannel.pub_sub.publish_request_new(
                RTC_TOPIC["MOTION_SWITCHER"], 
                {
                    "api_id": 1002,
                    "parameter": {"name": "normal"}
                }
            )
            await asyncio.sleep(5)  # Wait while it stands up


# 1001 - Kills robot turns off power basically but keeps robot on
async def damp(conn:Go2WebRTCConnection):
    await balance_stand(conn)
    # Perform a "Damp" movement
    print("Performing 'Damp' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {"api_id": SPORT_CMD["Damp"]}
    )

    await asyncio.sleep(0.5)
    print("Completed 'Damp' movement...")  

# 1002 - Unlocks the joints
async def balance_stand(conn:Go2WebRTCConnection):
    # Perform a "Balance Stand" movement
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {"api_id": SPORT_CMD["BalanceStand"]}
    )

    await asyncio.sleep(0.1)

# 1003 - Stop Current Movement
async def stop_move(conn:Go2WebRTCConnection):
    await balance_stand(conn)
    # Perform a "Stop" movement
    print("Performing 'Stop' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {"api_id": SPORT_CMD["StopMove"]}
    )

    print("Completed 'Stop' movement...")  

# 1004 - Stands the robot dog up
async def stand_up(conn:Go2WebRTCConnection):
    await balance_stand(conn)
    # Perform a "Damp" movement
    print("Performing 'Stand Up' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {"api_id": SPORT_CMD["StandUp"]}
    )

    await asyncio.sleep(0.5)
    print("Completed 'Stand Up' movement...")  

# 1005 - Stands (Sets) the robot dog down
async def stand_down(conn:Go2WebRTCConnection, time=None):
    await balance_stand(conn)
    # Perform a "Stand Down" movement
    print("Performing 'Stand Down' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {"api_id": SPORT_CMD["StandDown"]}
    )

    await asyncio.sleep(0.5)
    print("Completed 'Stand Down' movement...")  

    if time is not None:
        print(f"Sitting for {time} seconds...")
        await asyncio.sleep(time)
        print("Completed 'Sit' movement (standing up)...")
        await stand_up(conn)
    else:
        print("Completed 'Sit' movement...")

# 1006 - Stands robot dog up as fast as possible
async def recovery_stand(conn):
    await balance_stand(conn)
    print("Performing 'Recovery Stand' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": SPORT_CMD["RecoveryStand"]}
    )
    await asyncio.sleep(0.5)
    print("Completed 'Recovery Stand' movement...")

# 1007 - Rotates dog body
async def euler(conn, angles):
    await balance_stand(conn)
    x, y, z = angles
    print("Performing 'Euler' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {
            "api_id": SPORT_CMD["Euler"],
            "parameter": {"x": x, "y": y, "z": z}
        }
    )
    await asyncio.sleep(0.5)
    print("Completed 'Euler' movement...")

# 1008 - Moves dog body
async def move(conn, movement):
    await balance_stand(conn)
    x, y, z = movement
    print("Performing 'Move' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"],
        {
            "api_id": SPORT_CMD["Move"],
            "parameter": {"x": x, "y": y, "z": z}
        }
    )
    await asyncio.sleep(0.5)
    print("Completed 'Move' movement...")

# 1009 - Sits the robot dog (optionally for a specified time)
async def sit(conn, time=None):
    await balance_stand(conn)
    print("Performing 'Sit' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": SPORT_CMD["Sit"]}
    )
    await asyncio.sleep(0.5)
    
    if time is not None:
        print(f"Sitting for {time} seconds...")
        await asyncio.sleep(time)
        print("Completed 'Sit' movement (standing up)...")
        await rise_sit(conn)
    else:
        print("Completed 'Sit' movement...")

# 1010 - Stands the dog up from sitting position
async def rise_sit(conn):
    await balance_stand(conn)
    print("Performing 'Rise Sit' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": SPORT_CMD["RiseSit"]}
    )
    await asyncio.sleep(0.5)
    print("Completed 'Rise Sit' movement...")

# (X) 1011 - UNKNOWN Swtich Gait
'''
async def switch_gait(conn, value):
    await balance_stand(conn)
    print("Performing 'Switch Gait' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {
            "api_id": SPORT_CMD["SwitchGait"],
            "parameter": {"data": value}    
        }
    )
    await asyncio.sleep(2)
    print("Completed 'Switch Gait' movement...")
'''

# (X) 1012 - UNKNOWN NO EFFECT
'''
async def trigger(conn):
    await balance_stand(conn)
    print("Performing 'Trigger' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": SPORT_CMD["Trigger"]}
    )
    await asyncio.sleep(2)
    print("Completed 'Trigger' movement...")
'''

# (X) 1013 - Set Body Height
# (X) 1014 - Set FootRaiseHeight

# 1015 - (Not Working) Sets the speed level of the dog
'''
async def set_speed_level(conn, value):
    await balance_stand(conn)
    print("Performing 'Speed Level' movement...")
    response = await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {
            "api_id": 1015,  
            "parameter": {"data": value}       
        }
    )
    print("Completed 'Speed Level' movement...")
    return response
'''

# 1016 - Performs a hello movement
async def hello(conn):
    await balance_stand(conn)
    print("Performing 'Hello' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": SPORT_CMD["Hello"]}
    )
    await asyncio.sleep(0.5)
    print("Completed 'Hello' movement...")

# 1017 - Performs a stretch movement
async def stretch(conn):
    print("We made it here...")
    await balance_stand(conn)
    print("Performing 'Stretch' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": SPORT_CMD["Stretch"]}
    )
    await asyncio.sleep(0.5)
    print("Completed 'Stretch' movement...")

# (X) 1018 - COMPLICATED
'''
async def trajectory_follow(conn):
    await balance_stand(conn)
    print("Performing 'Trajectory Follow' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": SPORT_CMD["TrajectoryFollow"]}
    )
    await asyncio.sleep(2)
    print("Completed 'Trajectory Follow' movement...")
'''

# (X) 1019 - Continuous Gait

# 1020 - Happy Little Dance
async def content(conn):
    await balance_stand(conn)
    print("Performing 'Content' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {
            "api_id": 1020
        }
    )
    await asyncio.sleep(0.5)
    print("Completed 'Content' movement...")

# 1021 - Wallow - this doesn't work for some reason (on air)

# 1022 - Short Dance
async def dance1(conn):
    await balance_stand(conn)
    print("Performing 'Dance One' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {
            "api_id": 1022
        }
    )
    await asyncio.sleep(0.5)
    print("Completed 'Dance One' movement...")

# 1023 - Long Dance
async def dance2(conn):
    await balance_stand(conn)
    print("Performing 'Dance Two' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {
            "api_id": 1023
        }
    )
    await asyncio.sleep(0.5)
    print("Completed 'Dance Two' movement...")

# (X) 1024 - UNKNOWN BODY HEIGHT
'''
async def body_height(conn):
    await balance_stand(conn)
    print("Performing 'Body Height' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": SPORT_CMD["BodyHeight"]}
    )
    await asyncio.sleep(2)
    print("Completed 'Body Height' movement...")
'''

# (X) 1025 - UNKNOWN FOOT HEIGHT
'''
async def foot_raise_height(conn):
    await balance_stand(conn)
    print("Performing 'Foot Raise Height' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": SPORT_CMD["FootRaiseHeight"]}
    )
    await asyncio.sleep(2)
    print("Completed 'Foot Raise Height' movement...")
'''

# (X) 1026 - (Not Working) Gets the speed level of the dog 
'''
async def get_speed_level(conn):
    await balance_stand(conn)
    print("Performing 'Speed Level' movement...")
    response = await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {
            "api_id": 1026            
        }
    )
    print("Completed 'Speed Level' movement...")
    return response
'''

# 1027 - Switch Joystick ... Not implemented

# 1028 - UNKNOWN POSE
'''
async def pose(conn):
    await balance_stand(conn)
    print("Performing 'Pose' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {
            "api_id": 1028,
            "parameter": {"data": True}
        }
    )
    await asyncio.sleep(0.5)
    print("Completed 'Pose' movement...")
'''
    
# 1029 - Goes on its knees
async def scrape(conn):
    await balance_stand(conn)
    print("Performing 'Scrape' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": SPORT_CMD["Scrape"]}
    )
    await asyncio.sleep(0.5)
    print("Completed 'Scrape' movement...")

# 1030 - Performs a front flip
async def frontflip(conn):
    await balance_stand(conn)
    print("Performing 'FrontFlip' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {
            "api_id": 1030,
            "parameter": {"data": True}
        }
    )
    await asyncio.sleep(5)
    print("Completed 'FrontFlip' movement...")

####### 

# 1031 - Front Jump
async def front_jump(conn):
    await balance_stand(conn)
    print("Performing 'Front Jump' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": 1031}
    )
    await asyncio.sleep(0.5)
    print("Completed 'Front Jump' movement...")

# 1032 - Front Pounce
async def front_pounce(conn):
    await balance_stand(conn)
    print("Performing 'Front Pounce' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": 1032}
    )
    await asyncio.sleep(0.5)
    print("Completed 'Front Pounce' movement...")

# 1036 - Performs a heart movement
async def heart(conn):
    await balance_stand(conn)
    print("Performing 'FingerHeart' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": SPORT_CMD["FingerHeart"]}
    )
    await asyncio.sleep(0.5)
    print("Completed 'FingerHeart' movement...")

# 1061 - Switches dog to normal walking
async def staticwalk(conn):
    await balance_stand(conn)
    print("Performing 'StaticWalk' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": 1061}
    )
    await asyncio.sleep(0.5)
    print("Completed 'StaticWalk' movement...")

# 1062 - Switches the dog to run mode
async def trotrun(conn):
    await balance_stand(conn)
    print("Performing 'TrotRun' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": 1062}
    )
    await asyncio.sleep(0.5)
    print("Completed 'TrotRun' movement...")

# 1063 - Switches to normal walking
async def economicgate(conn):
    await balance_stand(conn)
    print("Performing 'EconomicGate' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": 1063}
    )
    await asyncio.sleep(0.5)
    print("Completed 'EconomicGate' movement...")

# 2041 - Performs a left flip
async def leftflip(conn):
    await balance_stand(conn)
    print("Performing 'LeftFlip' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {
            "api_id": 2041,
            "parameter": {"data": True}
        }
    )
    await asyncio.sleep(5)
    print("Completed 'LeftFlip' movement...")

# (??????) 2042 - Performs a right flip
async def rightflip(conn):
    await balance_stand(conn)
    print("Performing 'RightFlip' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {
            "api_id": 2042,
            "parameter": {"data": True}
        }
    )
    await asyncio.sleep(5)
    print("Completed 'RightFlip' movement...")

# 2043 - Performs a back flip
async def backflip(conn):
    await balance_stand(conn)
    print("Performing 'BackFlip' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {
            "api_id": 2043, 
            "parameter": {"data": True}
        }
    )
    await asyncio.sleep(5)
    print("Completed 'BackFlip' movement...")

# 2044 - Performs a hand stand for a certain length of time
async def handstand(conn, length):
    await balance_stand(conn)
    print("Performing 'HandStand' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {
            "api_id": 2044,
            "parameter": {"data": True}
        }
    )
    await asyncio.sleep(length)
    print("Completed 'HandStand' movement (returning to normal)...")

    await classicwalk(conn)

# 2045 - UNKNOWN WALK
'''
async def freewalk(conn):
    await balance_stand(conn)
    print("Performing 'FreeWalk' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": SPORT_CMD["FreeWalk"]}
    )
    await asyncio.sleep(2)
    print("Completed 'FreeWalk' movement...")
'''

# 2046/1304 - UNKNOWN BOUND (This one we maybe can get working)
'''
async def freebound(conn):
    await balance_stand(conn)
    print("Performing 'FreeBound' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {
            "api_id": 1304,
            "parameter": {"data": True}
        }
    )
    await asyncio.sleep(2)
    print("Completed 'FreeBound' movement...")
'''

# 2047 - UNKNOWN JUMP
'''
async def freejump(conn):
    await balance_stand(conn)
    print("Performing 'FreeJump' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {
            "api_id": 2047,
            "parameter": {"data": True}
        }
    )
    await asyncio.sleep(2)
    print("Completed 'FreeJump' movement...")
'''

# 2048 - UNKNOWN AVOIDANCE
'''
async def freeavoid(conn):
    await balance_stand(conn)
    print("Performing 'FreeAvoid' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {
            "api_id": 2048,
            "parameter": {"data": True}
        }
    )
    await asyncio.sleep(2)
    print("Completed 'FreeAvoid' movement...")
'''

# 2049 - Returns from hand stand to the regular walking mode
async def classicwalk(conn):
    await balance_stand(conn)
    print("Performing 'ClassicWalk' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {
            "api_id": 2049,
            "parameter": {"data": True}
        }
    )
    await asyncio.sleep(0.5)
    print("Completed 'ClassicWalk' movement...")

# 2050 - Walks on its feet like a human for specified time
async def walkupright(conn, time):
    await balance_stand(conn)
    print("Performing 'WalkUpRight' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"],
        {
            "api_id": 2050,
            "parameter": {"data": True}
        }
    )
    await asyncio.sleep(time)
    print("Completed 'WalkUpRight' movement (returning to normal)...")

    await classicwalk(conn)

# 2051 - Performs a Cross Stop Movement
async def crossstep(conn, time):
    await balance_stand(conn)
    print("Performing 'CrossStep' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], 
        {
            "api_id": 2051,
            "parameter": {"data": True}
        }
    )
    await asyncio.sleep(time)
    print("Completed 'CrossStep' movement (returning to normal)...")

    await classicwalk(conn)

# 2054 - UNKNOWN Sets Autorecovery (Seems Redundant)
'''
async def autorecoveryset(conn):
    await balance_stand(conn)
    print("Performing 'AutoRecoverySet' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": SPORT_CMD["AutoRecoverySet"]}
    )
    await asyncio.sleep(2)
    print("Completed 'AutoRecoverySet' movement...")
'''

# 2055 -  UNKNOWN Gets Autorecovery (Seems Redundant)
'''
async def autorecoveryget(conn):
    await balance_stand(conn)
    print("Performing 'AutoRecoveryGet' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": SPORT_CMD["AutoRecoveryGet"]}
    )
    await asyncio.sleep(2)
    print("Completed 'AutoRecoveryGet' movement...")
'''

# 2058 - UNKNOWN Switches avoidance mode
'''
async def switchavoidmode(conn):
    await balance_stand(conn)
    print("Performing 'SwitchAvoidMode' movement...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"], {"api_id": 2058}
    )
    await asyncio.sleep(2)
    print("Completed 'SwitchAvoidMode' movement...")
'''

async def main():
    try:
        # Choose a connection method (uncomment the correct one)
        #conn = Go2WebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.1.138")
        conn = Go2WebRTCConnection(WebRTCConnectionMethod.LocalSTA, serialNumber="B42D1000P5GE828H")
        # conn = Go2WebRTCConnection(WebRTCConnectionMethod.Remote, serialNumber="B42D1000P5GE828H", username="email@gmail.com", password="pass")
        # conn = Go2WebRTCConnection(WebRTCConnectionMethod.LocalAP)

        # Connect to the WebRTC service.
        await conn.connect()
        await dance2(conn)
        

    except ValueError as e:
        # Log any value errors that occur during the process.
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Handle Ctrl+C to exit gracefully.
        print("\nProgram interrupted by user")
        sys.exit(0)
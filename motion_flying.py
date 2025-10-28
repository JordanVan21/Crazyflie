import logging
import time
import sys
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-b", "--battery", action="store_true", help="Check battery status without flight")

args = parser.parse_args()

# URI to the Crazyflie to connect to
URI = uri_helper.uri_from_env(default='radio://0/30/2M/E7E7E7E7E7')
deck_attached_event = Event()


DEFAULT_HEIGHT = 0.5
BOX_LIMIT = 0.1
CALLBACK_AMT = 5
callback_count = 0
position_estimate = [0, 0]

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def param_deck_flow(name, value_str):
    value = int(value_str)
    print(f"{name} with value: {value}")
    if value:
        deck_attached_event.set()
        print('Deck is attached!')
    else:
        print('Deck is NOT attached!')

def take_off(scf):
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        time.sleep(3)
        mc.stop()

# NOT SMOOTH, worse than normal takeoff
def smooth_takeoff(mc, target_height=DEFAULT_HEIGHT, step=0.05, delay=0.3):
    cur_height = 0.0
    while cur_height < target_height:
        cur_height += step
        mc.up(step)
        time.sleep(delay)
    time.sleep(2)

def linear_movement(mc):
    # forward/backward etc take velocities. sleep is needed to execute those velocities
    time.sleep(3)
    mc.forward(0.5)
    time.sleep(1)
    mc.turn_left(180)
    time.sleep(1)
    mc.forward(0.5)
    time.sleep(2)

def box_movement(mc):
    body_x_cmd = 0.2
    body_y_cmd = 0
    max_vel = 0.2
    #comments are made assuming x is forward
    while (True):
        time.sleep(1)
        if position_estimate[0] >= BOX_LIMIT and position_estimate[1] <= BOX_LIMIT:
            print("GO RIGHT")
            body_y_cmd = max_vel
            body_x_cmd = 0
        elif position_estimate[0] >= BOX_LIMIT and position_estimate[1] >= BOX_LIMIT:
            print("GO BACK")
            body_y_cmd = 0
            body_x_cmd = -max_vel
        elif position_estimate[0] <= -BOX_LIMIT and position_estimate[1] <= BOX_LIMIT:
            print("GO LEFT")
            body_y_cmd = -max_vel
            body_x_cmd = 0
        elif position_estimate[0] <= -BOX_LIMIT and position_estimate[1] <= -BOX_LIMIT:
            print("GO FORWARD")
            body_y_cmd = 0
            body_x_cmd = max_vel
        
        time.sleep(1)
        mc.start_linear_motion(body_x_cmd, body_y_cmd, 0)
        

    # body_x_cmd = 0.2
    # body_y_cmd = 0.1
    # max_vel = 0.2

    # while (1):
    #     if position_estimate[0] > BOX_LIMIT:
    #         body_x_cmd=-max_vel
    #     elif position_estimate[0] < -BOX_LIMIT:
    #         body_x_cmd=max_vel

    #     if position_estimate[1] > BOX_LIMIT:
    #         body_y_cmd=-max_vel
    #     elif position_estimate[1] < -BOX_LIMIT:
    #         body_y_cmd=max_vel

    #     mc.start_linear_motion(body_x_cmd, body_y_cmd, 0)

    #     time.sleep(0.1)


    
def log_pos_callback(timestamp, data, logconf):
    print(data)
    global position_estimate
    position_estimate[0] = data['stateEstimate.x']
    position_estimate[1] = data['stateEstimate.y']

def log_battery_callback(timestamp, data, batconf):
    """Callback function for battery logging."""
    voltage = data['pm.vbat']
    level = data['pm.batteryLevel']
    print(f"TIME: {timestamp}, Battery Voltage: {voltage:.2f}V, Battery Level: {level:.0f}%")

    global callback_count
    callback_count += 1
    if callback_count >= CALLBACK_AMT:
        batconf.stop()


def config_pos(cf):
    logconf = LogConfig(name='Position', period_in_ms=1000)
    logconf.add_variable('stateEstimate.x', 'float')
    logconf.add_variable('stateEstimate.y', 'float')
    cf.log.add_config(logconf)
    logconf.data_received_cb.add_callback(log_pos_callback)
    return logconf

def config_bat(cf):
    batconf = LogConfig(name='Battery', period_in_ms=10)
    batconf.add_variable('pm.vbat', 'float')  # Battery voltage
    batconf.add_variable('pm.batteryLevel', 'uint8_t') # Battery level percentage
    cf.log.add_config(batconf)
    batconf.data_received_cb.add_callback(log_battery_callback)
    return batconf


def main():
     # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    # cache config caraibles and logging variables for faster response
    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        cf = scf.cf
        cf.param.add_update_callback(group='deck', name='bcFlow2',
            cb=param_deck_flow) 

        time.sleep(1)  

        if not deck_attached_event.wait(timeout=5):
            print('No flow deck detected')
            sys.exit(1)

        scf.cf.platform.send_arming_request(True)
        time.sleep(1.0)

        logconf = config_pos(cf)
        logconf.start()
        with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        #     smooth_takeoff(mc)
            logger.info("TAKEOFF")
            # linear_movement(mc)
            box_movement(mc)
        logconf.stop()

def check_battery():
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    # cache config caraibles and logging variables for faster response
    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        cf = scf.cf
        cf.param.add_update_callback(group='deck', name='bcFlow2',
            cb=param_deck_flow) 

        time.sleep(1)  

        batconf = config_bat(cf)
        batconf.start()
        time.sleep(0.2)

if __name__ == '__main__':
    if args.battery:
        check_battery()
    else:
        main()
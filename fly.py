import logging
import sys
import time
from threading import Event
import warnings


import cflib.crtp #scan crazyflie instances
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils.multiranger import Multiranger
from cflib.utils import uri_helper


URI = uri_helper.uri_from_env(default='radio://0/30/2M/E7E7E7E7E7')
deck_attached_event = Event()

DEFAULT_HEIGHT = 1.2
BOX_LIMIT = 0.5
BOOST_HEIGHT = 1.5
current_range = {'front': 1000, 'back': 1000, 'left': 1000, 'right': 1000, 'zrange': 1000}

warnings.filterwarnings("ignore", category=DeprecationWarning)

def param_deck_flow(_, value_str):
    value = int(value_str)
    print(value)
    if value:
        deck_attached_event.set()
        print('Deck is attached!')
    else:
        print('Deck is NOT attached!')

def take_off_simple(scf):
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        time.sleep(3)
        mc.stop()

def multi_range_callback(timestamp, data, logconf):
    global current_range
    current_range['front'] = data['range.front']
    current_range['back'] = data['range.back']
    current_range['left'] = data['range.left']
    current_range['right'] = data['range.right']
    current_range['zrange'] = data['range.zrange']
    print(f"Front: {current_range['front']}, Back: {current_range['back']}, Left: {current_range['left']}, Right: {current_range['right']}, Z: {current_range['zrange']}")

def take_off_with_multiranger(scf, multi_ranger):
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        start_time = time.time()
        while time.time() - start_time < 10:  # Fly for 10 seconds
            # Check for hand detection below (zrange low value)
            if current_range['zrange'] < 200:  # hand close
                mc.up(BOOST_HEIGHT - DEFAULT_HEIGHT)  # raise drone
            else:
                mc.down(BOOST_HEIGHT - DEFAULT_HEIGHT)  # return to default

            # Basic obstacle avoidance
            if current_range['front'] < 700:  # obstacle front
                print("front")
                mc.back(0.5)
            elif current_range['back'] < 700:
                print("back")
                mc.start_linear_motion(0.5, 0.0, 0.0)  # slow backward
                time.sleep(0.5)
                mc.forward(0.5)
            elif current_range['left'] < 700:
                print("left")
                mc.right(0.5)
            elif current_range['right'] < 700:
                print("right")
                mc.left(0.5)

            # if multi_ranger.front < BOX_LIMIT:
            #     mc.back(0.15)
            # elif multi_ranger.left < BOX_LIMIT:
            #     mc.right(0.15)
            # elif multi_ranger.right < BOX_LIMIT:
            #     mc.left(0.15)
            # elif multi_ranger.back < BOX_LIMIT:
            #     mc.forward(0.15)

            time.sleep(0.1)  # loop delay
        mc.stop()



if __name__ == '__main__':

    cflib.crtp.init_drivers()
    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        scf.cf.param.add_update_callback(group='deck', name='bcFlow2',
                                         cb=param_deck_flow)
        time.sleep(1)
        if not deck_attached_event.wait(timeout=5):
            print('No flow deck detected!')
            sys.exit(1)

        # Arm the Crazyflie
        scf.cf.platform.send_arming_request(True)
        time.sleep(1.0)
        # take_off_simple(scf)

        # Log config for Multi-ranger
        log_config = LogConfig(name='Multiranger', period_in_ms=100)
        log_config.add_variable('range.front', 'float')
        log_config.add_variable('range.back', 'float')
        log_config.add_variable('range.left', 'float')
        log_config.add_variable('range.right', 'float')
        log_config.add_variable('range.zrange', 'float')

        scf.cf.log.add_config(log_config)
        log_config.data_received_cb.add_callback(multi_range_callback)
        log_config.start()

        time.sleep(1.0)
        multi_ranger = Multiranger(scf)
        take_off_with_multiranger(scf, multi_ranger)

        log_config.stop()


import math
import time
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

# START IN THE MIDDLE LEFT

# --- CONFIGURATION ---
URI = uri_helper.uri_from_env(default='radio://0/15/2M/E7E7E7E7E7')
LOOP_DIAMETER = 0.4     # Width of one loop in meters
LOOP_TIME = 6.0         # Seconds to complete ONE loop (Total Fig8 time = 12s)
FLIGHT_HEIGHT = 0.5

def fly_figure_8(scf):
    commander = scf.cf.commander
    
    # 1. CALCULATE VELOCITY
    # We need the same math as the circle:
    # Forward Speed = Circumference / Time
    circumference = math.pi * LOOP_DIAMETER
    velocity_x = circumference / LOOP_TIME
    
    # Yaw Rate = 360 degrees / Time
    yaw_rate = 360.0 / LOOP_TIME

    # 2. TAKEOFF
    print("Taking off...")
    for i in range(10):
        commander.send_hover_setpoint(0, 0, 0, FLIGHT_HEIGHT * (i/10))
        time.sleep(0.1)
    
    # Stabilize
    for _ in range(10):
        commander.send_hover_setpoint(0, 0, 0, FLIGHT_HEIGHT)
        time.sleep(0.1)

    # 3. FIGURE 8 SEQUENCE
    print("Starting Figure 8...")
    
    # Define the two phases of the Figure 8
    # Phase 1: Positive Yaw (Left Turn)
    # Phase 2: Negative Yaw (Right Turn)
    phases = [yaw_rate, -yaw_rate]
    
    step_time = 0.1
    steps_per_loop = int(LOOP_TIME / step_time)

    for current_yaw in phases:
        print(f"Starting Loop with Yaw: {current_yaw}")
        
        for _ in range(steps_per_loop):
            # CONSTANT FORWARD MOTION, CHANGING YAW
            commander.send_hover_setpoint(velocity_x, 0, current_yaw, FLIGHT_HEIGHT)
            time.sleep(step_time)

    # 4. LANDING
    print("Landing...")
    # Stop moving first!
    for _ in range(10):
        commander.send_hover_setpoint(0, 0, 0, FLIGHT_HEIGHT)
        time.sleep(0.1)
        
    for i in range(10):
        commander.send_hover_setpoint(0, 0, 0, FLIGHT_HEIGHT * (1 - i/10))
        time.sleep(0.1)
        
    commander.send_stop_setpoint()

if __name__ == '__main__':
    cflib.crtp.init_drivers()
    
    print("Connecting...")
    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        # Reset estimator to ensure (0,0) is the center
        scf.cf.param.set_value('kalman.resetEstimation', '1')
        time.sleep(0.1)
        scf.cf.param.set_value('kalman.resetEstimation', '0')
        time.sleep(2)
        
        fly_figure_8(scf)
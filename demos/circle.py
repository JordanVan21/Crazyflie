import math
import time
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper
# START IN THE BOTTOM RIGHT OF THE CAGE

# 1. SETUP
URI = uri_helper.uri_from_env(default='radio://0/15/2M/E7E7E7E7E7')

# Flight Parameters
CIRCLE_DIAMETER = 0.7       # Meters
START_HEIGHT = 0.3          # Start the spiral low
END_HEIGHT = 1.0            # End the spiral high
CIRCLE_TIME = 8.0           # Seconds to complete one full circle
N_LOOPS = 2                 # How many circles to fly

def fly_spiral(scf):
    cf = scf.cf
    commander = cf.commander

    # 2. CONSTANTS
    circumference = math.pi * CIRCLE_DIAMETER
    velocity_x = circumference / CIRCLE_TIME
    yaw_rate = 360.0 / CIRCLE_TIME
    
    # Calculate total height change needed
    height_diff = END_HEIGHT - START_HEIGHT

    # 3. TAKEOFF sequence
    print(f"Taking off to {START_HEIGHT}m...")
    for i in range(10):
        # Ramp up to START_HEIGHT
        commander.send_hover_setpoint(0, 0, 0, START_HEIGHT * (i/10))
        time.sleep(0.1)

    # Stabilize
    for _ in range(10):
        commander.send_hover_setpoint(0, 0, 0, START_HEIGHT)
        time.sleep(0.1)

    # 4. SPIRAL Sequence
    print("Starting Spiral Up...")
    step_time = 0.1
    steps_per_circle = int(CIRCLE_TIME / step_time)
    total_steps = steps_per_circle * N_LOOPS

    # We need the index 'i' to calculate progress
    for i in range(total_steps):
        # Calculate progress from 0.0 to 1.0
        progress = i / total_steps
        
        # Calculate current Z based on progress (Linear Interpolation)
        current_height = START_HEIGHT + (height_diff * progress)

        # Send command: Forward Vel, 0 Lat Vel, Yaw Rate, Variable Height
        commander.send_hover_setpoint(velocity_x, 0, yaw_rate, current_height)
        time.sleep(step_time)

    # 5. LANDING Sequence
    print("Landing...")
    # Stabilize at the final height before descending
    for _ in range(10):
        commander.send_hover_setpoint(0, 0, 0, END_HEIGHT)
        time.sleep(0.1)

    # Ramp down from END_HEIGHT to 0
    for i in range(20): # Slower landing
        commander.send_hover_setpoint(0, 0, 0, END_HEIGHT * (1 - i/20))
        time.sleep(0.1)

    commander.send_stop_setpoint()

if __name__ == '__main__':
    cflib.crtp.init_drivers()
    
    print(f"Connecting to {URI}...")
    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        # Reset Estimator
        scf.cf.param.set_value('kalman.resetEstimation', '1')
        time.sleep(0.1)
        scf.cf.param.set_value('kalman.resetEstimation', '0')
        time.sleep(2)

        fly_spiral(scf)
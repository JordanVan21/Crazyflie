import time
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper

# START IN THE MIDDLE

URI = uri_helper.uri_from_env(default='radio://0/15/2M/E7E7E7E7E7')

# Cube Dimensions
SIDE_LENGTH = 0.5  # Meters
VELOCITY = 0.3     # m/s (A bit faster for straight lines)

def fly_square_layer(mc):
    """
    Flies a square pattern using strafing (no turning).
    Path: Forward -> Left -> Back -> Right
    """
    # 1. Forward (X+)
    mc.forward(SIDE_LENGTH, velocity=VELOCITY)
    time.sleep(0.5) # Short pause for sharp corners

    # 2. Left (Y+)
    mc.left(SIDE_LENGTH, velocity=VELOCITY)
    time.sleep(0.5)

    # 3. Back (X-)
    mc.back(SIDE_LENGTH, velocity=VELOCITY)
    time.sleep(0.5)

    # 4. Right (Y-)
    mc.right(SIDE_LENGTH, velocity=VELOCITY)
    time.sleep(0.5)



if __name__ == '__main__':
    cflib.crtp.init_drivers()

    print("Connecting...")
    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        
        # Takeoff to the bottom of the cube (e.g., 0.3m off ground)
        with MotionCommander(scf, default_height=0.3) as mc:
            
            print("Trace Bottom Face...")
            fly_square_layer(mc)

            print("Going Up (Elevator)...")
            mc.up(SIDE_LENGTH, velocity=VELOCITY/2) # Go up slower for stability
            time.sleep(0.5)

            print("Trace Top Face...")
            fly_square_layer(mc)

            print("Returning to start...")
            mc.down(SIDE_LENGTH, velocity=VELOCITY/2)
            
            # The 'with' block ends here, triggering auto-land
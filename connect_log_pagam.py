import logging
import time
import cflib
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper
from threading import Event
from cflib.crtp import init_drivers, scan_interfaces


uri2 = 'radio://0/15/2M/E7E7E7E7E7'
deck_flow_event = Event()
deck_ranger_event = Event()

# Callback for Flow Deck detection
def param_deck_flow(_, value_str):
    if int(value_str):
        print("Flow deck detected.")
        deck_flow_event.set()
    else:
        print("Flow deck NOT detected.")

# Callback for Multi-ranger Deck detection
def param_deck_ranger(_, value_str):
    if int(value_str):
        print("Multi-ranger deck detected.")
        deck_ranger_event.set()
    else:
        print("Multi-ranger deck NOT detected.")

def main():
    cflib.crtp.init_drivers()

    init_drivers()
    
    print("Scanning interfaces for Crazyflies...")
    available = scan_interfaces()

    print("Found Crazyflies:")
    for uri in available:
        print(uri)
    

    with SyncCrazyflie(uri2, cf=Crazyflie(rw_cache='./cache')) as scf:
        # Add both deck detection callbacks
        scf.cf.param.add_update_callback(group='deck', name='bcFlow2', cb=param_deck_flow)
        scf.cf.param.add_update_callback(group='deck', name='bcMultiranger', cb=param_deck_ranger)

        print("🔍 Waiting for deck detections...")

        # Wait up to 5 seconds for both decks
        flow_detected = deck_flow_event.wait(timeout=5.0)
        ranger_detected = deck_ranger_event.wait(timeout=5.0)

        if not flow_detected:
            print("Flow deck not detected within timeout.")
        if not ranger_detected:
            print("Multi-ranger deck not detected within timeout.")
        if flow_detected and ranger_detected:
            print("Both decks detected successfully.")

if __name__ == "__main__":
    main()
import time
import numpy as np
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class TremorEmulator:
    def __init__(self, ip=None, is_simulation=True):
        self.is_simulation = is_simulation
        if not is_simulation:
            from xarm.wrapper import XArmAPI
            self.arm = XArmAPI(ip)
            self.initialize_arm()
        else:
            print("Running in Simulation mode (MuJoCo)")
            self.arm = None

    def initialize_arm(self):
        if self.is_simulation: return
        self.arm.motion_enable(enable=True)
        self.arm.set_mode(0) # Position mode
        self.arm.set_state(state=0)
        print("Arm initialized")

    def run_subject_simulation(self, subject_id):
        """Bridge to MuJoCo simulation."""
        from src.simulation.run_simulation import run_sim
        run_sim(subject_id)

    def cleanup(self):
        if self.arm:
            self.arm.disconnect()

if __name__ == "__main__":
    print("TremorEmulator template.")

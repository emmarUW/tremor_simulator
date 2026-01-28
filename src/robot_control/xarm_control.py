import time
import numpy as np
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class TremorEmulator:
    def __init__(self, ip=None, is_simulation=True):
        self.is_simulation = is_simulation
        self.ip = ip
        self.arm = None
        self.is_connected = False
        self.tremor_active = False
        
        # Testing stance (joint angles in degrees)
        # Standard "ready" position for tremor testing
        self.testing_stance = [0, -35, -55, 0, 0] 
        self.active_axis = 'X' 
        self.replication_mode = 'Cartesian' # 'Cartesian' or 'Joint'
        
        if not is_simulation and ip:
            self.connect(ip)

    def connect(self, ip):
        """Establish connection with the physical xArm 5."""
        try:
            from xarm.wrapper import XArmAPI
            self.ip = ip
            self.arm = XArmAPI(self.ip)
            self.initialize_arm()
            self.is_connected = True
            self.is_simulation = False
            return True, "Connected successfully"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def initialize_arm(self):
        """Reset arm state and enable motion with load compensation."""
        if not self.arm: return
        self.arm.clean_error()
        self.arm.motion_enable(enable=True)
        self.arm.set_mode(0) # Position mode for stance
        self.arm.set_state(state=0)
        
        # 1. Load Compensation (Critical for motion accuracy)
        # xArm Gripper (~0.8kg) + tool (~0.2kg). 
        # Incorrect load causes the controller to dampen "unexplained" motor currents.
        self.arm.set_tcp_load(1.0, [0, 0, 50]) 
        
        # 2. Physics-based Limits for 6Hz @ 5mm oscillation
        # v1.11.1 Firmware may be picky about extremely high values.
        # Let's use robust but high values.
        self.arm.set_tcp_jerk(20000)
        self.arm.set_tcp_maxacc(5000)
        self.arm.set_collision_sensitivity(1) 
        self.arm.set_reduced_max_tcp_speed(2000)
        
        print(f"Arm at {self.ip} initialized - Robust high-frequency mode.")

    def set_testing_stance(self):
        """Move to the predefined testing stance."""
        if not self.arm: return
        self.arm.set_mode(0)
        self.arm.set_state(0)
        self.arm.set_servo_angle(angle=self.testing_stance, speed=20, wait=True)

    def open_gripper(self):
        """Fully open the xArm gripper."""
        if not self.arm: return
        self.arm.set_gripper_enable(True)
        self.arm.set_gripper_mode(0)
        self.arm.set_gripper_position(850, wait=True)

    def close_gripper(self):
        """Fully close the xArm gripper."""
        if not self.arm: return
        self.arm.set_gripper_enable(True)
        self.arm.set_gripper_mode(0)
        self.arm.set_gripper_position(0, wait=True)

    def get_current_pose(self):
        """Returns the actual position [x, y, z, roll, pitch, yaw] using cached state."""
        if not self.arm:
            return None
        # Use self.arm.position which is updated by the background report thread
        # rather than get_position() which makes a blocking network request.
        return self.arm.position

    def toggle_tremor(self, subject_data=None, axis='X', mode='Cartesian'):
        """Toggles the high-frequency tremor replication."""
        if not self.arm: return False
        
        if self.tremor_active:
            self.tremor_active = False
            return False
        else:
            if subject_data is None:
                return False
            self.tremor_active = True
            self.active_axis = axis
            self.replication_mode = mode
            # Start streaming in a background thread
            import threading
            threading.Thread(target=self._stream_tremor, args=(subject_data,), daemon=True).start()
            return True

    def _stream_tremor(self, subject_data):
        """Internal loop to stream tremor offsets to the robot at 100Hz."""
        print(f"Preparing tremor stream for {self.ip}...")
        
        # 1. Process the data into physical displacement (mm)
        from src.data_processing.processor import DataProcessor
        dp = DataProcessor(fs=100.0)
        displacements = dp.estimate_displacement(subject_data['imu_accel'], peak_freq=6.2)
        
        # 2. Capture neutral base pose in Position Mode first
        self.arm.clean_error()
        self.arm.motion_enable(True)
        self.arm.set_mode(0)
        self.arm.set_state(0)
        time.sleep(0.2)
        
        ret, base_pose = self.arm.get_position()
        if ret != 0 or base_pose is None:
            print(f"Error: Could not get current position, code={ret}")
            self.tremor_active = False
            return
        
        # Capture base joints for Joint Mode
        ret, base_angles = self.arm.get_servo_angle(is_radian=False)
        if ret != 0:
            print(f"Error: Could not get current angles, code={ret}")
            self.tremor_active = False
            return

        print(f"Base state captured. Mode: {self.replication_mode}")

        # 3. Switch to Servo Mode (Mode 1)
        print("Switching to Servo Mode (Mode 1)...")
        self.arm.set_mode(1)
        self.arm.set_state(0)
        time.sleep(1.0) # Solid wait for mode transition
        
        if self.arm.mode != 1:
            print(f"CRITICAL: Failed to switch to Mode 1. Mode is {self.arm.mode}")
            self.tremor_active = False
            return
            
        print("Servo streaming started. Applying fade-in.")
        
        idx = 0
        fs = 100.0
        start_time = time.time()
        fade_duration = 1.0 
        fade_samples = int(fade_duration * fs)

        print(f"Streaming {len(displacements)} tremor samples @ 100Hz...")

        while self.tremor_active and idx < len(displacements):
            # Calculate fade factor for smooth start
            fade_in = min(1.0, idx / fade_samples)
            
            if self.replication_mode == 'Cartesian':
                # --- CARTESIAN MODE (Current Fallback) ---
                tx, ty, tz = base_pose[0], base_pose[1], base_pose[2]
                
                if self.active_axis == 'X':
                    tx += (displacements[idx][0] * fade_in)
                elif self.active_axis == 'Y':
                    ty += (displacements[idx][1] * fade_in)
                elif self.active_axis == 'Z':
                    tz += (displacements[idx][2] * fade_in)
                elif self.active_axis == 'All (XYZ)':
                    tx += (displacements[idx][0] * fade_in)
                    ty += (displacements[idx][1] * fade_in)
                    tz += (displacements[idx][2] * fade_in)
                
                target_pose = [tx, ty, tz, base_pose[3], base_pose[4], base_pose[5]]
                self.arm.set_servo_cartesian(target_pose)
                
            else:
                # --- JOINT MODE (New Experimental) ---
                # Map 1mm displacement to roughly 0.5 degrees of joint vibration
                # This bypasses the IK solver entirely.
                sens = 0.5 
                target_angles = list(base_angles)
                
                if self.active_axis == 'X':
                    target_angles[1] += (displacements[idx][0] * sens * fade_in) # Shoulder
                    target_angles[2] += (displacements[idx][0] * -sens * fade_in) # Elbow
                elif self.active_axis == 'Y':
                    target_angles[0] += (displacements[idx][1] * sens * fade_in) # Base Rotation
                elif self.active_axis == 'Z':
                    target_angles[1] += (displacements[idx][2] * sens * fade_in) # Shoulder
                    target_angles[2] += (displacements[idx][2] * sens * fade_in) # Elbow
                elif self.active_axis == 'All (XYZ)':
                    target_angles[0] += (displacements[idx][1] * sens * fade_in)
                    target_angles[1] += (displacements[idx][0] * sens * fade_in)
                    target_angles[2] += (displacements[idx][2] * sens * fade_in)
                
                self.arm.set_servo_angle_j(target_angles, is_radian=False)
            
            # Diagnostic Console Info (minimal)
            if idx % 100 == 0:
                if self.replication_mode == 'Cartesian':
                    print(f"[TREMOR PACKET] Sample: {idx} | Cartesian Offset: {tx-base_pose[0]:.2f}mm")
                else:
                    print(f"[TREMOR PACKET] Sample: {idx} | Joint Mode Streaming ({self.active_axis})")
            
            # Timing sync
            idx += 1
            expected_time = start_time + (idx / fs)
            wait = expected_time - time.time()
            if wait > 0:
                time.sleep(wait)

        print("Tremor stream complete. Reseting mode...")
        self.arm.set_mode(0)
        self.arm.set_state(0)
        self.tremor_active = False
        print("Robot returned to Position Mode.")

    def run_subject_simulation(self, subject_id):
        """Bridge to MuJoCo simulation."""
        from src.simulation.run_simulation import run_sim
        run_sim(subject_id)

    def cleanup(self):
        if self.arm:
            self.arm.disconnect()

if __name__ == "__main__":
    print("TremorEmulator template.")

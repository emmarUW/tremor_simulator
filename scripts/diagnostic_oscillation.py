from xarm.wrapper import XArmAPI
import time
import numpy as np

def run_diagnostic():
    ip = "192.168.1.220"
    arm = XArmAPI(ip)
    
    print(f"--- DIAGNOSTIC START: {ip} ---")
    arm.clean_error()
    arm.motion_enable(True)
    arm.set_mode(0)
    arm.set_state(0)
    time.sleep(1)

    # 1. Capture Base
    ret, base_pose = arm.get_position()
    print(f"Base Position: {base_pose}")

    # 2. Report current limits (to see if WebUI syncs or if we override)
    print("\n--- Current Limits Detected ---")
    print(f"TCP Accel Limit: {arm.tcp_acc_limit}")
    print(f"TCP Jerk: {arm.tcp_jerk}")
    print(f"Collision Sensitivity: {arm.collision_sensitivity}")
    
    # We will NOT call set_tcp_jerk or others here to see if the WebUI settings
    # persist and improve the 1Hz performance.
    
    # 3. Switch to Servo Mode
    print("\nSwitching to Servo Mode (Mode 1)...")
    arm.set_mode(1)
    arm.set_state(0)
    time.sleep(1)

    print("\n--- TEST: 6.2Hz Sine Wave (5mm amplitude) ---")
    print("Capturing Peak-To-Peak movement from encoders...")
    
    duration = 5.0 # seconds
    fs = 100.0     # 100Hz
    num_samples = int(duration * fs)
    
    measured_x_values = []
    start_time = time.time()
    
    for i in range(num_samples):
        # 6.2Hz tremor simulation (Our clinical frequency)
        t = i / fs
        offset = 5.0 * np.sin(2 * np.pi * 6.2 * t)
        
        target_pose = list(base_pose)
        target_pose[0] += offset
        
        arm.set_servo_cartesian(target_pose)
        
        # Sample the actual encoder position
        ret, cur = arm.get_position()
        if ret == 0:
            measured_x_values.append(cur[0])
            
        elapsed = time.time() - start_time
        sleep_time = (i + 1)/fs - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

    if measured_x_values:
        pk_to_pk = max(measured_x_values) - min(measured_x_values)
        print(f"\n--- RESULTS (6.2Hz) ---")
        print(f"Commanded Peak-to-Peak: 10.00mm (+5 to -5)")
        print(f"Measured Peak-to-Peak:  {pk_to_pk:.2f}mm")
        print(f"Samples collected:      {len(measured_x_values)}")
        
        # Theory check: Max physical amplitude at 6.2Hz given 2000mm/s2 limit is 1.3mm (2.6mm pk-pk)
        if pk_to_pk < 1.0:
            print("Conclusion: Cartesian Filter is aggressively muting the signal.")
        elif pk_to_pk < 3.0:
            print("Conclusion: Motion is occurring but is capped by physical Accel limits.")
        else:
            print("Conclusion: Hardware is tracking better than predicted.")
    else:
        print("Error: No position samples collected.")

    print("\nDiagnostic Complete. Returning to Mode 0.")
    arm.set_mode(0)
    arm.set_state(0)
    arm.disconnect()

if __name__ == "__main__":
    run_diagnostic()

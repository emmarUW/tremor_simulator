import mujoco
import mujoco.viewer
import numpy as np
import time
import pickle
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.data_processing.processor import DataProcessor

def load_subject_data(subject_id):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pickle_path = os.path.join(base_dir, 'data', 'imu_data.pkl')
    
    if not os.path.exists(pickle_path):
        raise FileNotFoundError(f"Cleaned dataset not found.")
    
    with open(pickle_path, 'rb') as f:
        data = pickle.load(f)
    
    if subject_id not in data:
        raise ValueError(f"Subject {subject_id} not found.")
    
    subject_info = data[subject_id]
    acc_data = subject_info['imu_accel']
    fs = 100.53
    
    processor = DataProcessor(fs=fs)
    # Extract tremor band (3-10Hz)
    filtered_accel = processor.bandpass_filter(acc_data)
    
    # Scale acceleration to displacement (heuristic)
    # A multiplier of 0.004 results in ~4mm tip movement for 1g acceleration
    # which is a realistic 1:1 clinical representation for PD tremors.
    SCALE = 0.004 
    displacement = filtered_accel * SCALE
    
    # 1-second fade-in to ensure physics stability at startup
    fade_len = int(fs)
    fade_in = np.linspace(0, 1, fade_len)
    displacement[:fade_len] *= fade_in[:, np.newaxis]
    
    return displacement, fs, subject_info['annotation'].get('pd_status', 0), SCALE

def run_sim(subject_id=9):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    model_path = os.path.join(base_dir, 'src', 'simulation', 'xarm5_tremor.xml')
    model = mujoco.MjModel.from_xml_path(model_path)
    model.opt.integrator = 1 # RK4
    model.opt.timestep = 0.001 
    data = mujoco.MjData(model)
    
    tremor_data, fs, is_pd, physical_scale = load_subject_data(subject_id)
    
    q_ready = [0.0, -0.6, -1.0, 0.4, 0.0]
    
    # Initial state
    for i in range(5):
        data.qpos[i] = q_ready[i]
        data.ctrl[i] = q_ready[i]
    if model.nu > 5:
        data.ctrl[5] = 0.02 # Gripper open
    
    mujoco.mj_forward(model, data)
    
    # Settle period
    for _ in range(200):
        mujoco.mj_step(model, data)
    
    with mujoco.viewer.launch_passive(model, data) as viewer:
        idx = 0
        status = "PARKINSONS" if is_pd == 1 else "CONTROL"
        print(f"--- SIMULATION: Subject {subject_id} ({status}) ---")
        
        prev_jitter = np.zeros(3)
        
        while viewer.is_running():
            step_start = time.time()
            
            if idx < len(tremor_data):
                target_jitter = tremor_data[idx]
                
                # Physics steps to reach next IMU sample with linear interpolation
                sub_steps = int((1.0/fs) / model.opt.timestep)
                for s in range(max(1, sub_steps)):
                    alpha = s / sub_steps
                    # Smoothly move from previous sample to current sample
                    current_jitter = prev_jitter * (1.0 - alpha) + target_jitter * alpha
                    
                    data.ctrl[0] = q_ready[0] + current_jitter[0]
                    data.ctrl[1] = q_ready[1] + current_jitter[1]
                    data.ctrl[2] = q_ready[2] + current_jitter[2]
                    
                    mujoco.mj_step(model, data)
                
                prev_jitter = target_jitter
                idx += 1
            else:
                idx = 0
                prev_jitter = np.zeros(3)
            
            viewer.sync()
            
            elapsed = time.time() - step_start
            if elapsed < 1.0/fs:
                time.sleep(1.0/fs - elapsed)

if __name__ == "__main__":
    sid = int(sys.argv[1]) if len(sys.argv) > 1 else 9
    run_sim(sid)

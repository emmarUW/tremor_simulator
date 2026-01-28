import pickle
import numpy as np
import matplotlib.pyplot as plt
from src.data_processing.processor import DataProcessor

def main():
    pickle_path = r"C:\Users\emmar\Desktop\Tremor_Emulator\data\raw\tremor_dataset.pickle"
    with open(pickle_path, 'rb') as f:
        data = pickle.load(f)
    
    # Select Subject 9, Session 0 (confirmed tremor)
    subject_id = 9
    subject = next((s for s in data if s.get('subject_id') == subject_id), None)
    session = subject.get('sessions', [])[0]
    
    # Process data
    # Column 0: time, 1-3: acc
    acc_data = session[:, 1:4]
    fs = 100.53 # From previous analysis
    
    processor = DataProcessor(fs=fs)
    tremor_displacement = processor.estimate_displacement(acc_data)
    
    # Scale for robot (e.g. 1.0 m/s^2 -> 2.0 mm of movement)
    robot_scale = 2.0 
    robot_motion = tremor_displacement * robot_scale
    
    # Plot first 5 seconds
    t = (session[:, 0] - session[0, 0]) / 1e9
    mask = t < 5.0
    
    plt.figure(figsize=(12, 8))
    plt.subplot(2, 1, 1)
    plt.plot(t[mask], acc_data[mask])
    plt.title("Original Filtered Acceleration (m/s^2)")
    plt.grid(True)
    
    plt.subplot(2, 1, 2)
    plt.plot(t[mask], robot_motion[mask])
    plt.title("Estimated Robot Displacement (mm)")
    plt.xlabel("Time (s)")
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig('notebooks/motion_simulation.png')
    print("Motion simulation plot saved to notebooks/motion_simulation.png")

if __name__ == "__main__":
    main()

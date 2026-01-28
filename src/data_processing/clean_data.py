import pickle
import os
import numpy as np

def clean_dataset():
    # Use relative paths anchored to the project root
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    raw_path = os.path.join(base_dir, 'data', 'raw', 'tremor_dataset.pickle')
    out_path = os.path.join(base_dir, 'data', 'imu_data.pkl')
    
    if not os.path.exists(raw_path):
        print(f"Error: Raw dataset not found at {raw_path}")
        return

    with open(raw_path, 'rb') as f:
        raw_data = pickle.load(f)

    cleaned = {}
    for item in raw_data:
        s_id = item.get('subject_id')
        sessions = item.get('sessions', [])
        
        if not sessions:
            continue
            
        # Use first session
        session_data = sessions[0]
        
        # Consistent mapping for Zenodo dataset columns: [time, ax, ay, az, ...]
        if isinstance(session_data, np.ndarray) and session_data.shape[1] >= 4:
            accel = session_data[:, 1:4]
        else:
            accel = session_data 
            
        cleaned[s_id] = {
            'imu_accel': accel,
            'annotation': item.get('annotation', {})
        }

    with open(out_path, 'wb') as f:
        pickle.dump(cleaned, f)
    
    print(f"Successfully created cleaned dataset with {len(cleaned)} subjects at {out_path}")

if __name__ == "__main__":
    clean_dataset()

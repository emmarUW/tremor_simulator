import pickle
import matplotlib.pyplot as plt
import numpy as np

def plot_session(file_path, subject_id, session_idx):
    with open(file_path, 'rb') as f:
        data = pickle.load(f)
    
    subject = next((s for s in data if s.get('subject_id') == subject_id), None)
    if not subject:
        print(f"Subject {subject_id} not found.")
        return
    
    sessions = subject.get('sessions', [])
    if session_idx >= len(sessions):
        print(f"Session {session_idx} not found for Subject {subject_id}.")
        return
    
    session = sessions[session_idx]
    # session: timestamps, x, y, z
    t = (session[:, 0] - session[0, 0]) / 1e9  # nanoseconds to seconds
    acc_x = session[:, 1]
    acc_y = session[:, 2]
    acc_z = session[:, 3]
    
    plt.figure(figsize=(12, 6))
    plt.title(f"Subject {subject_id}, Session {session_idx} - Accelerometer Raw Data")
    plt.plot(t, acc_x, label='X')
    plt.plot(t, acc_y, label='Y')
    plt.plot(t, acc_z, label='Z')
    plt.xlabel("Time (s)")
    plt.ylabel("Acceleration (m/s^2)")
    plt.legend()
    plt.grid(True)
    plt.savefig('notebooks/sample_session.png')
    print("Plot saved to notebooks/sample_session.png")

if __name__ == "__main__":
    file_path = r"C:\Users\emmar\Desktop\Tremor_Emulator\data\raw\tremor_dataset.pickle"
    plot_session(file_path, 9, 0)

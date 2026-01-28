import pickle
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq

def analyze_frequency(file_path, subject_id, session_idx):
    with open(file_path, 'rb') as f:
        data = pickle.load(f)
    
    subject = next((s for s in data if s.get('subject_id') == subject_id), None)
    sessions = subject.get('sessions', [])
    session = sessions[session_idx]
    
    # Timestamps are in nanoseconds
    dt = np.mean(np.diff(session[:, 0])) / 1e9
    fs = 1.0 / dt
    print(f"Sampling frequency: {fs:.2f} Hz")
    
    # Analyze Z-axis (often strongest in some orientations)
    y = session[:, 3]
    y = y - np.mean(y) # Remove DC
    
    n = len(y)
    yf = fft(y)
    xf = fftfreq(n, dt)[:n//2]
    
    plt.figure(figsize=(12, 6))
    plt.plot(xf, 2.0/n * np.abs(yf[0:n//2]))
    plt.title(f"Frequency Spectrum - Subject {subject_id}, Session {session_idx}")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Amplitude")
    plt.xlim(0, 20) # Tremors are usually < 10Hz
    plt.grid(True)
    plt.savefig('notebooks/frequency_spectrum.png')
    print("Spectrum saved to notebooks/frequency_spectrum.png")

if __name__ == "__main__":
    file_path = r"C:\Users\emmar\Desktop\Tremor_Emulator\data\raw\tremor_dataset.pickle"
    analyze_frequency(file_path, 9, 0)

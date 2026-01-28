import numpy as np
from scipy.signal import butter, filtfilt

class DataProcessor:
    def __init__(self, fs=100.0):
        self.fs = fs

    def butter_bandpass(self, lowcut, highcut, order=5):
        nyq = 0.5 * self.fs
        low = lowcut / nyq
        high = highcut / nyq
        b, a = butter(order, [low, high], btype='band')
        return b, a

    def filter_tremor(self, data, lowcut=3.0, highcut=10.0, order=5):
        """
        Applies a bandpass filter to extract Parkinson's tremor frequency.
        """
        b, a = self.butter_bandpass(lowcut, highcut, order=order)
        y = filtfilt(b, a, data, axis=0)
        return y

    def bandpass_filter(self, data, lowcut=3.0, highcut=10.0, order=5):
        """ Alias for filter_tremor used in simulation scripts. """
        return self.filter_tremor(data, lowcut, highcut, order)

    def estimate_displacement(self, accel_data, peak_freq=6.0):
        """
        Converts acceleration (m/s^2) to displacement (mm).
        Using the physical relationship for harmonic motion: d = a / (2*pi*f)^2
        """
        # 1. Isolate the tremor (3-10Hz)
        accel_filtered = self.filter_tremor(accel_data)
        
        # 2. Physics-based conversion
        # omega = 2 * pi * f
        omega = 2 * np.pi * peak_freq
        
        # Conversion factor for m/s^2 to mm:
        # displacement_m = accel_m_s2 / omega^2
        # displacement_mm = (accel_m_s2 / omega^2) * 1000
        conversion_factor = 1000.0 / (omega**2)
        
        # Note: In harmonic motion, displacement is out of phase with acceleration.
        # But for an emulator where we just want the 'shake', the sign doesn't matter 
        # as much as the magnitude and frequency. We use the negative sign to be 
        # physically correct (d = -a/w^2).
        displacement_mm = -accel_filtered * conversion_factor
        
        return displacement_mm

if __name__ == "__main__":
    dp = DataProcessor()
    print("DataProcessor initialized with butterworth bandpass filter.")

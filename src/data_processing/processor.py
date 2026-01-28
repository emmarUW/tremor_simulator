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

    def estimate_displacement(self, accel_data):
        """
        A very rough estimate of displacement from filtered acceleration.
        For small oscillations, displacement is proportional to -acceleration / omega^2.
        As a simplification for an emulator, we can normalize and scale.
        """
        # Remove gravity/bias
        filtered = self.filter_tremor(accel_data)
        # Numerical double integration with drift correction is complex.
        # For an emulator where 'realism' of the shake is more important than absolute spatial accuracy
        # relative to the phone, we can use the filtered acceleration as a displacement proxy 
        # after scaling (e.g. 1 m/s^2 tremor amplitude ~ physical shake magnitude).
        return filtered

if __name__ == "__main__":
    dp = DataProcessor()
    print("DataProcessor initialized with butterworth bandpass filter.")

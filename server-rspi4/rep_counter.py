import csv
import os 
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, butter, filtfilt
from scipy.fft import fft, fftfreq

class rep_counter():
    def __init__(self, CAT, file_name):
        self.DATA_CATEGORY = CAT
        self.DATA_FILE = os.path.join(os.getcwd(), file_name)
        self.axis_keys = {
            'Shoulder': {'x': 0, 'y': 0, 'z': 1},
            'Curl': {'x': 1, 'y': 0, 'z': 0},
            'latraise': {'x': 1, 'y': 0, 'z': 0}
        }

    def bandpass_filter(self, data, lowcut, highcut, fs, order=4):
        nyquist = 0.5 * fs
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = butter(order, [low, high], btype='band')
        return filtfilt(b, a, data)
    
    def run_peak_detection(self, verbose= False) -> int:
        #Initialize variables
        time  = []
        bpm_data = []
        total_bpm  = 0
        #xacc, yacc, zacc = [], [], []
        superacc = []
        gravity_offset = 1
        try:
            with open(self.DATA_FILE, 'r') as f:
                relevant_axis = self.axis_keys.get(self.DATA_CATEGORY)
                reader = csv.reader(f)
                next(reader)#skip title row
                for row in reader:
                    sum_acc = 0
                    time.append(float(row[0]))
                    if relevant_axis.get('x'): sum_acc += float(row[1])
                    if relevant_axis.get('y'): sum_acc += float(row[2])
                    if relevant_axis.get('z'): sum_acc += float(row[3]) - gravity_offset
                    bpm_data_temp = float(row[4])
                    if(40 < bpm_data_temp < 120):
                        bpm_data.append(row[4])
                        total_bpm += float(row[4])
                    superacc.append(sum_acc)
        except Exception as e:
            print(f"Error reading data source file {self.DATA_FILE}: {e}")

        superacc = np.array(superacc) - np.mean(superacc) #clear DC offset
        #calculate the average bpm
        if(bpm_data): #[] is falsy, so protects against div by zero!
            avg_bpm = total_bpm/len(bpm_data)
        else:
            avg_bpm = 0
        #FT analysis
        N = len(superacc)                 
        if N > 1:
            T = (time[-1] - time[0]) / (N - 1)
        else:
            T = 1

        yf = fft(superacc)  #Compute the FFT of the signal
        xf = fftfreq(N, T)[:N//2]#Frequency axis (only positive frequencies)
        lowcut = 0.1
        highcut = 1.0
        filtered_superacc = self.bandpass_filter(superacc, lowcut, highcut, fs=1/T)
        peaks, _ = find_peaks(filtered_superacc, prominence=0.1, distance=5)
        if(verbose):
            print(f"# Peaks found: {len(peaks)}")
            plt.figure(figsize=(10, 10))
            plt.plot(time, superacc, label='Original Sum of Accelerations (DC Offset Removed)', alpha=0.5)
            plt.plot(time, filtered_superacc, label='Filtered Sum of Accelerations', color='blue')
            plt.plot(np.array(time)[peaks], np.array(filtered_superacc)[peaks], "x", label="Peaks", color='red')
            plt.title('Acceleration over time with Fourier-Based Filtering')
            plt.xlabel("Time (s)")
            plt.ylabel("Acceleration (g)")
            plt.legend()
            plt.grid(True)
            plt.show()
        return (len(peaks), avg_bpm)


if __name__ == '__main__':
    rep_counter_obj = rep_counter(CAT= 'Shoulder', file_name= 'shoulder_10_reps.csv')
    rep_counter_obj.run_peak_detection(verbose= True)

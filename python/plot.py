import serial
import numpy as np
import random #remove when actually implemented
import matplotlib.pyplot as plt
from collections import deque
import time
import math #remove when actually implemented

port = 'COM3' #REPLACE WITH RELEVANT PORT
baud_rate = 115200
sample_period = 100e-6 #in seconds (before exponent in microseconds)

buffer_size = 2000 
raw_buffer = deque(maxlen=buffer_size) 
display_buffer = []

triggered_rising_edge = 0
period_sample_count = 0

render_interval = 0.05 #seconds (20 fps)
last_render = time.perf_counter()

waves_displayed = 10
period = None

edge_state = 0; # 0 = LOW, 1 = HIGH

x = list(range(0,buffer_size))
fig, ax = plt.subplots()
(line,) = ax.plot(x, [0]*buffer_size, color="blue")
plt.show(block=False)

ax.set_ylim(-10,10) #10V is the hypothetical max voltage the device can read

#set graph x=values
x_vals = np.arange(buffer_size) * sample_period
ax.set_xlim(0, max(x_vals))
line.set_xdata(x_vals)

ax.set_ylabel("Voltage (V)")
ax.set_xlabel("Time (s)")

plt.ion()

def updateFigure(data):
    '''
    Updates the figure used for visualizing voltage
    
    param data: a list or deque containing all the data to be displayed
    '''
    y = np.full(buffer_size, np.nan)
    n = min(len(data), buffer_size)
    y[:n] = data[:n]

    line.set_ydata(y)
    line.set_xdata(x_vals[:len(y)])
    fig.canvas.draw_idle()
    plt.pause(0.001)

def risingEdgeDetection(sample, state, low = 1.70, high = 2.3) -> bool:
    '''
    uses a schmitt trigger to detech a rising edge action in the signal
    
    :param data: sample being tested for rising edge
    :param state: the current state of the program (high/low)
    :return: returns bool that reflects the new state
    :rtype: bool
    '''
    if state == 0 and sample >= high:
        return True, 1

    if state == 1 and sample <= low:
        return False, 0

    return False, state

fs = 3_000 #3kHz sample rate
dt = 1 / fs
t = 0.0
signal_freq = 30

try:
    '''
    #connect to serial port
    print(f"Attempting to establish connection to {port} at {baud_rate}.")
    ser = serial.Serial(port, baud_rate)
    time.sleep(2) #time for connection to properly establish
    print(f"Connection established successfully.")
    '''
    while True:
        #read new data
        '''
        raw_data = ser.readline()
        decoded_data = raw_data.decode("utf-8").strip()
        
        try:
            sample = 2.0 * float(decoded_data) * 5.0 / 1023.0 #convert from sensor values to voltage values
        except ValueError:
            continue
        '''
        noise_amplitude = 0.2  # volts (adjust)

        sample = (
            2.5 - 2.5
            + 2.5 * math.sin(2 * math.pi * signal_freq * t)
            + random.uniform(-noise_amplitude, noise_amplitude)
        )

        t += dt
        raw_buffer.append(sample)

        edge_detected, edge_state = risingEdgeDetection(sample, edge_state)

        #detect rising edge
        if edge_detected:
            if triggered_rising_edge == 0:
                #first edge: start capturing information
                triggered_rising_edge = 1
                period_sample_count = 0
                display_buffer.clear()
            else: # if not the first edge, must be second edge -> measure period
                period = period_sample_count
                period_sample_count = 0

        #Capture samples after trigger
        if triggered_rising_edge:
            period_sample_count += 1
            display_buffer.append(sample)

            # Stop after enough waves collected
            if period is not None:
                max_samples = period * waves_displayed
                if len(display_buffer) >= max_samples:
                    triggered_rising_edge = 0
                    period_sample_count = 0
                    period = None

        #update figure
        now = time.perf_counter()
        if (now - last_render) >= render_interval:
            last_render = now
            updateFigure(display_buffer)

except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
except KeyboardInterrupt:
    print(f"Serial interrupted by user")
except Exception as e:
    print(f"An unexpected error occured: {e}")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Serial port closed")
    plt.close(fig)
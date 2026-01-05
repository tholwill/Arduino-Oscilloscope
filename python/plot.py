import serial
import threading
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
import time

running = True

port = 'COM3' 
baud_rate = 115200
sample_period = 65e-6 #in seconds (before exponent in microseconds)

buffer_size = 2000 
raw_buffer = deque(maxlen=buffer_size) 
display_buffer = []

triggered_rising_edge = 0
period_sample_count = 0

render_interval = 0.05 #seconds (20 fps)
last_render = time.perf_counter()

waves_displayed = 5
period = None

edge_state = 0; # 0 = LOW, 1 = HIGH
mode = 0; # 0 = Standard, 1 = Rising edge detection

x = list(range(0,buffer_size))
fig, ax = plt.subplots()
(line,) = ax.plot(x, [0]*buffer_size, color="blue")
plt.show(block=False)

ax.set_ylim(0,3) #10V is the hypothetical max voltage the device can read
                 #However with the current setup I am using 3 is more useful

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

def risingEdgeDetection(sample, state, low = 1.20, high = 1.4) -> bool:
    '''
    uses a schmitt trigger to detech a rising edge action in the signal
    
    :param sample: sample being tested for rising edge
    :param state: the current state of the program (high/low)
    :return: returns bool that reflects the new state
    :rtype: bool
    '''
    if state == 0 and sample >= high:
        return True, 1

    if state == 1 and sample <= low:
        return False, 0

    return False, state

def switchMode():
    '''
    Analyses user input to determine whether the oscilloscope should use rising edge detection or not
    '''
    global mode, triggered_rising_edge, period_sample_count, running
    user_input = None
    while True:
        user_input = input()
        if user_input == 's': #s for "Switch mode"
            mode = 1 - mode   #swap between 0 and 1
            
            display_buffer.clear()

            if mode == 0:
                print("Mode switched to standard")
            elif mode == 1:
                print("Mode switched to rising edge detection")
                triggered_rising_edge = 0
                period_sample_count = 0
        elif user_input == 'q': #exit program
            running = False
            print("Program terminated by user")

#allow for continuous input monitoring for mode switching
threading.Thread(target=switchMode, daemon = True).start()

try:
    #connect to serial port
    print(f"Attempting to establish connection to {port} at {baud_rate}.")
    ser = serial.Serial(port, baud_rate)
    time.sleep(2) #time for connection to properly establish
    print(f"Connection established successfully.")
    
    while running:
        #read new data
        raw_data = ser.readline()
        decoded_data = raw_data.decode("utf-8").strip()
        
        try:
            sample = float(decoded_data) * 5.0 / 1023.0 #convert from sensor values to voltage values
        except ValueError:
            continue

        raw_buffer.append(sample)
        if mode == 0: #Standard mode
            display_buffer.append(sample)
            
            now = time.perf_counter()
            if (now - last_render) >= render_interval:
                last_render = now
                updateFigure(list(raw_buffer))

        elif mode == 1: #Rising edge mode
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
import serial
import threading
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
import time

running = True

port = 'COM3' 
baud_rate = 115200
sample_period = 100e-6 # in seconds (before exponent in microseconds)

voltage_bias = 2.50 # the voltage bias from the circuit

buffer_size = 2000 
raw_buffer = deque(maxlen=buffer_size) 
display_buffer = []

trigger_Val = 1.0 # the height for the rising edge trigger
trigger_Range = 0.1 # the range for the schmitt trigger
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

ax.set_ylim(-10,10) #10V is the hypothetical max voltage the device can read
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

def risingEdgeDetection(sample, state,  val = trigger_Val, range = trigger_Range) -> bool:
    '''
    uses a schmitt trigger to detech a rising edge action in the signal
    
    :param sample: sample being tested for rising edge
    :param state: the current state of the program (high/low)
    param val: the voltage value for the rising edge trigger
    param range: the voltage range for the schmitt trigger (prevents noise from causing false triggers)
    :return: returns bool that reflects the new state
    :rtype: bool
    '''
    if state == 0 and sample >= (trigger_Val + trigger_Range):
        return True, 1

    if state == 1 and sample <= (trigger_Val - trigger_Range):
        return False, 0

    return False, state

def switchMode():
    '''
    Analyses user input to determine whether the oscilloscope should use rising edge detection or not
    '''
    global mode, triggered_rising_edge, period_sample_count, running, trigger_Val, trigger_Range, waves_displayed
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

        elif user_input.startswith('t '): #set trigger value
            try:
                trigger_Val = float(user_input.split()[1])
                print(f"Trigger value set to {trigger_Val}V")
            except ValueError:
                print("Invalid trigger value. Please enter a valid number.")

        elif user_input.startswith('r '): #set trigger range
            try:
                trigger_Range = float(user_input.split()[1])
                print(f"Trigger range set to {trigger_Range}V")
            except ValueError:
                print("Invalid trigger value. Please enter a valid number.")
        elif user_input.startswith('w '): #set number of waves to display
            try:
                waves_displayed = int(user_input.split()[1])
                print(f"Number of waves to display set to {waves_displayed}")
            except ValueError:
                print("Invalid number of waves. Please enter a valid integer.")

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
            sample = ((float(decoded_data) * 5.0 / 1023.0) - voltage_bias) * 45.4545; #convert from sensor values to voltage values
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
import serial
import matplotlib.pyplot as plt
from collections import deque
import time

port = 'COM3' #REPLACE WITH RELEVANT PORT
baud_rate = 115200

buffer_size = 5000 #0.5s of data at 10kHz
raw_buffer = deque(maxlen=buffer_size) 
display_buffer = []

triggered_rising_edge = 0
period_sample_count = 0

render_interval = 0.05 #seconds (20 fps)
last_render = time.perf_counter()

waves_displayed = 3
period = None

x = list(range(buffer_size))
fig, ax = plt.subplots()
(line,) = ax.plot(x, [0]*buffer_size, color="blue")

ax.set_xlim(0,5000) 
ax.set_ylim(0,10) #10V is the hypothetical max voltage the device can read

plt.ion()

def updateFigure(data):
    '''
    Updates the figure used for visualizing voltage
    
    param data: a list or deque containing all the data to be displayed
    '''
    y = list(data)

    if  len(y) < buffer_size:
        y = [0] * (buffer_size - len(y)) + y

    line.set_ydata(y)
    fig.canvas.draw_idle()
    fig.canvas.flush_events()

def risingEdgeDetection(data, threshold = 2) -> bool:
    '''
    detects a threshold crossing rising edge
    
    :param data: a list or deque containing all the data
    :param threshold: the voltage threshold to see if crossed
    :return: returns bool depending on if the last point in data is a rising edge
    :rtype: bool
    '''
    if len(data) < 2:
        return False

    return data[-2] < threshold and data[-1] >= threshold #return if data has crossed from below to above the threshold

try:
    #connect to serial port
    print(f"Attempting to establish connection to {port} at {baud_rate}.")
    ser = serial.Serial(port, baud_rate)
    time.sleep(2) #time for connection to properly establish
    print(f"Connection established successfully.")

    while True:
        #read new data
        raw_data = ser.readline()
        decoded_data = raw_data.decode("utf-8").strip()

        try:
            sample = 2.0 * float(decoded_data) * 5.0 / 1023.0
        except ValueError:
            continue

        raw_buffer.append(sample)

        #detect rising edge
        if risingEdgeDetection(raw_buffer):
            if triggered_rising_edge == 0:
                #first edge: arm capture
                triggered_rising_edge = 1
                period_sample_count = 0
                display_buffer.clear()
            else: # if not the first edge, must be second edge -> measure period
                period = period_sample_count
                period_sample_count = 0
                triggered_rising_edge += 1

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
        plt.close(fig)
        print("Serial port closed")
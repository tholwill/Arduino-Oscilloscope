import serial
import matplotlib.pyplot as plt
from collections import deque
import time

port = 'COM3' #REPLACE WITH RELEVANT PORT
baud_rate = 115200

buffer_size = 5000 #0.5s of data at 10kHz
raw_buffer = deque(maxlen=buffer_size) 

render_interval = 0.02 #seconds (50 fps)
last_render = time.perf_counter()

x = list(range(buffer_size))
fig, ax = plt.subplots()
(line,) = ax.plot(x, [0]*buffer_size, color="blue")

ax.set_xlim(0,5000) 
ax.set_ylim(0,10) #10V is the hypothetical max voltage the device can read

plt.ion()

def updateFigure(data) -> None:
    y = list(data)

    if  len(y) < buffer_size:
        y = [0] * (buffer_size - len(y)) + y

    line.set_ydata(data)
    fig.canvas.draw_idle()
    fig.canvas.flush_events()

def risingEdgeDetection(data, threshold = 2) -> bool:
    if len(data) < 2:
        return False

    return data[-1] > threshold and data[-2] <= data[-1] #return if data has crossed from below to above the threshold

try:
    #connect to serial port
    print(f"Attempting to establish connection to {port} at {baud_rate}.")
    ser = serial.Serial(port, baud_rate)
    time.sleep(2) #time for connection to properly establish
    print(f"Connection established successfully.")

    while True:
        #read new data
        rawData = ser.readline()
        decodedData = rawData.decode("utf-8").strip()

        raw_buffer.append(float(decodedData))

        #update figure
        now = time.perf_counter()
        if (now - last_render) >= render_interval:
            last_render = now
            updateFigure(raw_buffer)

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
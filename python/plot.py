import serial
import matplotlib.pyplot as plt
from collections import deque

ser = serial.Serial('COM3', 115200)
buffer = deque(maxlen=500)

print(matplotlib.__version__)
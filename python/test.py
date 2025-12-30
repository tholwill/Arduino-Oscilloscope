import matplotlib.pyplot as plt
import numpy as np

# 1. Prepare sample data
x = np.linspace(0, 10, 100)
y = np.sin(x)

# 2. Create a figure and an axes
fig, ax = plt.subplots()

# 3. Plot the data
line, = ax.plot(x, y, label='sin function', color='blue')

# 4. Add labels and a title
ax.set_xlabel('X axis label')
ax.set_ylabel('Y axis label')
ax.set_title('Simple Plot Example')
ax.legend() # Add a legend

# 5. Display the plot
plt.show()

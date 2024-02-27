import numpy as np
import matplotlib.pyplot as plt
import os

class LatticeSystem:
    def __init__(self, size):
        self.size = size
        self.system = np.ones((size, size), dtype=bool)  # Initialize all nodes as operational
        self.failure_times = np.zeros((size, size))       # Initialize failure times as 0

    def simulate(self, total_time):
        time = 0
        while time < total_time:
            # Generate number of nodes to fail
            num_failures = np.random.randint(1, self.size*self.size+1)

            # Generate failure locations and times
            for _ in range(num_failures):
                row = np.random.randint(self.size)
                col = np.random.randint(self.size)

                # Generate time to failure for the selected location
                failure_time = np.random.exponential(scale=0.5)

                # Update failure time and mark node as failed
                self.failure_times[row, col] = failure_time
                self.system[row, col] = False

            # Save the current state of the system as an image
            self.save_image(time)

            # Check if there are any non-zero failure times
            if np.any(self.failure_times > 0):
                # Advance time to next event
                time += np.min(self.failure_times[self.failure_times > 0])

                # Repair failed nodes
                for i in range(self.size):
                    for j in range(self.size):
                        if self.system[i, j] == False:
                            repair_time = np.random.exponential(scale=1.5)
                            if repair_time < total_time - time:
                                self.system[i, j] = True
                                self.failure_times[i, j] = 0

                # Save the current state of the system after repair as an image
                self.save_image(time)
            else:
                # If there are no failures, break out of the loop
                break

    def save_image(self, time):
        plt.figure()
        plt.imshow(self.system, cmap='binary', interpolation='nearest')
        plt.title(f'Time: {time:.2f}')
        plt.xlabel('Column')
        plt.ylabel('Row')
        plt.grid(False)
        plt.savefig(os.path.join("system_states", f"system_state_{time:.2f}.png"))
        plt.close()

# Simulation parameters
total_time = 15

# Create a 4x4 lattice system
#system = LatticeSystem(size=4)
system = LatticeSystem(size=4)

# Run simulation
system.simulate(total_time)
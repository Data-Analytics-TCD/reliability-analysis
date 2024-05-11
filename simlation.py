import numpy as np
import csv
import time
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

class Node:
    def __init__(self, x, y, fr, rr) -> None:
        self.x = x
        self.y = y
        self.timeline = {}
        self.fails = []
        self.repairs = []
        self.fr = fr
        self.rr = rr

    def generate_timeline(self, sim_time):
        self.timeline = {}
        self.fails = []
        self.repairs = []

        working = True
        time_accrued = 0
        while time_accrued < sim_time:
            time_accrued += self.fail() if working else self.repair()
            correct_list = self.fails if working else self.repairs
            correct_list.append(time_accrued)
            working = not working
            self.timeline[time_accrued] = working

    def fail(self):
        return np.random.exponential(1/self.fr)

    def repair(self):
        return np.random.exponential(1/self.rr)

class Submatrix:
    def __init__(self, nodes) -> None:
        self.nodes = nodes
        self.timeline = {}
        self.first_fail = -1
        self.first_repair = -1
        self.fails = []
        self.repairs = []

    def process_node_timelines(self):
        self.timeline = {}
        self.first_fail = -1
        self.first_repair = -1
        self.fails = []
        self.repairs = []
        events = defaultdict(int)
        for node in self.nodes:
            for fail in node.fails:
                events[fail] -= 1
            for repair in node.repairs:
                events[repair] += 1
        sorted_events = sorted(events.items())
        last_state = True
        working_nodes = len(self.nodes)
        for ts, event in sorted_events:
            working_nodes += event
            working = working_nodes > 0
            if working != last_state:
                last_state = working
                self.timeline[ts] = working
                correct_list = self.repairs if working else self.fails
                correct_list.append(ts)
                if not working and self.first_fail == -1:
                    self.first_fail = ts
                if working and self.first_repair == -1:
                    self.first_repair = ts

    def get_uptime_avg(self):
        if not self.repairs:
            return 0
        total_uptime = 0
        previous_time = 0
        for time in sorted(self.timeline.keys()):
            if self.timeline[time]:
                total_uptime += time - previous_time
            previous_time = time
        return total_uptime / (len(self.repairs) + 1)

    def get_downtime_avg(self):
        if not self.fails:
            return 0
        total_downtime = 0
        previous_time = 0
        for time in sorted(self.timeline.keys()):
            if not self.timeline[time]:
                total_downtime += time - previous_time
            previous_time = time
        return total_downtime / len(self.fails)

class LatticeSystem:
    def __init__(self, m, n, r, s, fail_rate, repair_rate):
        self.m = m
        self.n = n
        self.r = r
        self.s = s
        self.fail_rate = fail_rate
        self.repair_rate = repair_rate

    def simulate(self, sim_time, iterations):
        nodes = [Node(x, y, self.fail_rate, self.repair_rate) for x in range(self.m) for y in range(self.n)]
        matrix = [nodes[i * self.n:(i + 1) * self.n] for i in range(self.m)]
        submatrices = [Submatrix([node for row in matrix[start_row:start_row + self.r] 
                                  for node in row[start_col:start_col + self.s]])
                       for start_row in range(self.m - self.r + 1)
                       for start_col in range(self.n - self.s + 1)]

        results = {}
        for i in range(iterations):
            start_time = time.time()  # Capture start time of the iteration
            results[i] = {}
            for node in nodes:
                node.generate_timeline(sim_time)

            with ThreadPoolExecutor() as executor:
                # Execute the processing in parallel
                list(executor.map(lambda sm: sm.process_node_timelines(), submatrices))

            # Initialize variables to store the lowest first fail and first repair times
            lowest_first_fail = float('inf')
            lowest_first_repair = float('inf')

            # Calculate the lowest first fail and first repair times
            for sm in submatrices:
                if sm.first_fail != -1:  # Check if a fail time was recorded
                    lowest_first_fail = min(lowest_first_fail, sm.first_fail)
                if sm.first_repair != -1:  # Check if a repair time was recorded
                    lowest_first_repair = min(lowest_first_repair, sm.first_repair)

            end_time = time.time()  # End timing the iteration
            elapsed_time = end_time - start_time  # Calculate elapsed time

            # Store results in the dictionary
            results[i]['mttf'] = np.mean([round(sm.get_uptime_avg(), 3) for sm in submatrices])
            results[i]['mttr'] = np.mean([round(sm.get_downtime_avg(), 3) for sm in submatrices])
            results[i]['ff'] = (round(lowest_first_fail, 3) if lowest_first_fail != float('inf') else 'No Failure')
            results[i]['fr'] = (round(lowest_first_repair, 3) if lowest_first_repair != float('inf') else 'No Repair')
            results[i]['et'] = (round(elapsed_time, 3))

        for result in results.items():
            print(result)
        return results

if __name__ == '__main__':
    # Simulation parameters
    sim_times = [10, 100]
    mns = [(3, 3), (10, 10), (50, 50), (100, 100)]
    rss = [(2, 2), (3, 3), (5, 5), (10, 10)]
    frs = [(10, 10), (10, 5), (10, 2.5), (10, 1)]
    with open('simulation_results.csv', 'w', newline='') as file:
        fieldnames = ['sim_time', '(m,n)', '(r,s)', 'fail_rate', 'repair_rate', 'iteration', 'mttf', 'mttr', 'ff', 'fr', 'elapsed_time']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for sim_time in sim_times:
            for mn in mns:
                m, n = mn
                for rs in rss:
                    r, s = rs
                    for fr in frs:
                        fr, rr = fr
                        print("**********************************")
                        print(f"sim_time: {sim_time}, m: {m}, n: {n}, r: {r}, s: {s}, fr: {fr}, rr: {rr}")
                        config_key = (sim_time, m, n, r, s, fr, rr)
                        system = LatticeSystem(m, n, r, s, fr, rr)
                        results = system.simulate(sim_time, 10)
                        for iteration, result in results.items():
                            row = {
                                'sim_time': sim_time,
                                '(m,n)': (m,n),
                                '(r,s)': (r,s),
                                'fail_rate': fr,
                                'repair_rate': rr,
                                'iteration': iteration,
                                'mttf': result['mttf'],
                                'mttr': result['mttr'],
                                'ff': result['ff'],
                                'fr': result['fr'],
                                'elapsed_time': result['et']
                            }
                            writer.writerow(row)
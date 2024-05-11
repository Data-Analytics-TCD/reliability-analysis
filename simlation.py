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
            time_accrued += np.random.exponential(1 / (self.fr if working else self.rr))
            if time_accrued < sim_time:
                correct_list = self.fails if working else self.repairs
                correct_list.append(time_accrued)
                working = not working
                self.timeline[time_accrued] = working

class Submatrix:
    def __init__(self, nodes) -> None:
        self.nodes = nodes
        self.timeline = {}
        self.first_fail = -1
        self.first_repair = -1
        self.fails = []
        self.repairs = []
        self.total_uptime = 0
        self.total_downtime = 0

    def process_node_timelines(self, sim_time):
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
        working = True
        previous_ts = 0
        for ts, event in sorted_events:
            working_nodes += event
            working = working_nodes > 0
            if working != last_state:
                last_state = working
                previous_ts = ts
                self.timeline[ts] = working
                if not working:
                    self.fails.append(ts)
                    self.total_uptime += ts - previous_ts
                    if self.first_fail == -1:
                        self.first_fail = ts
                else:
                    self.repairs.append(ts)
                    self.total_downtime += ts - previous_ts
                    if self.first_repair == -1:
                        self.first_repair = ts
        if working:
            self.total_uptime += sim_time - previous_ts
        else:
            self.total_downtime += sim_time - previous_ts

    def get_uptime_avg(self):
        return (self.total_uptime / (len(self.repairs))) if self.repairs else self.total_uptime

    def get_downtime_avg(self):
        return (self.total_downtime / len(self.fails)) if self.fails else self.total_downtime

class LatticeSystem:
    def __init__(self, m, n, r, s, fail_rate, repair_rate):
        self.m = m
        self.n = n
        self.r = r
        self.s = s
        self.fail_rate = fail_rate
        self.repair_rate = repair_rate
        self.timeline = {}
        self.total_uptime = 0
        self.total_downtime = 0
        self.fails = 0
        self.repairs = 0
        self.first_fail = -1
        self.first_repair = -1

    def process_sm_timelines(self, submatrices, sim_time):
        self.timeline = {}
        self.total_uptime = 0
        self.total_downtime = 0
        self.fails = 0
        self.repairs = 0
        self.first_fail = -1
        self.first_repair = -1
        events = defaultdict(int)
        for sm in submatrices:
            for fail in sm.fails:
                events[fail] += 1
            for repair in sm.repairs:
                events[repair] -= 1
        sorted_events = sorted(events.items())
        last_state = True
        broken_sm = 0
        previous_ts = 0
        working = True
        for ts, broken in sorted_events:
            broken_sm += broken
            working = broken_sm == 0
            if working != last_state:
                last_state = working
                self.timeline[ts] = working
                if not working:
                    self.fails += 1
                    self.total_uptime += ts - previous_ts
                    if self.first_fail == -1:
                        self.first_fail = ts
                else:
                    self.repairs += 1
                    self.total_downtime += ts - previous_ts
                    if self.first_repair == -1:
                        self.first_repair = ts
                previous_ts = ts
        if working:
            self.total_uptime += sim_time - previous_ts
        else:
            self.total_downtime += sim_time - previous_ts
        print("Uptime:", self.total_uptime, "Downtime:", self.total_downtime)
    
    def get_uptime_avg(self):
        return (self.total_uptime / self.repairs) if self.repairs else self.total_uptime

    def get_downtime_avg(self):
        return (self.total_downtime / self.fails) if self.fails else self.total_downtime
        

    def simulate(self, sim_time, iterations):
        nodes = [Node(x, y, self.fail_rate, self.repair_rate) for x in range(self.m) for y in range(self.n)]
        matrix = [nodes[i * self.n:(i + 1) * self.n] for i in range(self.m)]
        submatrices = [Submatrix([node for row in matrix[start_row:start_row + self.r] 
                                  for node in row[start_col:start_col + self.s]])
                       for start_row in range(self.m - self.r + 1)
                       for start_col in range(self.n - self.s + 1)]

        results = {}
        with ThreadPoolExecutor() as executor:
            for i in range(iterations):
                start_time = time.time()  # Capture start time of the iteration
                results[i] = {}
                # Generate timelines for all nodes; waits for completion here
                list(executor.map(lambda node: node.generate_timeline(sim_time), nodes))
                # Process node timelines in all submatrices; waits for completion here
                list(executor.map(lambda sm: sm.process_node_timelines(sim_time), submatrices))

                self.process_sm_timelines(submatrices, sim_time)

                end_time = time.time()  # End timing the iteration
                elapsed_time = end_time - start_time  # Calculate elapsed time

                # Store results in the dictionary
                results[i]['mttf'] = self.get_uptime_avg()
                results[i]['mttr'] = self.get_downtime_avg()
                results[i]['ff'] = (self.first_fail if self.first_fail != -1 else 'No Failure')
                results[i]['fr'] = (self.first_repair if self.first_repair != -1 else 'No Repair')
                results[i]['sm_mttf'] = np.mean([sm.get_uptime_avg() for sm in submatrices])
                results[i]['sm_mttr'] = np.mean([sm.get_downtime_avg() for sm in submatrices])
                results[i]['fails'] = self.fails
                results[i]['repairs'] = self.repairs
                results[i]['et'] = (round(elapsed_time, 3))

        for result in results.items():
            print(result)
        return results

if __name__ == '__main__':
    # Simulation parameters
    mns = [(3,3), (5,5), (10, 10), (25,25), (30,30), (50, 50) ]
    rss = [(2,2), (3,3), (5, 5), (8, 8), (10, 10)]
    frs = [(10, 10), (10, 7.5), (10, 5), (10, 2.5)]
    sim_times = [50, 75, 100]
    with open('final_simulation_results.csv', 'w', newline='') as file:
        fieldnames = ['sim_time', '(m,n)', '(r,s)', 'fail_rate', 'repair_rate', 'iteration', 'mttf', 'mttr', 'ff', 'fr', 'sm_mttf', 'sm_mttr', 'fails', 'repairs', 'elapsed_time']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for mn in mns:
            m, n = mn
            for rs in rss:
                r, s = rs
                for fr in frs:
                    fr, rr = fr
                    for sim_time in sim_times:
                        if not (sim_time > 50 and m > 25):
                            print("**********************************")
                            print(f"sim_time: {sim_time}, m: {m}, n: {n}, r: {r}, s: {s}, fr: {fr}, rr: {rr}")
                            config_key = (sim_time, m, n, r, s, fr, rr)
                            system = LatticeSystem(m, n, r, s, fr, rr)
                            results = system.simulate(sim_time, 5)
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
                                    'sm_mttf': result['sm_mttf'],
                                    'sm_mttr': result['sm_mttr'],
                                    'fails': result['fails'],
                                    'repairs': result['repairs'],
                                    'elapsed_time': result['et']
                                }
                                writer.writerow(row)
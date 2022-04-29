from cProfile import label
from turtle import color
import numpy as np 
import matplotlib.pyplot as plt
import sys
import os

def plot_throughput(directory):
    faults = []
    throughputs = []
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r') as f:
            lines = f.readlines()
            throughput = float(lines[-1].split(' ')[3])            
            throughputs.append(throughput)    
            faults.append(filename)
    
    plt.bar(x=faults, height = throughputs, color = ['red', 'blue', 'green', 'yellow', 'magenta'])
    plt.legend()
    plt.ylabel('Throughput (ops/s)')
    plt.xlabel('Memory Limit')
    plt.title('Throughput for Memory Contention (Follower)')
    plt.show()

if __name__ == '__main__':
    dir = sys.argv[1]
    plot_throughput(dir)
from turtle import color
import numpy as np 
import matplotlib.pyplot as plt
import sys
import os

def plot_throughput(directory):
    faults = ["No Slow"]
    throughputs = [1641.12]
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r') as f:
            lines = f.readlines()
            print(lines[-1])
            throughput = float(lines[-1].split(' ')[3])            
            throughputs.append(throughput)    
            faults.append(filename)
    
    fig = plt.figure()
    plt.bar(faults, throughputs, color = ['red', 'blue', 'green', 'yellow'])
    plt.xlabel('Faults')
    plt.ylabel('Throughput (ops/s)')
    plt.title('Follower Fault Injection')
    plt.show()

if __name__ == '__main__':
    dir = sys.argv[1]
    plot_throughput(dir)
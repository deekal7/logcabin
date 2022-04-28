import numpy as np 
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import sys

def plot_points(file):
    x = []
    y = []
    with open(file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip('\n')
            toks = line.split(' ')
            x.append(float(toks[3]))
            y.append(float(toks[1]))
    
    x = np.array(x)
    y = np.array(y)

    plt.plot(x,y)
    plt.scatter (x, y)
    plt.xlabel('Throughput (ops/s)')
    plt.ylabel('Latency (ms)')
    plt.title('Leader Memory Contention Performance')

    pt = 3
    for i in range(len(x)):
        plt.annotate(pt, (x[i], y[i]))
        pt += 2
    plt.show()

if __name__ == '__main__':
    fname = sys.argv[1]
    plot_points(fname)
import numpy as np 
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

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
    print(x)
    print(y)

    # x_new = np.linspace(x.min(), x.max(), 500)

    # f = interp1d(x, y, kind='quadratic')
    # y_smooth=f(x_new)

    plt.plot(x,y)
    # plt.scatter (x, y)
    plt.xlabel('Throughput (ops/s)')
    plt.ylabel('Latency (ms)')
    plt.show()

if __name__ == '__main__':
    plot_points('outputs/benchmark')
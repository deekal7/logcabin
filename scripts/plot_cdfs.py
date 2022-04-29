from cProfile import label
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import sys
import os


def plot_cdf(directory):
    colors = ['red', 'blue', 'green', 'yellow', 'magenta', 'cyan', 'black']
    i = 0
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r') as f:
            lines = f.readlines()
            latencies = []
            for line in lines[:-1]:
                line = line.strip('\n')
                toks = line.split(',')
                for tok in toks:
                    if tok != '':
                        latencies.append(float(tok))
            data = np.sort(np.array(latencies))
            bins=np.append(data, data[-1]+1)
            counts, bin_edges = np.histogram(latencies, bins=bins, density=False)
            counts=counts.astype(float)/len(latencies)
            cdf = np.cumsum(counts)
            plt.plot(bin_edges[0:-1], cdf, linestyle='--', marker="o", color=colors[i], label=filename+'MB')
            plt.ylim((0,1))
            i += 1

    plt.legend()
    plt.ylabel('CDF')
    plt.xlabel('Latency (ms)')
    plt.title('Leader Latency vs CDF Different Mem Contention')
    plt.show()


if __name__ == '__main__':
    dir = sys.argv[1]
    plot_cdf(dir)

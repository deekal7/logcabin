from matplotlib import pyplot as plt
import sys
import numpy as np

bar_width = 0.1
index = np.arange(2)

slow_tp_1_data = [1148.77, 1123.1]
slow_tp_2_data = [1193.47, 1108.83]
slow_tp_5_data = [1266.6, 1273.28]
slow_tp_75_data = [1267.52, 1361.66]

# slow_tp_1_data = [1597.49, 1589.77]
# slow_tp_2_data = [1561.39, 1592.22]
# slow_tp_5_data = [1583.92, 1600.73]
# slow_tp_75_data = [1596.7, 1604.13]

# fig = plt.figure()
# ax = fig.add_axes([0,1])

plt.figure(figsize=(7,5))
slow_1 = plt.bar(index, slow_tp_1_data, 
                width=bar_width, label="1%", color='orange')

slow_2 = plt.bar(index + bar_width, slow_tp_2_data,
                width=bar_width, label="2%", color='lightblue')

slow_5 = plt.bar(index + 2*bar_width, slow_tp_5_data,
                width=bar_width, label="5%", color='lavender')

slow_75 = plt.bar(index + 3*bar_width, slow_tp_75_data,
                width=bar_width, label="7.5%", color='lightpink')

# ax.set_ylabel('Throughput (ops/sec)')
# ax.set_xlabel('Node Type')
# ax.set_xticks(index + bar_width/2)
# ax.set_xticklabels(("Leader", "Follower"))
# ax.legend()

plt.xlabel('Node Type')
plt.ylabel('Throughput (ops/sec)')
plt.title(sys.argv[1])
plt.xticks(index + bar_width/2, ["Leader", "Follower"])
plt.legend()
plt.show()
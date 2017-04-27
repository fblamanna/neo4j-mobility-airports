# encoding: utf-8

"""
Perform Similarity measures with Neo4j, py2neo and pandas.
Here we compute the Hamming Distance among strings to evaluate their mutual distance.
This helps in filtering 'bot' users on a Twitter dataset

Execution:
>> python HammingDistance.py [password] [cypher query] [alias or variable to plot]

Required Packages: py2neo, pandas, itertools, matplotlib, seaborn
"""

__author__ = """ Fabio Lamanna (fabio@fabiolamanna.it) """

# Import Modules
import sys
import numpy as np
import matplotlib.pyplot as plt

try:
    import pandas as pd
except ImportError:
    raise ImportError("You need to install pandas in order to properly run the script")

try:
    import itertools
except ImportError:
    raise ImportError("You need to install itertools in order to properly run the script")

try:
    import seaborn as sns
except ImportError:
    raise ImportError("You need to install seaborn in order to properly run the script")

try:
    from py2neo import Graph
except ImportError:
    raise ImportError("You need to install py2neo in order to properly run the script")

# Hamming Distance Function
def hamming_distance(s1, s2):
	return sum(e1 != e2 for e1, e2 in zip(s1, s2))

# Hamming Function
def Hamming(passw, query, variable):

	# Call Database
	graph = Graph(password=passw)

	# Import results from query to pandas Dataframe
	df = pd.DataFrame(graph.data(query))

	# Build combinations of the first 10 digits of each string
	combs = list(itertools.combinations(df[variable].str[:30],2))

	# Apply Function
	distance = [hamming_distance(x[0], x[1]) for x in combs]

	# Plot and Save Figure
	ax = sns.boxplot(distance)
	ax.set(xlabel='Hamming Distance')
	plt.savefig('HammingDistance.png', dpi=300, tight_layout=True)
	plt.close()

if __name__ == "__main__":

    Hamming(sys.argv[1], sys.argv[2], sys.argv[3])
import numpy as np
import re
import os
import matplotlib.pyplot as plt

n = 50
fname = "doc.txt"

def plot_ndcg(dcg, idcg):
    plt.figure(figsize=(10,7)) 
    x = np.arange(1,51)
    plt.plot(x, np.divide(dcg,idcg))
    plt.xlabel("Number of documents", fontsize = 16)
    plt.ylabel("Normalized Discounted cumulative gain", fontsize = 16)
    plt.title("Top 50 NDCG", fontsize = 20)
    plt.show()

def computeDCG(rank):
    """Make sure the arrays are sorted by the same index beforehand"""
    m = len(rank)
    res = np.zeros(m)
    res[0] = rank[0]
    for i in range(1,m):
        res[i] = res[i-1] + rank[i] / np.log2(i+1+1)
        
    return res


def read_file(fname):
    with open(fname, "r") as f:
        i = 0
        rank = np.zeros(n)
        while i <30 :
             line = f.readline().rstrip()
             tmp = line.split(" ")
             rank[i] = tmp[1]
             i+=1
       
        rank_sorted = sorted(rank)[::-1]
    return rank, rank_sorted
    


rank, rank_sorted = read_file(fname)
dcg = computeDCG(rank)
idcg = computeDCG(rank_sorted)

plot_ndcg(dcg, idcg)


    
    



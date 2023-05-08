import numpy as np
import re
import os
import matplotlib.pyplot as plt


n  = 50

def read_file(filename):
    with open(filename, "r") as f:
        i = 0
        relevance = np.zeros(n)
        while (line := f.readline().rstrip()):
                tmp = line.split(" ")
                relevance[i] = int(tmp[2])
                i+=1
            
    return relevance
    

def recall(L):
    tp = 0
    rec = np.zeros(len(L))
    for i in range(len(L)):
        tp += 1 if L[i] >0 else 0
        rec[i] = tp / 100
        
    return rec
    

def precision(L):
    tp = 0
    prec = np.zeros(len(L))
    for i in range(len(L)):
        tp += L[i]
        prec[i] = tp / (i+1)
        
    return prec
   

def plot_precision_recall(prec, rec, smooth = False):
    plt.figure(figsize=(10,7))   
    rec = list(rec)
    prec = list(prec)
    if smooth :
        i = 1
        while i < len(rec):
            while rec[i] == rec[i-1] : 
                prec.pop(i)
                rec.pop(i)
                if i == len(rec) : break
            i+=1
         
    plt.plot(rec, prec)
    plt.xlabel("Recall", fontsize = 16)
    plt.ylabel("Precision", fontsize = 16)
    
    if smooth :plt.title("Precision-recall graph smoothed", fontsize = 20)    
    else : plt.title("Precision-recall graph", fontsize = 20)
    plt.show()
    



relevance = read_file("doc.txt")
prec = precision(relevance)
rec = recall(relevance)
plot_precision_recall(prec, rec )
plot_precision_recall(prec, rec, smooth = True)
    

for i in range(1,6):
    print(rec[i*10-1])
    
 
for i in range(1,6):
    print(prec[i*10-1])


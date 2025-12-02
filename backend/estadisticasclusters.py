import numpy as np
from sklearn.cluster import MiniBatchKMeans
import time
import joblib
import os

models_dir="data/fashion/models"
kmeans = joblib.load(os.path.join(models_dir, "codebook.pkl"))
labels = kmeans.labels_ 

K = kmeans.n_clusters
counts = np.bincount(labels, minlength=K)
empty = np.sum(counts == 0)
print(f"K = {K}  → clusters vacíos: {empty} / {K}")
print("stats counts -> min, median, mean, max:", counts.min(), np.median(counts), counts.mean(), counts.max())

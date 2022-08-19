def compute_stats(arr):
    return dict(median=np.median(arr)*100, mean=np.mean(arr)*100, std=np.std(arr)*100, min=np.min(arr)*100, max=np.max(arr)*100)
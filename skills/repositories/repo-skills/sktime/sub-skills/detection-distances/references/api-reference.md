# Detection and Distance API Reference

Verified signatures:

- `ThresholdDetector(upper=1, lower='-upper', mode='segments')`.
- `ScipyDist(metric='euclidean', p=2, colalign='intersect', var_weights=None, metric_kwargs=None)`.

Detection tasks include point anomalies, segment anomalies, changepoints, and
segmentation. Detector outputs are often sparse pandas DataFrames with ilocs or
intervals; always inspect the output type and columns before interpreting.

Pairwise transformers output square or rectangular matrices. Distances usually
have zero diagonals when comparing an object with itself; kernels need not.
Optional DTW backends may require `dtw-python`, `dtaidistance`, `tslearn`, or
numba-dependent packages.

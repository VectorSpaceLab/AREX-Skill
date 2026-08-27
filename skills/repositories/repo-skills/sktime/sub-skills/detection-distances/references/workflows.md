# Detection and Distance Workflows

## Threshold anomaly smoke

```python
import pandas as pd
from sktime.detection.naive import ThresholdDetector

y = pd.Series([0.0, 1.0, 5.0, 6.0, 1.0, 0.0])
detector = ThresholdDetector(upper=4.0, mode="segments")
segments = detector.fit(y).predict(y)
```

For `mode="segments"`, intervals describe contiguous anomalous regions. For
`mode="points"`, map returned ilocs back to the original time index before
reporting them.

## Pairwise distance smoke

```python
import numpy as np
from sktime.dists_kernels.scipy_dist import ScipyDist

X = np.array([[0.0, 0.0], [3.0, 4.0]])
D = ScipyDist(metric="euclidean").transform(X)
assert D.shape == (2, 2)
```

If DTW optional dependencies are absent, use simple base distances as a fallback
and state that they are not phase-invariant DTW substitutes.

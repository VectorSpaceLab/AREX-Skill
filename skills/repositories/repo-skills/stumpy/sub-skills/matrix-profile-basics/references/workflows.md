# Workflows

These workflows assume the user wants 1-D matrix profiles or distance profiles. If the task turns into motifs, matches, discords, segmentation, multidimensional profile selection, streaming, or acceleration setup, route away before adding more detail.

## 1. Install/import smoke handoff

Use the bundled smoke script first.

```bash
python scripts/profile_smoke.py --help
python scripts/profile_smoke.py --mode exact
```

Expected signals:

- `stumpy` and `numpy` import successfully.
- The smoke prints the installed STUMPY distribution version.
- The smoke prints the profile shape and a finite-distance check.
- No files are read or written.

## 2. Exact normalized self-join

Use this when you want the default 1-D matrix profile.

```python
import numpy as np
import stumpy

T = np.array([0.0, 2.0, -1.0, 3.0, 1.0, 5.0, -2.0, 4.0], dtype=np.float64)
m = 3

mp = stumpy.stump(T, m=m)
print(mp.shape)
print(mp.P_)
print(mp.I_)
print(mp.left_I_)
print(mp.right_I_)
```

Notes:

- `mp` is an object-dtype `mparray`.
- For `k = 1`, each row is `[P, I, left_I, right_I]`.
- `left_I_` and `right_I_` are only meaningful for self-joins.
- Use the lowest value in `mp.P_` to locate the strongest motif-like repeat.

## 3. Exact AB-join

Use this when annotating one time series with nearest neighbors from another.

```python
import numpy as np
import stumpy

T_A = np.array([0.0, 2.0, -1.0, 3.0, 1.0, 5.0, -2.0, 4.0], dtype=np.float64)
T_B = np.array([1.0, -1.0, 2.0, 0.5, 3.5, -0.5, 4.5, 1.5], dtype=np.float64)

mp = stumpy.stump(T_A, m=3, T_B=T_B, ignore_trivial=False)
print(mp.shape)
print(mp.P_)
print(mp.I_)
```

Notes:

- AB-joins are not symmetric.
- `left_I_` and `right_I_` are sentinel `-1` values for AB-joins.
- Keep the same window size for both series.

## 4. Raw-distance matrix profile

Use `aamp` when amplitude matters or you need a non-normalized comparison.

```python
import numpy as np
import stumpy

T = np.array([0.0, 2.0, -1.0, 3.0, 1.0, 5.0, -2.0, 4.0], dtype=np.float64)
mp = stumpy.aamp(T, m=3, p=2.0)
print(mp.P_)
print(mp.I_)
```

You can also route through the high-level API with `normalize=False` when you intentionally want the same raw-distance family:

```python
mp = stumpy.stump(T, m=3, normalize=False, p=2.0)
```

## 5. Distance-profile workflow

Use `mass` when you have one query subsequence and want a distance profile against a longer series.

```python
import numpy as np
import stumpy

T = np.array([0.0, 2.0, -1.0, 3.0, 1.0, 5.0, -2.0, 4.0], dtype=np.float64)
Q = T[:3].copy()

D = stumpy.mass(Q, T, query_idx=0)
print(D.shape)
print(D)
```

Notes:

- `mass` returns a `float64` distance profile, not an `mparray`.
- If the query is not a subsequence of `T`, omit `query_idx`.
- Use `normalize=False` only when you explicitly want raw Minkowski distances.

## 6. Top-k interpretation

Use `k > 1` when you want more than the nearest neighbor.

```python
import numpy as np
import stumpy

T = np.array([0.0, 2.0, -1.0, 3.0, 1.0, 5.0, -2.0, 4.0], dtype=np.float64)
mp = stumpy.stump(T, m=3, k=2)
print(mp.shape)
print(mp.P_.shape)
print(mp.I_.shape)
print(mp.left_I_.shape)
print(mp.right_I_.shape)
```

Notes:

- `P_` and `I_` become 2-D top-k arrays.
- `left_I_` and `right_I_` stay top-1 arrays.
- The row layout expands to `[P_1, ..., P_k, I_1, ..., I_k, left_I, right_I]`.

## 7. pandas and polars inputs

Use Series inputs when you want 1-D data with a dataframe-like source.

```python
import pandas as pd
import polars as pl
import stumpy

values = [0.0, 2.0, -1.0, 3.0, 1.0, 5.0, -2.0, 4.0]

mp_pd = stumpy.stump(pd.Series(values), m=3)
mp_pl = stumpy.aamp(pl.Series(values), m=3)
```

Notes:

- Series inputs are converted to NumPy and work with the 1-D APIs.
- DataFrames are transposed before conversion, so they are a better fit for multidimensional workflows than for this basic 1-D skill.

## 8. Route-out cues

After computing a valid 1-D profile, switch sub-skills if the next question is about motifs, matches, discords, snippets, segmentation, streaming updates, pan profiles, or acceleration backends.

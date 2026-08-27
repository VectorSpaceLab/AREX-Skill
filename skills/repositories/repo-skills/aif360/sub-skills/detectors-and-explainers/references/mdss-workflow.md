# MDSS Bias-Scan Workflow

## When to read

Read this when the task asks for a subgroup scan, anomalous bias subset, MDSS
score, or a comparison between observed outcomes and model expectations.

## Verified signatures

Legacy detector:

```text
aif360.detectors.bias_scan(data, observations, expectations=None,
                           favorable_value=None, overpredicted=True,
                           scoring='Bernoulli', num_iters=10,
                           penalty=1e-17, mode='binary', **kwargs)
```

sklearn detector:

```text
aif360.sklearn.detectors.bias_scan(X, y_true, y_pred=None,
                                   pos_label=None, overpredicted=True,
                                   scoring='Bernoulli', num_iters=10,
                                   penalty=1e-17, mode='binary', **kwargs)
```

`MDSS_bias_scan` is the sklearn function's canonical name; `bias_scan` is a
backward-compatible alias.

## Inputs

| Input | Meaning |
| --- | --- |
| `data` / `X` | pandas DataFrame with candidate subgroup features. Keep columns categorical or discretized when possible. |
| `observations` / `y_true` | Ground-truth or observed target values. |
| `expectations` / `y_pred` | Model expectations, probabilities, scores, or predictions depending `mode`. |
| `favorable_value` / `pos_label` | Which label is favorable/positive in binary tasks. |
| `overpredicted` | Whether to search for a subgroup where expectations are too high versus too low. |
| `scoring` | Scoring function name or scoring object, commonly `Bernoulli`; source also includes Gaussian, Poisson, and BerkJones scoring implementations. |
| `mode` | Bias-scan mode such as `binary`, `continuous`, `nominal`, or `ordinal`, matching the outcome/expectation type. |

## Basic sklearn-style scan

```python
import pandas as pd
from aif360.sklearn.detectors import bias_scan

X = pd.DataFrame({"region": ["north", "south", "south"], "channel": ["web", "web", "store"]})
y_true = pd.Series([1, 1, 0])
y_score = pd.Series([0.8, 0.2, 0.5])
subset, score = bias_scan(
    X,
    y_true,
    y_score,
    pos_label=1,
    overpredicted=False,
    scoring="Bernoulli",
    mode="binary",
)
```

The returned subset is a dictionary from feature names to selected values. The
score is a numeric anomalous-subgroup score; higher values indicate a stronger
scan signal under the selected scoring model.

## Operating guidance

- Use features that make sense as subgroup descriptors. Continuous columns may
  need binning before scan interpretation.
- Keep indexes aligned between `X`, observations, and expectations.
- For probability expectations, verify they are in the range expected by the
  scoring function.
- Use `num_iters` as a search-depth/speed trade-off; increasing it can improve
  search but costs more runtime.
- Treat the returned subgroup as a hypothesis for investigation, not as proof of
  causality.

## Safe smoke

Run:

```bash
python sub-skills/detectors-and-explainers/scripts/mdss_smoke.py --json
```

It builds a tiny DataFrame and checks that the base MDSS scan path returns a
subset and numeric score.

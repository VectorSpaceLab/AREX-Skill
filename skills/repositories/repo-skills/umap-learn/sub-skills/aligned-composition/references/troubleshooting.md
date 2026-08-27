# AlignedUMAP and Composition Troubleshooting

Use this table after identifying whether the failure is in relation generation,
aligned fitting/updating, or composition. Validate data and row identity before
changing alignment hyperparameters.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Error about relation length | For `n` slices, relation list length is not `n - 1` | Provide one relation dictionary for each adjacent slice pair. |
| Index error or nonsensical alignment | Relation keys/values are stable IDs, stale row positions, or out of range for current slice shapes | Build row-index maps after all filtering/sorting; validate every key/value against the final slice lengths. |
| Slice sizes changed after relation creation | A slice was filtered, resampled, or rebuilt after the relation map was constructed | Recompute the relation dictionary against current row positions, then refit or update. |
| Alignment appears inverted or drifts after update | The relation map was built in the wrong row-index direction, or a slice changed after map creation | Build maps as `previous slice row -> new slice row`; invert an opposite-direction map before `update`. |
| Embeddings drift too much across slices | Missing relation keys, weak `alignment_regularisation`, or too small `alignment_window_size` | Check relation coverage, increase regularisation cautiously, and validate against known correspondences. |
| Real temporal changes disappear | Alignment regularisation or window is too strong | Lower regularisation or window size; compare with independent per-slice UMAP embeddings. |
| Update fails with list-valued parameters | A list was supplied where the update expects the new slice value, or list lengths do not match | Use scalar parameters for update unless the API path explicitly expects a new per-slice value. Keep `n_components` scalar. |
| `Only models with the equivalent samples can be combined` | The two fitted models do not have the same sample count or row order | Rebuild both views from the same samples in the same row order and refit before composing. |
| Composition output is meaningless | Feature views were independently sorted, filtered, or joined | Create one canonical sample-ID order, apply it to every view, then fit both models again. |
| `A - B` differs from `B - A` | Contrast operator is directional | Record operand order and interpret contrast as first view relative to second. |
| Composition takes unexpectedly long | Combining graphs triggers a new embedding optimization | Start on a small sample and lower epochs for exploration; scale after validating the operator choice. |
| `Only fitted UMAP models can be combined` | One operand has not completed `.fit(...)` | Fit both operands first and compose the fitted mapper objects, not raw arrays. |

## Relation Validation Snippet

```python
def validate_relation(rel, n_left, n_right):
    bad_keys = [k for k in rel if k < 0 or k >= n_left]
    bad_vals = [v for v in rel.values() if v < 0 or v >= n_right]
    if bad_keys or bad_vals:
        raise ValueError({"bad_keys": bad_keys, "bad_values": bad_vals})
```

Run this before `AlignedUMAP.fit` or `update` when relations are generated from
external IDs. Also check that any intended one-to-one correspondence does not
reuse a destination row for multiple source rows.

## Optional Dependencies

AlignedUMAP and the `UMAP` composition operators use the base package
dependencies; they do not require the optional plotting or TensorFlow/Keras
extras. If plotting the resulting embeddings raises an import error, route to
the plotting diagnostics sub-skill and install the documented `plot` extra only
if rendering is required.

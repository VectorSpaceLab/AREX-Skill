# Troubleshooting

Use this guide when `stumpy.stump`, `stumpy.aamp`, or `stumpy.mass` fails before the result can be interpreted.

## 1. Integer or object dtype input

Symptoms:

- `TypeError: <class 'numpy.float64'> dtype expected but found int64 in input array`
- Similar dtype complaints from `check_dtype`

Cause:

- The basic 1-D APIs expect floating-point input arrays.

Fix:

```python
T = np.asarray(T, dtype=np.float64)
```

For pandas or polars sources, cast before calling the STUMPY API.

## 2. Invalid window size

Symptoms:

- `ValueError: All window sizes must be greater than or equal to three`
- `ValueError: The window size must be less than or equal to ...`

Cause:

- `m` is too small or longer than one of the inputs.

Fix:

- Keep `m >= 3`.
- Keep `m <= len(T_A)` and `m <= len(T_B)` when both series are present.
- If the self-join warning says the window may be too large and could lead to meaningless results, reduce `m`.

## 3. Self-join versus AB-join warnings

Symptoms:

- `Arrays T_A, T_B are equal, which implies a self-join. Try setting ignore_trivial = True.`
- `Arrays T_A, T_B are not equal, which implies an AB-join. ignore_trivial has been automatically set to False.`
- `ignore_trivial cannot be False for a self-join`

Fix:

- Use `ignore_trivial=True` for self-joins.
- Use `ignore_trivial=False` for AB-joins.
- If `T_B` is omitted, the call is a self-join.
- If `T_A` and `T_B` differ, let the AB-join semantics stand.

## 4. NaN, inf, and constant subsequences

Symptoms:

- `inf` distances in the output
- Unexpected warnings or masked neighbors
- Distance profiles that do not look like ordinary Euclidean values

Cause:

- Any subsequence containing `NaN` or `inf` is treated as non-finite.
- Constant subsequences are handled specially in the normalized paths.

Fix:

- Clean or mask illegal values before calling the API when possible.
- If you know a subsequence is constant, pass `T_A_subseq_isconstant` / `T_B_subseq_isconstant` / `Q_subseq_isconstant` to the exact API.
- Treat `inf` as a validity signal, not automatically as an algorithm failure.

## 5. Object-dtype matrix-profile arrays

Symptoms:

- `mp.dtype` is `object`
- Casting the whole result feels awkward
- Index columns look like mixed types

Cause:

- `stump` and `aamp` intentionally return `mparray` objects with mixed distance/index columns.

Fix:

- Read `mp.P_`, `mp.I_`, `mp.left_I_`, and `mp.right_I_` instead of assuming a plain float array.
- For `k > 1`, remember that `P_` and `I_` become 2-D top-k arrays.
- For AB-joins, expect left/right indices to be `-1`.

## 6. Normalize and p-norm confusion

Symptoms:

- `p` appears to have no effect
- Raw distances do not match normalized ones
- The same call behaves differently under another flag

Cause:

- `p` is ignored when the normalized path is active.

Fix:

- Use `aamp` or `mass(..., normalize=False, p=...)` when you want raw Minkowski distances.
- Use `stump(..., normalize=True)` or `mass(..., normalize=True)` when you want z-normalized distances.
- Keep `p` at the default `2.0` unless you explicitly want another Minkowski norm.

## 7. pandas/polars shape confusion

Symptoms:

- A one-column DataFrame behaves like a 2-D input
- A 1-D call raises a dimension error even though the original data looked simple

Cause:

- DataFrames are transposed before conversion, while Series are the safer 1-D input shape.

Fix:

- Use `pd.Series(...)` or `pl.Series(...)` for 1-D matrix-profile work.
- Reserve DataFrames for multidimensional workflows.

## 8. `mass` query alignment warnings

Symptoms:

- A warning says the query subsequence and the slice from `T` differ

Cause:

- `query_idx` does not match the actual position of `Q` in `T`.

Fix:

- Re-check the slice used for `Q`.
- Remove `query_idx` if `Q` is not a known subsequence of `T`.

## 9. When to route elsewhere

If the input is healthy but the request is really about motifs, matches, discords, snippets, segmentation, approximate/streaming/pan analysis, multidimensional profiles, or acceleration backends, stop troubleshooting here and route to the owner sub-skill.

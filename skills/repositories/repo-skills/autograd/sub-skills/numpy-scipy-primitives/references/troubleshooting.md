# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError` for `autograd.scipy` or `scipy.*` | SciPy is not installed in the current environment. | Install the optional dependency with `pip install "autograd[scipy]"` or install `scipy` directly. |
| `ImportError` for `xarray` | xarray is optional and not part of the base Autograd install. | Install `xarray` or skip the container-interoperability examples. |
| `A.dot(B)` or `x.dot(y)` fails or does not trace | The method form is not part of the supported wrapper contract. | Rewrite to `np.dot(A, B)` or `np.matmul(A, B)`. |
| In-place mutation changes the forward pass unexpectedly | The array is being mutated while Autograd still needs the old value for the reverse pass. | Rewrite the code as a pure expression; avoid `A[i] = x` and `A += B` on differentiable values. |
| `np.sum([x, y])`, `np.mean([x, y])`, or similar list inputs misbehave | A primitive saw a Python list and could not safely inspect the hidden boxed values. | Wrap the values with `np.array([x, y])` first, or use the Autograd builtins container helpers. |
| `isinstance(x, np.ndarray)` or `isinstance(x, tuple)` gives a surprising result | Boxed values are not plain `ndarray` subclasses. | Import `isinstance` and `tuple` from `autograd.builtins` when the check must work on boxed values. |
| `np.linalg.norm(..., ord=...)` raises `NotImplementedError` | The requested norm is outside the supported ord/axis combinations. | Use the supported vector and matrix cases, or reformulate the loss so it uses a supported norm. |
| FFT gradient paths complain about repeated axes or real-FFT shape limits | Those gradient cases are intentionally unsupported. | Remove repeated axes and keep real-FFT inputs in the supported even-length form. |
| An xarray example works until the last line | The container is still holding the boxed values when a scalar output is required. | Keep the ufunc on the container, then extract `.data` or a comparable array before the final reduction. |
| `scipy.stats.multivariate_normal` with a singular covariance is unstable | The singular-covariance gradient path is not supported. | Use a nonsingular covariance or avoid differentiating with respect to that singular matrix. |

## Quick recovery checklist

1. Decide whether the failure is a missing optional dependency, an unsupported wrapper pattern, or a true bug.
2. If it is a missing dependency, install the extra and rerun the smoke helper.
3. If it is a wrapper limitation, rewrite the expression using the supported public form.
4. If it is about derivative semantics or a new custom rule, route to the sibling sub-skill instead of patching this one.

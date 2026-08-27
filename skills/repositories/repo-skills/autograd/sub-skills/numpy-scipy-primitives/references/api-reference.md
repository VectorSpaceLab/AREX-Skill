# API Reference

This reference summarizes the verified wrapper surface covered by the `numpy-scipy-primitives` sub-skill.

## Verified import surface

- `import autograd.numpy as np`
- `import autograd.scipy as asp`
- `from autograd.scipy import special, signal, linalg, integrate, stats`
- optional `import xarray as xr`
- optional `from autograd.builtins import isinstance, tuple, list, dict`

## NumPy wrapper families

| Area | Representative names | Notes |
| --- | --- | --- |
| Numeric ufuncs | `np.sin`, `np.cos`, `np.exp`, `np.log`, `np.maximum`, `np.where`, `np.abs`, `np.real`, `np.imag`, `np.conj` | Most common elementwise math is wrapped and supports complex values where the underlying rule allows it. |
| Reductions and shape ops | `np.sum`, `np.mean`, `np.std`, `np.var`, `np.concatenate`, `np.stack`, `np.append`, `np.vstack`, `np.hstack`, `np.column_stack`, `np.reshape`, `np.squeeze`, `np.expand_dims`, `np.transpose`, `np.moveaxis`, `np.repeat`, `np.tile`, `np.diff`, `np.cumsum` | Several safe wrappers convert list/tuple inputs before calling the primitive. |
| Construction helpers | `np.array`, `np.select`, `np.r_`, `np.c_`, `np.make_diagonal` | Prefer explicit array construction before passing data into a primitive. |
| Linear algebra | `np.linalg.inv`, `solve`, `det`, `slogdet`, `pinv`, `norm`, `eigh`, `eig`, `cholesky`, `svd` | Matrix norm support is partial; see troubleshooting for ord/axis limits. |
| FFT | `np.fft.fft`, `ifft`, `fft2`, `ifft2`, `fftn`, `ifftn`, `rfft`, `irfft`, `rfft2`, `irfft2`, `rfftn`, `irfftn`, `fftshift`, `ifftshift` | Gradient paths have axis and shape limits. |

Method form such as `A.dot(B)` is not part of the supported wrapper contract here; use `np.dot(A, B)` or `np.matmul(A, B)`.

## SciPy wrapper families

| Area | Representative names | Notes |
| --- | --- | --- |
| Special functions | `special.beta`, `betainc`, `betaln`, `polygamma`, `psi`, `digamma`, `gamma`, `gammaln`, `gammainc`, `gammaincc`, `gammasgn`, `rgamma`, `multigammaln`, `j0`, `j1`, `y0`, `y1`, `jn`, `yn`, `i0`, `i1`, `iv`, `ive`, `erf`, `erfc`, `erfinv`, `erfcinv`, `logit`, `expit`, `logsumexp` | `logsumexp` is available through `autograd.scipy.special`. |
| Signal | `signal.convolve` | Supports the public convolution modes used by the repo tests. |
| Linear algebra | `linalg.sqrtm`, `solve_triangular`, `solve_banded`, `solve_sylvester` | Use the bundled troubleshooting notes for matrix-shape and singularity caveats. |
| Integration | `integrate.odeint` | Works with small bounded in-memory systems and flattened auxiliary args. |
| Stats | `stats.beta`, `stats.chi2`, `stats.gamma`, `stats.norm`, `stats.poisson`, `stats.t`, optional `stats.multivariate_normal`, optional `stats.dirichlet` | Each distribution exposes the subset of PDF/CDF/PMF/log variants implemented in the package. |

## xarray and other `__array_ufunc__` containers

- Verified with `xarray.DataArray`.
- NumPy ufuncs such as `np.sin` and `np.maximum` dispatch through the container and keep the boxed values alive.
- Keep a plain scalar output at the end; extract `out.data` or a comparable array before the final reduction.
- The wrappers have no xarray dependency; any other container that implements `__array_ufunc__` should follow the same pattern.

## Complex numbers

Autograd supports complex scalars and arrays. Real-valued losses that use complex primitives can be differentiated, but non-holomorphic questions should be handled carefully and usually belong in the differentiation-core route.

## Public limitations

- Unsupported `A.dot(B)` method form.
- In-place mutation and assignment on differentiable arrays are unsafe.
- Some matrix norms and FFT gradient shapes are intentionally unsupported.
- If SciPy is missing, `autograd.scipy` is unavailable until the optional dependency is installed.

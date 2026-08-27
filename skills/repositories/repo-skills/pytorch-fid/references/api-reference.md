# API Reference

Public APIs live mainly in `pytorch_fid.fid_score` and
`pytorch_fid.inception`. Use this reference when integrating FID computation into
Python code instead of shelling out to the CLI.

## Safe imports

```python
from pytorch_fid.fid_score import (
    ImagePathDataset,
    calculate_activation_statistics,
    calculate_fid_given_paths,
    calculate_frechet_distance,
    compute_statistics_of_path,
    get_activations,
    save_fid_stats,
)
from pytorch_fid.inception import InceptionV3
```

Importing these symbols is safe. Constructing `InceptionV3` for a real FID run
may trigger a weight download when the FID Inception weights are not already in
the PyTorch cache.

## `fid_score` signatures

### `ImagePathDataset(files, transforms=None)`

Torch `Dataset` wrapper around image file paths. Each item opens the image with
Pillow, converts it to RGB, and applies the optional transform. The FID code
passes `torchvision.transforms.ToTensor()`.

### `get_activations(files, model, batch_size=50, dims=2048, device='cpu', num_workers=1)`

Runs an already constructed model over image files and returns a NumPy array of
shape `(num_files, dims)`.

Operating notes:

- `files` should be a sorted list of image paths.
- `model(batch)` must return a list/tuple whose first element is a feature map.
- If the feature map is spatial (`H` or `W` not equal to `1`), the function uses
  adaptive average pooling to `(1, 1)` before flattening.
- If `batch_size > len(files)`, it prints a warning and uses `len(files)`.
- Empty file lists are invalid in practice because the adjusted batch size would
  be zero.

### `calculate_frechet_distance(mu1, sigma1, mu2, sigma2, eps=1e-6)`

Computes the Frechet distance between two multivariate Gaussians:

```python
fid = calculate_frechet_distance(mu_a, sigma_a, mu_b, sigma_b)
```

Requirements:

- `mu1` and `mu2` must have the same one-dimensional shape.
- `sigma1` and `sigma2` must have the same two-dimensional shape.
- Covariances should be square and dimension-compatible with the means.
- Inputs should be finite floating-point arrays.

Behavior:

- Shape mismatches raise `AssertionError` with package messages.
- Near-singular products may print a message and add `eps` to covariance
  diagonals.
- Non-negligible imaginary components from `scipy.linalg.sqrtm` raise
  `ValueError`.
- The return value is a scalar numeric FID value.

### `calculate_activation_statistics(files, model, batch_size=50, dims=2048, device='cpu', num_workers=1)`

Computes image activations with `get_activations`, then returns:

```python
mu, sigma = calculate_activation_statistics(files, model, batch_size, dims, device, num_workers)
```

Return shapes should be:

- `mu`: `(dims,)`
- `sigma`: `(dims, dims)`

Use enough images for a meaningful covariance estimate. Very small file lists
can produce unstable or degenerate covariance values.

### `compute_statistics_of_path(path, model, batch_size, dims, device, num_workers=1)`

Returns `(mu, sigma)` for one path.

- If `path` ends with `.npz`, it loads `mu` and `sigma` from that archive.
- Otherwise it treats `path` as an image directory and computes stats from files
  matching the package's supported extensions.

The package implementation does not deeply validate `.npz` shape, finiteness, or
dimension compatibility here. Run `scripts/validate_fid_inputs.py` or
`scripts/inspect_stats_npz.py` before calling this API in robust workflows.

### `calculate_fid_given_paths(paths, batch_size, device, dims, num_workers=1)`

High-level API for the normal comparison path:

```python
fid_value = calculate_fid_given_paths(
    ["real_images", "generated_images"],
    batch_size=50,
    device="cpu",
    dims=2048,
    num_workers=1,
)
```

Behavior:

- `paths` must contain two existing paths.
- `dims` must be one of `64`, `192`, `768`, or `2048`.
- The function constructs `InceptionV3([block_idx]).to(device)`.
- It then gets statistics for both paths and calls `calculate_frechet_distance`.
- The return value is a scalar FID value.

### `save_fid_stats(paths, batch_size, device, dims, num_workers=1)`

High-level API for precomputing reference stats:

```python
save_fid_stats(["reference_images", "reference_stats.npz"], 50, "cpu", 2048, 1)
```

Behavior:

- `paths[0]` must exist.
- `paths[1]` must not already exist; existing output raises `RuntimeError`.
- The function constructs `InceptionV3`, computes stats for `paths[0]`, and saves
  `mu` and `sigma` with `numpy.savez_compressed`.

## `InceptionV3` signature and layer selection

```python
InceptionV3(
    output_blocks=(3,),
    resize_input=True,
    normalize_input=True,
    requires_grad=False,
    use_fid_inception=True,
)
```

Dimension-to-block mapping:

| `dims` | block index | feature surface |
| --- | --- | --- |
| `64` | `0` | first max-pooling features |
| `192` | `1` | second max-pooling features |
| `768` | `2` | pre-aux-classifier features |
| `2048` | `3` | final average-pooling features |

For FID, keep `use_fid_inception=True` unless intentionally comparing a
nonstandard model. With `use_fid_inception=True`, the package constructs a
patched TorchVision Inception and loads FID-specific weights. With
`use_fid_inception=False`, it uses TorchVision's pretrained Inception path,
which is not comparable to the default FID path.

Forward input/outputs:

- Input tensor shape: `B x 3 x H x W`
- Input value range expected by `InceptionV3.forward`: `(0, 1)` when
  `normalize_input=True`; it rescales internally to `(-1, 1)`.
- Return value: a list of selected feature maps sorted by output block.

## Robust API usage pattern

```python
from pathlib import Path
from pytorch_fid.fid_score import calculate_fid_given_paths

paths = [Path("real_images"), Path("generated_images")]
for path in paths:
    if not path.exists():
        raise FileNotFoundError(path)

fid = calculate_fid_given_paths(
    [str(paths[0]), str(paths[1])],
    batch_size=25,
    device="cpu",
    dims=2048,
    num_workers=1,
)
print(float(fid))
```

For production scripts, validate image counts, `.npz` schema, and expected
dimension before calling the high-level API. See [`data-formats.md`](data-formats.md)
and [`workflows.md`](workflows.md).

## Caveats

- Directory image discovery is shallow; arrange images directly under the input
  directory or provide a precomputed `.npz` file.
- Use lowercase supported extensions for reliable matching across platforms.
- Feature dimension, Inception weights, preprocessing, and implementation must
  stay fixed for scores to be comparable.
- FID from this package is not exactly comparable with the official TensorFlow
  implementation.
- First model construction may need network/cache access for FID weights.
- Torch/TorchVision/NumPy compatibility matters; a NumPy 1.x runtime is safer
  for torch builds that warn or fail with NumPy 2.

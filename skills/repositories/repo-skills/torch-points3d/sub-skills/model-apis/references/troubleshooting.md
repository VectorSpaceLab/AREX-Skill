# Model API Troubleshooting

## Invalid or missing `architecture`

**Symptoms**

- Constructor raises `ValueError()` immediately.
- Error says `model_architecture` value is not within `['unet', 'encoder', 'decoder']`.
- `NotImplementedError` after choosing `decoder`.

**Recovery**

Pass an explicit architecture and choose one implemented by that factory:

```python
model = PointNet2(architecture="unet", input_nc=3, num_layers=3, output_nc=5)
```

Use `"unet"` or `"encoder"` for most high-level API tasks. Treat `"decoder"`
as unsupported unless the concrete factory implements it.

## Dense input shape assertion

**Symptoms**

- `AssertionError` from `_set_input` in PointNet2 or RSConv.
- The model expects batch-major points but receives PyG-style flattened points.

**Recovery**

For PointNet2 and RSConv application APIs, build `Data` objects with `pos` shaped
`[1, N, 3]` and optional `x` shaped `[1, N, C]`, then batch them with PyG
`Batch.from_data_list`. Use the bundled PointNet2 smoke script as a template.

## Feature-channel mismatch

**Symptoms**

- Matrix multiplication, convolution, or batchnorm shape mismatch.
- Output head exists but has unexpected width.

**Recovery**

Make `input_nc` match the last dimension of `x` before Torch Points3D internal
transposes. If you pass `output_nc`, assert `out.x.shape[1] == output_nc` for
high-level `PointNet2`, `KPConv`, and `RSConv` smokes.

## KPConv compiled op failure

**Symptoms**

- Import or runtime errors from `torch_points_kernels`, `torch_cluster`, `torch_scatter`, or `torch_sparse`.
- Build errors while installing `torch-points-kernels`.

**Recovery**

1. Run the root environment probe with `--require-pyg`.
2. Verify PyTorch/PyG wheel compatibility.
3. If only KPConv fails while PointNet2 succeeds, keep dense workflows available and mark KPConv as blocked by compiled extension setup.
4. When building from source, inspect the compiler error and apply a local C++ build fix only for the target environment; do not present local flags as universal.

## Sparse backend failure

**Symptoms**

- `Could not load Minkowski Engine, please check that it is installed correctly`.
- `ModuleNotFoundError: No module named 'MinkowskiEngine'` while importing the Minkowski application.
- `SparseConv3d` fails after selecting `backend="minkowski"` or `backend="torchsparse"`.

**Recovery**

`SparseConv3d` and `Minkowski` are optional-backend workflows. First decide
whether the task can use dense PointNet2/RSConv or partial-dense KPConv. If not,
install the selected sparse backend and re-run:

```bash
python scripts/torch_points3d_env_probe.py --json --require-sparse-backend
```

Then run a sparse-specific model smoke. CPU imports of `torch_points3d` do not
prove sparse backend runtime.

## Pretrained registry surprises

**Symptoms**

- A supposedly local call downloads a `.pt` file.
- Unknown tag error.
- Loading a tag tries to instantiate a dataset or sparse backend.

**Recovery**

Use `PretainedRegistry.available_models()` to inspect tags without downloads.
Ask before calling `from_pretrained(download=True)`. For checkpoint-only model
inspection, prefer `from_file(path, mock_property={...})` when dataset files are
not present and you know the dataset properties.

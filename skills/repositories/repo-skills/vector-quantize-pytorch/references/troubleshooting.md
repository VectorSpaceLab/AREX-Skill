# Troubleshooting

## Install or import failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'vector_quantize_pytorch'` | Package not installed in the active Python environment, or the environment differs from the one running the script | Install with `pip install vector-quantize-pytorch`, then run `python -c "import vector_quantize_pytorch"` from the same interpreter. |
| `ModuleNotFoundError` for `torch`, `einops`, `einx`, or `torch_einops_utils` | Base dependencies are missing or the install was interrupted | Reinstall the package in a clean environment and run `python -m pip check`. |
| Optional example imports fail for `torchvision`, `tqdm`, `fire`, or `x_transformers` | Tutorial/example dependencies are optional and not part of the core package | Install only the optional dependency required by that tutorial. Do not install example extras just to use the core quantizer APIs. |
| CUDA is unavailable inside PyTorch | CPU-only torch wheel, driver/container passthrough issue, or no accelerator selected | This package's selected smoke checks work on CPU. Install a CUDA-capable PyTorch build only when the user's workflow explicitly requires accelerator execution. |

## Shape and layout errors

- Start by reading [package overview](package-overview.md#tensor-layout-conventions) and the owning sub-skill API reference.
- Sequence tensors usually use `(batch, sequence, dim)`.
- Image feature maps usually use `(batch, channels, height, width)` but classes differ in whether they need `accept_image_fmap=True` or `channel_first=True`.
- 3D feature maps need class-specific support such as `VectorQuantize(accept_3d_fmap=True)`.
- Grouped residual quantizers add a leading `groups` axis to indices. Do not feed grouped indices to non-grouped reconstruction helpers.
- If a class has a `dim` argument, it must match the feature dimension after any projection or layout conversion.

## Return tuple mistakes

Do not unpack every quantizer as `(quantized, indices, loss)`.

- `FSQ` returns two values; with `return_indices=False`, the second value is `None`.
- `FSP` returns four values.
- `RandomProjectionQuantizer` returns indices only.
- `HierarchicalVQ` returns a list/tuple of per-scale indices.
- Flags such as `return_all_codes` or `return_loss_breakdown` add extra return data. Read the nearest API reference before changing unpacking code.

## Reconstruction from indices fails or differs

- Use `.eval()` when generating indices intended for later reconstruction unless stochastic training behavior is the goal.
- Save and reload the module state with the indices. Learned-codebook classes reconstruct with the current codebook values, not standalone indices.
- Training-time quantize dropout can mark skipped residual layers with `-1`; handle or avoid these indices before treating them as discrete targets.
- Use `torch.allclose` with a tolerance for projection, perturbation, SimVQ, or low-precision workflows. Exact equality is only expected for specific scalar or deterministic binary cases.

## Codebook or level configuration issues

- `LFQ` `codebook_size` must be a power of two; the internal binary width is derived from `log2(codebook_size)` and `num_codebooks`.
- Scalar quantizers require `levels` to match the intended codebook dimension. If using integer `levels` in `LatentQuantize`, provide `codebook_dim` when needed.
- `VectorQuantize` multi-head and `codebook_dim` options change projected dimensions and index shape. Confirm the expected shape before wiring to a loss or decoder.
- `HierarchicalVQ` scales must fit the feature-map size used for reconstruction. Use the sub-skill smoke helper to test a tiny valid shape before scaling up.

## When to run bundled helpers

- Root import/environment check: `python scripts/check_vector_quantize_env.py`.
- Base VQ and random projection: `python sub-skills/vector-quantization/scripts/smoke_vector_quantize.py`.
- Residual VQ: `python sub-skills/residual-quantizers/scripts/smoke_residual_quantizers.py`.
- FSQ/FSP/residual FSQ: `python sub-skills/scalar-quantizers/scripts/smoke_scalar_quantizers.py`.
- LFQ/Latent/Binary/EvoLFQ: `python sub-skills/lookup-free-and-latent/scripts/smoke_lookup_free_latent.py`.
- SimVQ/HierarchicalVQ: `python sub-skills/sim-and-hierarchical/scripts/smoke_sim_hierarchical.py`.

All bundled helpers use tiny random tensors and should not download datasets, require credentials, or train models.

# Troubleshooting

## Purpose

Use this file for cross-cutting MinkowskiEngine failures that do not belong to one specific workflow. For build flags, compiler choice, or CUDA/BLAS install matrices, read `sub-skills/build-and-install/references/build-reference.md`.

## Common Failure Surfaces

### `ModuleNotFoundError: MinkowskiEngineBackend._C`

**Symptoms**
- `import MinkowskiEngine` fails immediately.
- `MinkowskiEngineBackend._C` cannot be imported.

**Likely causes**
- The extension was never built or installed.
- The wrong environment is being used.
- The install was done for a different Python or ABI.

**Recovery**
- Re-run the bundled smoke helper: `python scripts/check_minkowski_engine.py --smoke`.
- If the helper cannot import the package, follow `sub-skills/build-and-install/SKILL.md`.
- Confirm the environment's Python, `pip check`, and package metadata before trying to patch runtime code.

### `torch.cuda.is_available()` is false in a CUDA build

**Symptoms**
- CUDA examples or GPU tests are unavailable.
- Import warnings say the package was compiled with `CPU_ONLY`.

**Likely causes**
- The package was built in CPU-only mode.
- The host lacks a compatible CUDA toolkit or `nvcc`.
- A CUDA wheel or driver mismatch prevented GPU compilation.

**Recovery**
- Treat the current build as CPU-only until a verified CUDA build exists.
- Read the build sub-skill for `--force_cuda`, `--cuda_home`, and BLAS choices.
- Do not assume GPU support just because the machine has NVIDIA GPUs.

### `OMP_NUM_THREADS` warning at import

**Symptoms**
- Import prints that `OMP_NUM_THREADS` was auto-set.

**Likely causes**
- The host has many CPU cores and no explicit thread cap was exported.

**Recovery**
- Export `OMP_NUM_THREADS` before running heavy scripts if you need a different thread count.
- Use the warning as a performance note, not a failure.

### `SparseTensors must share the same coordinate manager` or `coordinate_map_key` mismatch

**Symptoms**
- Binary ops, concatenation, in-place ops, or slice/decomposition fail with coordinate-manager/key errors.

**Likely causes**
- Sparse tensors were created independently and cannot be compared directly.
- In-place operations require the same coordinate map key, not just the same coordinates.

**Recovery**
- Share the coordinate manager when tensors must interact.
- Use `ME.SparseTensor(..., coordinate_manager=other.coordinate_manager)` when appropriate.
- For in-place operations, also share the coordinate map key.
- If you intended independent tensors, convert them to a common layout first or use the data-workflow sub-skill.

### Wrong coordinate shape or batch layout

**Symptoms**
- Errors about dimension mismatch, invalid coordinate size, or unexpected batch decomposition.

**Likely causes**
- Batch indices are not in the prepended first column.
- Coordinates are not 2D, or coordinates/features have different row counts.

**Recovery**
- Use `ME.utils.batched_coordinates` or `ME.utils.sparse_collate` instead of manual concatenation.
- Remember that batch index comes first in this repo's coordinate convention.
- Recheck quantization and batch-collation before blaming the layer.

### `cublas_v2.h`, undefined symbols, or CUDA version mismatch during build

**Symptoms**
- Build fails around missing CUDA headers, undefined symbols, or invalid device function messages.

**Likely causes**
- The build is pointed at the wrong `CUDA_HOME`.
- The CUDA toolkit and PyTorch CUDA runtime do not match.

**Recovery**
- Read the build sub-skill for the exact `CUDA_HOME` and `--force_cuda` rules.
- Rebuild in a fresh environment rather than trying to patch a broken install in place.

## When to Stop

Stop and move to `build-and-install` when the issue is about environment, compiler, CUDA, BLAS, or importability. Move to `sparse-tensor-data` when the issue is about coordinates, quantization, batching, slicing, or tensor keys. Move to `layers-and-networks` when the issue is about layer arguments, network wiring, or output shapes. Move to `training-and-demos` when the issue is about datasets, collate functions, example scripts, or multi-GPU training patterns.

# Troubleshooting Advanced Protenix Configuration

Use this reference to diagnose backend, config, TFG, confidence, and metric failures without mutating the user's environment unnecessarily.

## First Response Checklist

1. Run `python scripts/protenix_runtime_doctor.py --json`.
2. If model imports are involved, restart with `LAYERNORM_TYPE=torch` before importing `protenix.model.*`.
3. Reduce triangle kernels to `torch` before changing source code.
4. Disable TF32/cache/fusion if a fused path, dtype, or numerical symptom is suspected.
5. Reproduce with the smallest config or tensor shape that still fails.
6. Route prediction command construction to `../../cli-and-inference/SKILL.md`, JSON/features to `../../input-data-and-features/SKILL.md`, and training data/launches to `../../training-and-data-pipeline/SKILL.md`.

## Optional Dependency Import Errors

Symptoms:

- `ModuleNotFoundError` or `ImportError` for `cuequivariance_torch`, `cuequivariance_ops_torch`, `triton`, `deepspeed`, `ninja`, `ml_collections`, or `yaml`.
- Backend-specific import succeeds in one process and fails after changing CUDA/PyTorch packages.

Actions:

- Use the doctor report to distinguish missing imports from CUDA invisibility.
- Switch to `triangle_attention="torch"` and `triangle_multiplicative="torch"` for core config/model debugging.
- Do not select `triangle_attention="deepspeed"` unless `deepspeed` and its DS4Sci Evoformer attention components are available.
- If only YAML/config parsing fails, repair the Python package environment rather than changing Protenix configs.

## Torch or CUDA Is Invisible

Symptoms:

- `torch.cuda.is_available()` is false.
- CUDA device count is zero.
- Kernels fail immediately with CPU tensor/device errors.

Actions:

- Do not test GPU-only kernels in this process.
- Use `LAYERNORM_TYPE=torch` and torch triangle kernels for CPU/config inspection.
- Check whether the installed PyTorch build reports a CUDA version in the doctor output.
- Ask the user before installing or changing GPU packages; GPU driver/runtime repairs are environment operations, not skill-runtime content.

## ABI, Symbol, and Version Mismatches

Symptoms:

- Missing shared-library symbols.
- Errors mention incompatible CUDA, PyTorch, Triton, cuEquivariance, or DeepSpeed versions.
- Extension modules import but fail at first call.

Actions:

- Record package versions from the doctor report.
- Stay on torch kernels when the task does not require optimized backends.
- Align package versions only in an environment-preparation task; do not patch Protenix model math to hide ABI mismatch.
- Remember that the verified inspection environment had Protenix `2.0.0`, PyTorch `2.7.1`, and Triton `3.3.1`; this is evidence, not a universal requirement.

## No Kernel Image or Unsupported GPU

Symptoms:

- `no kernel image is available for execution on the device`.
- Triton import/runtime error with `Not Supported`.
- Failures on consumer GPUs or older architectures.

Actions:

1. Set `LAYERNORM_TYPE=torch` before imports.
2. Use `--triatt_kernel torch --trimul_kernel torch` or equivalent config values.
3. Disable efficient fusion and cache while isolating.
4. Re-enable one path at a time only if the user needs acceleration.
5. If cuEquivariance is required, verify GPU architecture, CUDA runtime, PyTorch, and cuEquivariance package compatibility outside the generated skill content.

## Fast Layer Norm Build or Import Fails

Symptoms:

- Importing model modules triggers CUDA extension build output.
- Failure mentions `fast_layer_norm_cuda_v2`, compiler, `nvcc`, or write permissions.

Actions:

- Restart the process with `LAYERNORM_TYPE=torch` and retry the import.
- Use the doctor script without `--include-model-imports` for a low-risk initial report.
- Only test fused layer norm when the user is specifically troubleshooting fast layer norm or optimized training/inference.
- If a build is required, check `nvcc`, `ninja`, CUDA headers, PyTorch CUDA version, and write permissions in the active Python environment.

## cuEquivariance Fallback Choices

Symptoms:

- Errors mention `cuequivariance_torch`, `cuequivariance_ops_torch`, triangular multiplication, triangle attention, unsupported dtype, unsupported dimension, or tuning cache.

Actions:

- Use `triangle_multiplicative="torch"` and `triangle_attention="torch"` to isolate correctness.
- Know the source fallback: triangular multiplication automatically uses torch when `c_hidden != c_z`, but it does not catch every import/runtime failure.
- Avoid changing `CUEQ_TRITON_TUNING` or cache variables unless the user is intentionally tuning performance.
- For training/backward failures, inspect `enable_tf32`, dtype, and confidence-head skip-AMP settings before changing modules.

## Triton and TriAttention Failures

Symptoms:

- `triton` import errors.
- `Not Supported` errors around `protenix.model.tri_attention`.
- GPU-specific failures in custom attention kernels.

Actions:

- Prefer `triangle_attention="torch"` for correctness isolation.
- The tri-attention package includes a fallback wrapper for import/runtime import failures, but explicit torch selection is clearer for support tasks.
- Verify Triton major version and GPU name with the doctor report.
- Do not assume a passing Triton import means every JIT kernel shape will run.

## DeepSpeed DS4Sci Failures

Symptoms:

- Errors under `deepspeed.ops.deepspeed4science`.
- CUTLASS path errors.
- Build failures after selecting `triangle_attention="deepspeed"`.

Actions:

- Confirm `deepspeed` imports before selecting the backend.
- Check `CUTLASS_PATH` only for the DeepSpeed triangle attention path.
- Switch to `torch`, `cuequivariance`, or `triattention` unless the user explicitly requires DeepSpeed.
- Do not recommend cloning CUTLASS or changing system paths inside generated public skill content; describe the requirement and ask before environment mutation.

## Config Override Typos

Symptoms:

- `unrecognized arguments` from `argparse`.
- Override is accepted but value does not change.
- `config ... not allowed to be none`.

Actions:

- Verify the dotted key exists in the parsed config tree.
- Parse once with `fill_required_with_null=True` for inspection when required values are unavailable.
- For model-specific keys, merge `configs_model_type.model_configs[model_name]` before applying the final override parse.
- Use strings that match the default type: booleans as `true`/`false`, lists as comma-separated strings, and nullable values as `null` only when allowed.

## TFG Misuse

Symptoms:

- `TFG is enabled but no terms are configured`.
- `Unsupported keys in TFG config`.
- `Unknown potential`.
- `TFG is missing required input features`.

Actions:

- Check `../references/tfg-confidence-and-metrics.md` for allowed top-level keys and potential names.
- Treat missing feature keys as input/feature pipeline issues unless the task is to edit a potential registry or validation map.
- Keep TFG disabled for routine prediction unless the user explicitly wants guidance.
- If guidance appears inert, inspect `rho`, `mu`, projection step counts, term intervals, and term weights.

## Confidence Tensor Shape Issues

Symptoms:

- Matrix multiplication or indexing errors in `logits_to_score`, `calculate_ptm`, `calculate_chain_based_gpde`, or `calculate_chain_pair_pae`.
- Chain-pair confidence has surprising directionality.
- NaNs from empty masks or missing frames.

Actions:

- Confirm logits have the bin dimension last.
- Confirm PAE probability shape is `[..., N_token, N_token, N_bins]`.
- Confirm `token_asym_id`, `token_has_frame`, and token masks have length `N_token`.
- For `calculate_chain_pair_pae`, remember that tests preserve 0→1 and 1→0 direction separately.
- Do not silently reshape atom-level arrays to token-level arrays; use `atom_to_token_idx` and feature metadata correctly.

## RMSD and LDDT Shape Issues

Symptoms:

- Assertion failure in `rmsd`.
- Division by zero, NaNs, or invalid alignment results.
- LDDT returns unexpected sample dimensions.

Actions:

- For `rmsd`, require `pred_pose.shape == true_pose.shape == [..., N, 3]`.
- Ensure masks have shape `[..., N]` and contain at least one valid atom per evaluated sample.
- For `LDDT.forward`, pass `pred_coordinate` as `[N_sample, N_atom, 3]`, `true_coordinate` as `[N_atom, 3]`, and a dense pair `lddt_mask` as `[N_atom, N_atom]`.
- Keep all tensors on compatible devices and floating dtypes.
- Use `allowing_reflection=False` unless mirror alignment is explicitly intended.

## When Not to Patch Source

Do not patch model source as a first response when:

- A portable torch backend solves the user's immediate task.
- The failure is clearly an environment mismatch.
- The symptom is a missing optional acceleration dependency.
- The user is assembling a routine prediction command or input JSON.
- The issue is a training data/database path problem.

Patch source only after reproducing a source-level bug with safe fallback settings and a minimal test case.

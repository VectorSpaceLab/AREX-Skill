# Acceleration troubleshooting

Use this matrix after running [check_acceleration_backend.py](../scripts/check_acceleration_backend.py). Keep fixes scoped to backend readiness; route generation, serving, training, and TurboT2AV commands to their owning sub-skills.

## Build and import failures

| Symptom | Likely cause | Fix | Recheck |
| --- | --- | --- | --- |
| `CUDA_HOME is not set` during install | PyTorch extension build cannot find a CUDA toolkit | Install or activate a CUDA toolkit/developer package compatible with the PyTorch CUDA build, then ensure `CUDA_HOME` or the toolkit binaries are visible to the build process | `python -c "from torch.utils.cpp_extension import CUDA_HOME; print(CUDA_HOME)"` |
| `nvcc: command not found` | CUDA runtime/driver exists but compiler toolkit is missing | Install CUDA `nvcc` developer tooling for the target CUDA version; a driver-only system is insufficient for editable/source builds | `nvcc --version` |
| Missing headers such as `cuda.h`, `cusparse.h`, or CUDA library link errors | CUDA developer headers/libraries are missing or version-mismatched | Add CUDA dev headers/libraries matching the active PyTorch CUDA runtime; avoid mixing unrelated toolkit versions | Re-run editable/package build with build isolation disabled only if dependencies are already prepared |
| CUTLASS include errors during `turbo_diffusion_ops` build | CUTLASS submodule contents are absent | Initialize submodules before source/editable install: `git submodule update --init --recursive` | Confirm CUTLASS include directories exist, then rebuild |
| Build process is killed or stalls | CUDA extension compilation is resource-heavy | Reduce parallel jobs, use a machine with enough RAM/CPU, and keep only required dependency variants in the environment | Re-run the install with a lower job count and inspect the first compiler error |
| `ImportError: No module named turbo_diffusion_ops` | Custom extension was not built/installed or the wrong Python environment is active | Reinstall the package in the environment used to run inference; for source builds, ensure CUDA dev tooling and CUTLASS are present | `python sub-skills/acceleration-backends/scripts/check_acceleration_backend.py --require-cuda` |
| `undefined symbol` or ABI error importing `turbo_diffusion_ops` | Extension was built against a different PyTorch/CUDA/Python ABI | Clean/rebuild the extension under the active PyTorch and Python environment; avoid copying compiled `.so` files between environments | Import `torch` first, then `turbo_diffusion_ops` in the target environment |

## Dependency failures

| Symptom | Likely cause | Fix | Recheck |
| --- | --- | --- | --- |
| `flash_attn is not installed.` message or import failure in Wan/rCM modules | `flash-attn` dependency was skipped or failed to build | Install `flash-attn` compatible with the active CUDA/PyTorch stack; it may require `--no-build-isolation` after PyTorch is installed | Run a help/parser smoke for the target script and the diagnostic import checks |
| `AssertionError: Install SpargeAttn first to enable SageSLA.` | `attention_type=sagesla` requested but SpargeAttn is missing | Either install SpargeAttn with user approval or switch to `--attention_type sla` / `original` | `python sub-skills/acceleration-backends/scripts/check_acceleration_backend.py --require-sagesla` |
| Diagnostic reports `SAGESLA_ENABLED = false` | The optional `spas_sage_attn` package is not importable | Same as above; missing SpargeAttn is acceptable for `sla` and `original` but not for `sagesla` | Require SageSLA only for tasks that use `attention_type=sagesla` |
| SageSLA import succeeds but forward fails on head dimension | SageSLA path expects head dimension 64 or 128 | Use supported Wan model dimensions or pad/adapt only with a model-aware implementation | Validate in full model context rather than synthetic arbitrary shapes |

## Runtime flag mismatches

| Symptom | Likely cause | Fix | Recheck |
| --- | --- | --- | --- |
| State-dict key or shape mismatch after adding `--quant_linear` | The checkpoint is unquantized but command requests INT8 Linear modules | Remove `--quant_linear` or use the matching quantized checkpoint | Compare checkpoint naming/metadata and rerun parser/backend checks |
| Runtime custom-op failure only when `--quant_linear` is set | `Int8Linear` path uses `turbo_diffusion_ops` and CUDA | Verify custom op import and tiny INT8 smoke; if unavailable, use an unquantized checkpoint without `--quant_linear` | Diagnostic script with `--require-cuda` |
| Quality/speed tradeoff is poor with default `sla_topk=0.1` | Top-k ratio is too low for the target video quality | Consider `--sla_topk 0.15` for TurboDiffusion Wan workflows; higher ratios usually improve quality at more attention cost | Compare with the same seed/checkpoint after routing to inference sub-skill |
| User adds `--default_norm` expecting faster norms | Flag semantics are inverted: `--default_norm` keeps original Wan LayerNorm/RMSNorm | Omit `--default_norm` to enable FastNorm replacements | Diagnostic FastNorm smokes plus command review |
| `attention_type=sagesla` silently assumed from README defaults | Optional SpargeAttn was not installed | Explicitly choose `sla` or install SpargeAttn; do not leave default `sagesla` when the backend cannot support it | Diagnostic `SAGESLA_ENABLED` signal |

## Source-layout import failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `No module named imaginaire`, `rcm`, `ops`, `SLA`, `serve`, or `modify_model` when running a source script | Some scripts were authored to import top-level modules from the inner package source directory | Run source scripts with `PYTHONPATH=<path-to-inner-turbodiffusion-directory>` or install the package and prefer qualified module imports where available |
| Installed console entry point still hits source-layout imports | The entry point reaches modules that import source-layout top-level names | Add the same generic `PYTHONPATH` entry for source-layout compatibility, or patch/wrap commands through the owning sub-skill command builders |
| Fully qualified `turbodiffusion.ops` works but top-level `ops` does not | This is expected outside source-layout script execution | Do not treat missing top-level `ops` as a package install failure unless running a source-authored script that requires it |

Never record a user's absolute source directory in the runtime skill. Express the fix as a generic `PYTHONPATH` entry.

## Tiny SLA random-forward warning

A tiny random `SparseLinearAttention` forward can compile and run but produce non-finite values. Treat this as a warning, not as a correctness failure for real model inference, because the synthetic tensor does not represent a validated Wan model context. Use it only to expose severe import/kernel crashes. Do not accept it as proof that SLA quality or numerical behavior is correct.

If this warning appears:

1. Confirm the diagnostic still passed the required import/custom-op/FastNorm checks.
2. Prefer model-context validation when checkpoints are available.
3. If the user only needs `sagesla`, focus on SpargeAttn readiness instead of plain SLA random tensors.
4. If non-finite values occur during real generation, route to inference troubleshooting with the exact checkpoint, prompt, seed, `attention_type`, `sla_topk`, and precision settings.

## Escalation rules

- If backend checks fail before any model command is built, stay in this sub-skill.
- If a command is valid but model paths, prompts, image inputs, or output files are wrong, route to `video-inference` or `interactive-serving`.
- If checkpoint conversion or quantized export failed, route to `training-and-checkpoints` after confirming the backend state here.
- If the question mentions TileLang, Pixi, LTX-2, W8A8 post-scale, Gemma, or TurboT2AV checkpoints, route to `turbot2av-extension`.

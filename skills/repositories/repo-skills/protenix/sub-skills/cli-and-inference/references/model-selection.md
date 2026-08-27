# Model Selection and Inference Controls

## Supported Prediction Models

Use the model name exactly as the CLI expects it. The installed model list supports these prediction names:

| Model name | MSA | RNA MSA | Template | Typical use |
| --- | --- | --- | --- | --- |
| `protenix-v2` | Yes | Yes | Yes | Enhanced-capacity current model for high-quality predictions. |
| `protenix_base_default_v1.0.0` | Yes | Yes | Yes | Conservative default for fair v1-style predictions and template/RNA MSA support. |
| `protenix_base_20250630_v1.0.0` | Yes | Yes | Yes | Practical-application v1 model with a later training-data cutoff. |
| `protenix_base_default_v0.5.0` | Yes | No | No | Backward-compatible base model without template/RNA MSA support. |
| `protenix_base_constraint_v0.5.0` | Yes | No | No | v0.5 constraint model; route constraint JSON details to input-data skills. |
| `protenix_mini_esm_v0.5.0` | No by default | No | No | Lightweight ESM-backed model; default params force `use_msa=false`. |
| `protenix_mini_ism_v0.5.0` | No by default | No | No | Lightweight ISM-backed model; default params force `use_msa=false`. |
| `protenix_mini_default_v0.5.0` | Yes | No | No | Lightweight smoke-test or high-throughput shape. |
| `protenix_tiny_default_v0.5.0` | Yes | No | No | Smallest supported model shape. |

If the user asks for template or RNA MSA inference, choose only `protenix-v2`, `protenix_base_default_v1.0.0`, or `protenix_base_20250630_v1.0.0`.

## Default Parameters

`protenix pred` exposes `--cycle`, `--step`, and `--sample`, but `--use_default_params true` resets cycle and step for known model families:

| Model family | Effective `cycle` | Effective `step` | Extra behavior |
| --- | ---: | ---: | --- |
| `protenix-v2` | 10 | 200 | Keeps MSA setting supplied by user. |
| v1/base/constraint models | 10 | 200 | Keeps MSA setting supplied by user. |
| mini/tiny models | 4 | 5 | Mini ESM/ISM also force `use_msa=false`. |

`--use_default_params` does not reset `--sample`; sample count is still controlled by `--sample`.

Examples:

```bash
# Model defaults: cycle/step determined by model family.
protenix pred --input input.json --out_dir output --model_name protenix_base_default_v1.0.0 --use_default_params true

# Explicit reduced command: defaults disabled so cycle/step are honored.
protenix pred --input input.json --out_dir smoke --model_name protenix_mini_default_v0.5.0 --use_default_params false --cycle 4 --step 5 --sample 1
```

## Seeds

Use `--seeds` for comma-separated CLI seeds:

```bash
protenix pred --input input.json --out_dir output --seeds 101,102
```

If `--use_seeds_in_json true` is set, Protenix logs that JSON `modelSeeds` take priority over CLI seeds. Route JSON placement, examples, and schema validation to `../../input-data-and-features/SKILL.md`.

## Dtype

The default dtype is `bf16`. Use `fp32` when diagnosing mixed-precision issues or when a CPU/fallback environment does not support BF16 efficiently:

```bash
protenix pred --input input.json --out_dir output --dtype fp32 --trimul_kernel torch --triatt_kernel torch
```

Inference internally keeps some confidence/diffusion computations in full precision depending on token count and model. Deep precision-policy changes route to `../../advanced-model-configuration/SKILL.md`.

## Cache and Checkpoint Expectations

`protenix pred` is not just a command validator. Once launched, it can initialize the inference runner and download runtime files before prediction:

- Model checkpoints are expected under the runtime checkpoint directory derived from `PROTENIX_ROOT_DIR` plus `checkpoint`.
- Common cache files such as chemical component/cache metadata are downloaded when missing.
- Template cache metadata may also be downloaded when `--use_template true`.
- ESM/ISM models can require additional ESM checkpoint files.

For public skill content, never hard-code a local cache root or checkout path. Tell the user to set `PROTENIX_ROOT_DIR` on the runtime machine if they want caches and checkpoints somewhere specific:

```bash
export PROTENIX_ROOT_DIR=/path/to/protenix-data-root
protenix pred --input input.json --out_dir output --model_name protenix_base_default_v1.0.0 --use_default_params true
```

If the user only wants command validation, use `scripts/build_protenix_pred_command.py`; it does not import Protenix or trigger downloads.

## Kernel Flags

The user-facing kernel controls are:

| Flag | Portable value | Accelerated values | Notes |
| --- | --- | --- | --- |
| `--trimul_kernel` | `torch` | `cuequivariance` | `cuequivariance` is the default and requires compatible dependencies. |
| `--triatt_kernel` | `torch` | `cuequivariance`, `triattention`, `deepspeed` | `deepspeed` requires a valid `CUTLASS_PATH` at runtime. |
| `--enable_cache` | `false` for debugging | `true` by default | Enables diffusion shared-variable cache. |
| `--enable_fusion` | `false` for debugging | `true` by default | Enables efficient diffusion transformer fusion. |
| `--enable_tf32` | `false` for strict numerics | `true` by default | Allows TF32 matrix operations on supported NVIDIA GPUs. |

Recommended no-run fallback command shape for CUDA/JIT failures:

```bash
python sub-skills/cli-and-inference/scripts/build_protenix_pred_command.py \
  --input input.json \
  --out-dir output \
  --trimul-kernel torch \
  --triatt-kernel torch \
  --dtype fp32 \
  --print-warnings
```

For cuEquivariance installation, CUTLASS compatibility, layernorm JIT, or backend-specific performance tuning, route to `../../advanced-model-configuration/SKILL.md`.

## TFG Routing

`--use_tfg_guidance true` toggles Training-Free Guidance during prediction:

```bash
protenix pred --input input.json --out_dir output --use_tfg_guidance true
```

Keep this sub-skill at the flag-routing level. TFG scoring, guidance internals, and config surgery belong to `../../advanced-model-configuration/SKILL.md`.

## Model/Feature Decision Checklist

1. Does the user need template or RNA MSA support? Use `protenix-v2` or a v1.0.0 base model.
2. Does the user need fair v1 benchmark comparability? Use `protenix_base_default_v1.0.0`.
3. Does the user want practical latest-cutoff behavior from v1? Use `protenix_base_20250630_v1.0.0`.
4. Does the user need a lightweight smoke-test command shape? Use `protenix_mini_default_v0.5.0` or `protenix_tiny_default_v0.5.0`, with `--use_default_params false` if they chose explicit cycle/step values.
5. Does the command fail in CUDA kernels? Keep the same model but switch `--trimul_kernel torch --triatt_kernel torch`, then route deeper backend work to advanced configuration.

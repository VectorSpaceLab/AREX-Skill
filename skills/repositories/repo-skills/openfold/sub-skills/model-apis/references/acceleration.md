# OpenFold Acceleration and Optional Kernels

OpenFold exposes acceleration choices through config fields, model internals, CLI flags, and optional packages. Use this reference for API-level reasoning; route backend installation and hardware setup to `../installation-assets/`, CLI command construction to `../inference/`, and training launch choices to `../training/`.

## Config-Level Switches

`model_config(...)` exposes these acceleration-related arguments:

- `long_sequence_inference=False`
- `use_deepspeed_evoformer_attention=False`
- `use_cuequivariance_attention=False`
- `use_cuequivariance_multiplicative_update=False`
- `precision="tf32"`
- `trt_mode=None`
- `trt_engine_dir=None`
- `trt_num_profiles=1`
- `trt_optimization_level=3`
- `trt_max_sequence_len=640`

The config constraint pass validates optional package availability for enabled FlashAttention, DeepSpeed4Science Evoformer attention, and cuEquivariance flags. This can fail during config construction before any model is created.

## DeepSpeed Evoformer Attention

API/config signal:

- `config.globals.use_deepspeed_evo_attention`
- `model_config(..., use_deepspeed_evoformer_attention=True)`

Dependency signal:

- `deepspeed` must be importable.
- `deepspeed.ops.deepspeed4science` must be importable.

Failure behavior:

- `model_config` raises `ValueError` when DeepSpeed Evoformer attention is requested but DeepSpeed4Science is unavailable.
- Long-sequence inference can enable this flag automatically unless low-memory attention is already selected.

Native candidate:

- Maintainer DeepSpeed attention tests compare regular, DeepSpeed, and optional FlashAttention attention paths. Treat them as optional-package and hardware sensitive.

## cuEquivariance Kernels

API/config signals:

- `config.globals.use_cuequivariance_attention`
- `config.globals.use_cuequivariance_multiplicative_update`
- `model_config(..., use_cuequivariance_attention=True, use_cuequivariance_multiplicative_update=True)`

Dependency signal:

- `cuequivariance_torch` must be importable.

Failure behavior:

- `model_config` raises `ValueError` when either cuEquivariance flag is requested without `cuequivariance_torch`.
- Source internals indicate cuEquivariance attention can fall back for unsupported shapes; validate the intended fallback backend before relying on it.

Native candidate:

- Maintainer cuEquivariance tests cover cuEquivariance attention and multiplicative-update behavior. Treat them as optional-package and hardware sensitive.

## FlashAttention

API/config signal:

- `config.globals.use_flash = True`, usually through a config override after `model_config` or via user-facing CLI/experiment config.

Dependency signal:

- `flash_attn` must be importable.

Constraint behavior:

- FlashAttention is mutually exclusive with `globals.use_lma` and `globals.use_deepspeed_evo_attention`.
- FlashAttention is also mutually exclusive with `globals.use_cuequivariance_attention`.
- Long-sequence inference disables FlashAttention.

Use `scripts/validate_config_preset.py --use-flash` to test the config path without model construction.

## TensorRT

TensorRT config fields live under `config.trt`:

- `config.trt.mode`
- `config.trt.engine_dir`
- `config.trt.num_profiles`
- `config.trt.optimization_level`
- `config.trt.max_sequence_len`

Planning guidance:

- Set `trt_mode` only when TensorRT is installed and the engine lifecycle is planned.
- Use an explicit `trt_engine_dir`; do not rely on private cache paths.
- Choose `trt_max_sequence_len` to cover expected sequence lengths.
- Config validation does not compile, run, or reuse engines.

Example safe validation:

```bash
python scripts/validate_config_preset.py \
  --preset model_1_ptm \
  --trt-mode run \
  --trt-engine-dir engines \
  --trt-max-sequence-len 2048 \
  --json
```

## Long-Sequence Inference

`long_sequence_inference=True` is an inference-only memory profile. Source behavior:

- Asserts `train` is false.
- Enables `globals.offload_inference`.
- Enables DeepSpeed Evoformer attention unless LMA is already selected.
- Disables FlashAttention.
- Enables template offload inference.
- Disables tune-chunk-size behavior in template pair stack, extra MSA stack, and Evoformer stack.

Safe TensorRT-disabled validation:

```bash
python scripts/validate_config_preset.py \
  --preset model_1_ptm \
  --long-sequence-inference \
  --precision tf32 \
  --json
```

If this fails because DeepSpeed4Science is unavailable, either route backend installation to `../installation-assets/` or choose a manual memory strategy that avoids DeepSpeed-specific flags.

## Precision

- `tf32` is the default `model_config` precision.
- `bf16` can reduce memory on compatible hardware.
- `fp16` should be treated as numerically risky unless the user explicitly accepts it.
- `low_prec=True` changes config numerical constants and is separate from the `precision` string.

Runtime support depends on PyTorch, device, CUDA, and optional backends; route environment readiness to `../installation-assets/`.

## Maintainer Test Selection

| Goal | Candidate | Default stance |
| --- | --- | --- |
| Base config/parser smoke | Safe import/config checks | Good default and currently viable. |
| Base model compatibility | Maintainer model tests | Skip until `attn_core_inplace_cuda` and model imports work. |
| Custom kernel build/parity | Maintainer kernel tests | Skip unless compiled kernels and hardware are ready. |
| DeepSpeed Evoformer attention | Maintainer DeepSpeed attention tests | Optional; requires DeepSpeed4Science and compatible runtime. |
| FlashAttention parity | FlashAttention parity cases | Optional; requires `flash_attn`. |
| cuEquivariance paths | Maintainer cuEquivariance tests | Optional; requires `cuequivariance_torch`. |
| Weight translation | Maintainer import-weight tests | Safer than full inference if fixtures are small, but still requires model imports. |

Do not run model/kernel tests as generic smoke checks in an environment where `openfold.model.model` cannot import.

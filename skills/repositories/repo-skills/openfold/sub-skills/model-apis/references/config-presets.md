# OpenFold Config Presets

`model_config(...)` is the supported API for selecting OpenFold model presets and applying high-level overrides before model construction. Validate unusual combinations with `../scripts/validate_config_preset.py`; it builds the config only and does not instantiate `AlphaFold`.

## Signature

```python
model_config(
    name,
    train=False,
    low_prec=False,
    long_sequence_inference=False,
    use_deepspeed_evoformer_attention=False,
    use_cuequivariance_attention=False,
    use_cuequivariance_multiplicative_update=False,
    precision="tf32",
    trt_mode=None,
    trt_engine_dir=None,
    trt_num_profiles=1,
    trt_optimization_level=3,
    trt_max_sequence_len=640,
)
```

## Preset Families

| Family | Examples | Typical use | Notes |
| --- | --- | --- | --- |
| Monomer inference | `model_1` through `model_5` | AlphaFold/OpenFold monomer prediction. | `model_1` and `model_2` use templates; `model_3` through `model_5` disable templates. |
| Monomer pTM inference | `model_1_ptm` through `model_5_ptm` | Monomer prediction with TM/pAE-style heads. | Template behavior follows the matching non-pTM model number. |
| Multimer inference | `model_1_multimer`, `model_1_multimer_v2`, `model_1_multimer_v3`, and sibling IDs where supported | Complex prediction with multimer feature semantics. | Source handles multimer branches and sets `globals.is_multimer`. Match weights and data to multimer family. |
| SoloSeq / sequence embeddings | `seq_model_esm1b`, `seq_model_esm1b_ptm` | Single-sequence embedding mode. | Expects sequence-embedding features such as `seq_embedding`; do not assume ordinary MSA features. |
| Training | `initial_training`, `finetuning`, `finetuning_ptm`, `finetuning_no_templ`, `finetuning_no_templ_ptm` | Training/fine-tuning configs. | Training command construction belongs in `../training/`. |
| Sequence-embedding training | `seqemb_initial_training`, `seqemb_finetuning` | Training sequence-embedding variants. | Confirm feature and checkpoint compatibility before use. |

Invalid names raise `ValueError: Invalid model name`.

## Summary Fields Worth Inspecting

The bundled helper reports stable fields rather than dumping the full nested config:

- `globals.is_multimer`: selects multimer embedders and multimer feature semantics.
- `globals.seqemb_mode_enabled`: indicates sequence-embedding/SoloSeq path.
- `globals.use_deepspeed_evo_attention`, `globals.use_cuequivariance_attention`, `globals.use_cuequivariance_multiplicative_update`, `globals.use_flash`, and `globals.use_lma`: mutually constrained attention/memory paths.
- `globals.offload_inference`, `globals.chunk_size`, and `globals.blocks_per_ckpt`: memory and checkpointing behavior.
- `model.template.enabled`, `model.template.offload_templates`, and `model.template.offload_inference`: template path behavior.
- `model.heads.tm.enabled`: TM/pTM-style auxiliary head availability.
- `data.common.use_templates`, `data.predict.max_msa_clusters`, and `data.predict.max_extra_msa`: feature-pipeline expectations.
- `trt.mode`, `trt.engine_dir`, `trt.num_profiles`, `trt.optimization_level`, and `trt.max_sequence_len`: TensorRT planning fields.

## Safe Override Guidance

| Intent | Preferred API choice | Notes |
| --- | --- | --- |
| Conservative inference config | `precision="tf32"` | Default signature value. Runtime hardware support still matters. |
| Lower memory on compatible hardware | `precision="bf16"` | Usually safer than FP16, but hardware/runtime validation belongs in `../installation-assets/`. |
| FP16 experimentation | `precision="fp16"` | Supported by the config API, but treat as numerically risky. |
| Low-precision constants | `low_prec=True` | Changes numerical constants such as `eps` and `inf`; avoid for strict checkpoint parity unless requested. |
| Long-sequence memory mode | `long_sequence_inference=True` | Inference-only and can enable DeepSpeed Evoformer attention. |
| DeepSpeed Evoformer attention | `use_deepspeed_evoformer_attention=True` | Requires `deepspeed.ops.deepspeed4science`. |
| cuEquivariance attention/update | `use_cuequivariance_attention=True` and/or `use_cuequivariance_multiplicative_update=True` | Requires `cuequivariance_torch`. |
| TensorRT fields | `trt_mode`, `trt_engine_dir`, profile count, optimization level, max sequence length | Config validation does not compile or run engines. |
| Training config | `train=True` with a training preset | Training launches, experiment setup, and resume commands belong in `../training/`. |

## Constraint Behavior

`enforce_config_constraints(config)` is called before `model_config` returns. It enforces:

- `model.template.average_templates` and `model.template.offload_templates` are mutually exclusive.
- Only one of `globals.use_lma`, `globals.use_flash`, and `globals.use_deepspeed_evo_attention` may be true.
- Only one of `globals.use_lma`, `globals.use_flash`, and `globals.use_cuequivariance_attention` may be true.
- `globals.use_flash=True` requires the `flash_attn` package.
- `globals.use_deepspeed_evo_attention=True` requires both `deepspeed` and `deepspeed.ops.deepspeed4science`.
- cuEquivariance flags require `cuequivariance_torch`.
- `long_sequence_inference=True` asserts `train` is false.

If optional backends are missing, config construction can fail before any model is instantiated. This is expected and useful for cheap validation.

## Long-Sequence With TensorRT Disabled

A difficult but common request is to validate long-sequence inference while keeping TensorRT disabled. Use:

```bash
python scripts/validate_config_preset.py \
  --preset model_1_ptm \
  --long-sequence-inference \
  --precision tf32 \
  --json
```

In source, long-sequence inference:

- Enables `globals.offload_inference`.
- Enables `globals.use_deepspeed_evo_attention` unless low-memory attention is already selected.
- Disables `globals.use_flash`.
- Enables template offload inference.
- Disables chunk-size tuning for template pair stack, extra MSA stack, and Evoformer stack.

Because it may enable DeepSpeed Evoformer attention, the validation can fail on systems without DeepSpeed4Science. If the user cannot install that backend, plan a manual memory strategy or route environment setup to `../installation-assets/`; do not silently claim long-sequence mode is usable.

## Routing Rules

- Use this reference for preset and config-object selection.
- Route raw data and feature-pipeline layout to `../data-preparation/`.
- Route public CLI flags exposing these options to `../inference/`.
- Route training experiment configs and launchers to `../training/`.
- Route optional backend installation and compiled-extension repair to `../installation-assets/`.

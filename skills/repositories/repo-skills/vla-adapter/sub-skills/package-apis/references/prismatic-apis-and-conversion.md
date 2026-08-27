# Prismatic APIs and Conversion Reference (external native checkout)

This document records native checkpoint layouts and source-entrypoint
inventory. It does not provide or execute `load`, `load_vla`, action-head,
LoRA-merge, or HF-conversion implementations. Inspect or run any listed native
entrypoint only after `cd <absolute-repo-root>` in the separate checkout.
## Native checkpoint layouts

### Base Prismatic VLM run

Typical files:

```text
config.json
checkpoints/latest-checkpoint.pt
```

The local `load()` path currently expects the exemplar checkpoint filename under `checkpoints/`.

### Native OpenVLA / VLA run

Typical files:

```text
config.json
dataset_statistics.json
checkpoints/latest-checkpoint.pt
```

When fine-tuning with LoRA, the checkpoint directory also includes:

```text
lora_adapter/
```

Common sidecar weights may also appear when the corresponding training option is enabled:

- `proprio_projector--*.pt`
- `noisy_action_projector--*.pt`
- `action_head--*.pt`
- `vision_backbone--*.pt`

### HF-style export bundle

Typical files:

```text
config.json
configuration_prismatic.py
modeling_prismatic.py
processing_prismatic.py
preprocessor_config.json
processor_config.json
tokenizer.json
tokenizer_config.json
special_tokens_map.json
added_tokens.json
vocab.json
merges.txt
generation_config.json
```

For OpenVLA exports, keep `dataset_statistics.json` beside the HF assets so the action-prediction path can unnormalize outputs.

## Source-script inventory for this sub-skill

These native entry points define the evidence behind this sub-skill:

| Script | Role |
| --- | --- |
| `scripts/extern/convert_prismatic_weights_to_hf.py` | Prismatic VLM HF conversion rules, projector key remapping, TIMM LayerScale patching, processor save flow |
| `vla-scripts/extern/convert_openvla_weights_to_hf.py` | OpenVLA HF conversion, dataset statistics copy, fused-vision remapping |
| `vla-scripts/merge_lora_weights_and_save.py` | LoRA adapter merge flow and adapter-directory expectation |
| `vla-scripts/train.py` | Native VLA run layout, dataset statistics save point, checkpoint sidecar patterns |
| `vla-scripts/finetune.py` | Fine-tuning checkpoint layout, LoRA adapter output, component sidecars |
| `scripts/extern/verify_prismatic.py` | HF-model smoke verification pattern for Prismatic exports |
| `vla-scripts/extern/verify_openvla.py` | HF-model smoke verification pattern for OpenVLA exports |

## Conversion expectations

### Prismatic HF conversion

The Prismatic converter remaps:

- `projector.0/2/4.*` → `projector.fc1/fc2/fc3.*`
- `llm.` → `language_model.`
- vision backbone keys → `vision_backbone.*`
- `LayerScale.gamma` → `scale_factor`

It expects a run directory with `config.json` and `checkpoints/latest-checkpoint.pt`.

### OpenVLA HF conversion

The OpenVLA converter additionally:

- reads `dataset_statistics.json`
- remaps native `vision_backbone` keys for single or fused backbones
- copies `dataset_statistics.json` into the output bundle

It expects the same run-directory layout plus the statistics file.

### LoRA merge flow

The merge utility expects:

- a base checkpoint or base model id/path
- a fine-tuned checkpoint directory containing `lora_adapter/`
- compatible base model code for the selected mini/full path

The merge path can be CUDA-heavy because it materializes the base model and adapter together before `merge_and_unload()`.

## Layout checker scope

Use `scripts/check_checkpoint_layout.py` to validate:

- the checkpoint root itself
- `config.json`
- optional `dataset_statistics.json`
- optional `lora_adapter/`
- HF-style config assets when requested

It is intentionally a layout checker, not a weight loader.

# Model and Backend Compatibility

## Supported model families

| Family | Notes |
| --- | --- |
| `Qwen2-VL` | Default system message is used. No reasoning-format training support. |
| `Qwen2.5-VL` | Mixed-modality and video training are supported; video handling uses the repo’s Qwen2.5-specific forward path. |
| `Qwen3-VL` | Uses 32×32-style token budgeting in the repo docs; reasoning support is only for the Thinking variant. |
| `Qwen3-VL-MoE` | Uses the same Qwen3-VL family rules plus the MoE-specific patches and Liger 0.8 support. |
| `Qwen3.5` | Reasoning support is enabled; optional reasoning samples are allowed. |
| `Qwen3.5-MoE` | Same reasoning rules as Qwen3.5 plus Liger 0.8 MoE support. |

## Reasoning rules

- `--enable_reasoning True` is supported only for `Qwen3-VL-*-Thinking` and `Qwen3.5`.
- For `Qwen3-VL-*-Thinking`, every assistant turn must include a non-empty `reasoning` field when reasoning is enabled.
- For `Qwen3.5`, a sample may include reasoning or omit it; the repo uses the official non-thinking scaffold for the no-reasoning case.
- DPO needs either both `chosen_reasoning` and `rejected_reasoning`, or neither.

## Backend and kernel notes

- Flash Attention 2 is optional. The documented fallback for Qwen3.5 is `--disable_flash_attn2 True`.
- Liger 0.8.0 is the pinned model-family target in this repo. It is recommended for Qwen3-VL-MoE and Qwen3.5-MoE, but QLoRA + Liger is not the recommended combination.
- DeepSpeed ZeRO-2 and ZeRO-3 are both supported. Offload templates exist for memory-constrained runs.
- Video data uses the repo’s multimodal preprocessing path and a PyAV/FFmpeg-supported runtime.

## Training implications

- Dense Qwen3-VL full finetuning with Liger can be slow; the README recommends turning off Liger or switching to ZeRO-2 in that case.
- For video, keep `fps` and `nframes` mutually exclusive.
- For QLoRA + vision, avoid combining quantization bits with `vision_lora`, `freeze_vision_tower=False`, or `unfreeze_topk_vision>0`.

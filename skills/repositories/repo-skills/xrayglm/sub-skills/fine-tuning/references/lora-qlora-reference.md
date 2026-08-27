# LoRA, QLoRA, and P-Tuning reference

Evidence: `finetune_XrayGLM.py` and `lora_mixin.py`, with runtime facts
provided for this checkout.

## Choosing an adapter

| Request | Source behavior | Gate and trade-off |
|---|---|---|
| `--use_ptuning` | Adds `PTuningV2Mixin(..., pre_seq_len)` to the model. `disable_untrainable_params()` keeps parameters whose names contain `ptuning`. | Small trainable prefix and lower optimizer state, but still requires the full VisualGLM forward and image encoder in CUDA memory. Verify the saved prefix keys. |
| `--use_lora` | Adds `LoraMixin(..., r=lora_rank, head_first=True, layer_range=[0, 14])`, replacing attention dense and QKV projections in selected layers, plus decoder cross-attention where applicable. | Preferred fallback when QLoRA is unavailable. Base weights are frozen; `matrix_A` and `matrix_B` are trainable. Rank default is 10. |
| `--use_qlora` | Uses the same LoRA path with `qlora=True`, constructs `bitsandbytes.nn.LinearNF4`, and recursively replaces transformer linear layers with 4-bit layers. | Conditional only. Requires a compatible CUDA bitsandbytes build and successful `LinearNF4` initialization; the installed CPU-only/missing-libcudart warnings block readiness. |

P-Tuning and LoRA flags can both add mixins because their source branches are
not mutually exclusive with `use_ptuning`, but do not combine them casually:
record the expected trainable names and verify checkpoint loading. LoRA and
QLoRA are mutually exclusive in practice because `use_lora` is checked first
and suppresses the `use_qlora` branch when both are true.

## What actually becomes trainable

`disable_untrainable_params()` starts with an empty enable list and adds
`ptuning` for P-Tuning and `matrix_A`, `matrix_B` for either LoRA flavor. Every
other named parameter receives `requires_grad_(False)`. The mixin prints
parameters that remain enabled. Capture that output during a preflight or
small approved CUDA check. Do not assume `lora_rank` alone proves the adapter
is active.

The custom LoRA implementation initializes A matrices with Kaiming uniform and
B matrices with zeros. It applies `lora_alpha / r` scaling (alpha defaults to
1) and no dropout by default. Attention is partitioned for QKV and assembled
with `head_first=True`; this implementation assumes the model's QKV output
order. Its fixed layer range is `list(range(0, 28, 14))`, i.e. layers 0 and 14,
not all 28 layers. Cross-attention modules are also replaced when the target
layer is a decoder layer.

The visual encoder path (`eva`, BLIP2 ViT/Q-Former, and `glm_proj`) is not made
trainable by these adapter flags. If a future change intends to train it,
that is a different scope and needs a new trainable-parameter audit.

## QLoRA readiness gate

QLoRA is not ready merely because `bitsandbytes` appears in `requirements.txt`
or imports without an exception. This checkout reports bitsandbytes 0.39.0
warnings about a CPU-only build/missing `libcudart`; treat that as a hard
conditional block. Before any QLoRA launch, in the exact Python 3.10/CUDA
runtime, run a no-training probe equivalent to:

```bash
python - <<'PY'
import torch
from bitsandbytes.nn import LinearNF4
assert torch.cuda.is_available(), "CUDA is required for QLoRA readiness"
layer = LinearNF4(16, 16).cuda()
x = torch.randn(1, 16, device="cuda", dtype=torch.float16)
layer(x)
print("LinearNF4 CUDA probe passed")
PY
```

This probe is still not 6B distributed-training validation. If it fails, do
not suppress the warning or claim QLoRA readiness. Use standard LoRA, or
install and verify a bitsandbytes build compatible with the deployed CUDA and
torch versions, then rerun the probe. The host having no `nvcc` means a source
build may be unavailable; use a compatible prebuilt package or stop.

## Checkpoint and merge cautions

The trainer's `training_main` saves whatever SAT/DeepSpeed checkpoint policy
is active; it does not document a universal adapter-only file format. Inspect
checkpoint contents and trainable keys before moving them to inference.
`checkpoints/README.md` only says to place model weights there, while
`assets/train_cli.txt` records historical checkpoint paths; neither proves
that a newly saved adapter is self-contained.

`LoraMixin.merge_lora()` exists but is not called by the training entry point.
It reconstructs ordinary linear weights from the base weight plus A/B deltas;
for NF4 it dequantizes via bitsandbytes and may move the result to CUDA. Merging
is therefore a separate, reversible conversion: copy the base checkpoint,
merge only into a new output, preserve the adapter and config, load the output,
and compare a small approved CUDA inference. Do not merge into the original
base, merge an incomplete checkpoint, or use a QLoRA merge path while the
bitsandbytes CUDA gate is unresolved.

For a checkpoint load failure, first compare model/adapter flags, rank,
`pre_seq_len`, layer range, SAT version, and expected parameter names. Stop on
missing trainable keys or unexpected full-model updates rather than using
`strict=False` to hide a mismatch.

---
name: checkpoint-export
description: "Inspect EasyR1 actor checkpoint directories and guide Hugging
  Face-format checkpoint export without reopening the source repository."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# checkpoint-export

Use this sub-skill when a task involves EasyR1 saved checkpoints, actor checkpoint preflight checks, or converting actor weights into Hugging Face format for inference or upload.

Do **not** use this sub-skill to create checkpoints by running training; route training launch, save-frequency, and resume setup questions to the EasyR1 training workflow guidance instead.

## Start here

- [references/checkpoint-export.md](references/checkpoint-export.md) explains the actor checkpoint layout, model-merger export workflow, LoRA merge requirements, generation config preservation, and upload caveats.
- [references/troubleshooting.md](references/troubleshooting.md) maps common checkpoint/export failures to concrete fixes, including incomplete shards, unsupported DTensor layouts, missing LoRA base models, and Hugging Face network/auth issues.
- [scripts/easyr1_checkpoint_inspector.py](scripts/easyr1_checkpoint_inspector.py) is a safe preflight inspector for a local actor checkpoint directory; it parses filenames and metadata JSON without loading model weights.

## Quick workflow

1. Identify the actor directory, normally `.../global_step_<step>/actor`, not the parent step directory and not the `huggingface/` child.
2. Run the bundled inspector before any expensive merge:

   ```bash
   python scripts/easyr1_checkpoint_inspector.py <actor_checkpoint_dir>
   python scripts/easyr1_checkpoint_inspector.py --json <actor_checkpoint_dir>
   ```

3. If preflight passes, use the export command shape and validation checklist in [references/checkpoint-export.md](references/checkpoint-export.md).
4. If preflight fails or the merger raises, diagnose with [references/troubleshooting.md](references/troubleshooting.md) before retrying.

Full EasyR1 training and end-to-end checkpoint generation require the CUDA/flash-attn/vLLM/Ray runtime; CPU/API checks and this inspector only prove checkpoint metadata and local file layout behavior.

---
name: dalle-training
description: "Train and resume DALLE-pytorch transformer workflows with
  image-text folders, WebDataset shards, VAE choices, tokenizers, and
  checkpoints."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# DALL-E transformer training

Use this sub-skill for `DALLE` transformer training, resume checkpoints, image-text folder/WebDataset preparation, tokenizer choices, model hyperparameters, and DALL-E checkpoint payloads.

## Read first

- `references/workflows.md` for API and command-style training flows.
- `references/data-formats.md` for image-text folder and WebDataset schemas.
- `references/checkpoints-and-tokenizers.md` for VAE/DALL-E checkpoint and tokenizer compatibility.
- `references/troubleshooting.md` for empty datasets, tokenization, CUDA, W&B, VAE mismatch, and resume failures.
- `scripts/validate_image_text_folder.py` before training on a folder dataset.
- `scripts/build_train_dalle_command.py` to produce a shell-safe training command template.

## Typical routes

| Request | Action |
| --- | --- |
| "Train DALL-E on my image/caption folder" | Run/describe `validate_image_text_folder.py`, choose VAE path or VAE wrapper, then build a command template. |
| "Use WebDataset" | Read `data-formats.md`, require `--wds image_key,caption_key`, and confirm tar/shard/URL/GCS source behavior. |
| "Resume training" | Inspect checkpoint keys; use `--dalle_path` and keep original model/tokenizer/VAE assumptions. |
| "Use a custom tokenizer" | Read tokenizer section; make sure `vocab_size` and padding id match checkpoint/training choices. |
| "Write DALLE API code" | Use `references/workflows.md` and root `references/api-reference.md` for constructor/forward details. |

## Minimal API pattern

```python
import torch
from dalle_pytorch import DiscreteVAE, DALLE

vae = DiscreteVAE(image_size=128, num_layers=3, num_tokens=8192, codebook_dim=512, hidden_dim=256)
dalle = DALLE(dim=512, vae=vae, num_text_tokens=10000, text_seq_len=256, depth=2, heads=8)
text = torch.randint(0, 10000, (4, 256))
images = torch.randn(4, 3, 128, 128)
loss = dalle(text, images, return_loss=True)
loss.backward()
```

## Boundary notes

- VAE pretraining and VAE-only checkpoints belong to `../vae-training/SKILL.md`.
- Generation and CLIP reranking belong to `../generation-and-ranking/SKILL.md`.
- DeepSpeed, Apex, Horovod, Docker, sparse attention backend installation, and CUDA wheel decisions belong to `../distributed-and-backends/SKILL.md`.

## Validation checklist

Before giving a training answer:

- data layout has been validated or failure points are explicit;
- VAE source (`--vae_path`, OpenAI VAE, or VQGAN) is chosen deliberately;
- tokenizer path/Chinese flag/truncation is compatible with `text_seq_len`;
- checkpoint path and resume semantics are clear;
- GPU/W&B/checkpoint side effects are approved before execution;
- optional distributed backend flags are not suggested unless backend availability is known.

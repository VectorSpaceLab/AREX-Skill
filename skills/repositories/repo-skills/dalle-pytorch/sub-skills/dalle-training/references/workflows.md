# DALL-E training workflows

## API training skeleton

Use the API when the user wants custom loops, CPU tests, or a pip-only workflow.

```python
import torch
from torch.optim import Adam
from dalle_pytorch import DiscreteVAE, DALLE

vae = DiscreteVAE(image_size=128, num_layers=3, num_tokens=8192, codebook_dim=512, hidden_dim=256)
dalle = DALLE(
    dim=512,
    vae=vae,
    num_text_tokens=10000,
    text_seq_len=256,
    depth=2,
    heads=8,
    dim_head=64,
    attn_types=("full",),
)
opt = Adam([p for p in dalle.parameters() if p.requires_grad], lr=3e-4)

text = torch.randint(0, 10000, (4, 256))
images = torch.randn(4, 3, 128, 128)
loss = dalle(text, images, return_loss=True, null_cond_prob=0.2)
loss.backward()
opt.step()
```

`null_cond_prob` trains classifier-free conditioning. Later generation can use `cond_scale > 1` to strengthen conditioning.

## Build a script-compatible training command

Use the command builder for the historical helper surface:

```bash
python scripts/build_train_dalle_command.py \
  --image-text-folder /data/image-text-data \
  --vae-path ./vae.pt \
  --epochs 20 \
  --batch-size 4 \
  --dim 512 \
  --depth 2 \
  --heads 8
```

The command builder prints a command and warnings; it does not run training.

## Image-text folder workflow

1. Validate pairing:

   ```bash
   python scripts/validate_image_text_folder.py /data/image-text-data --strict
   ```

2. Choose VAE source (`--vae_path`, `--taming`, or OpenAI VAE with legacy torch).
3. Choose tokenizer: default, YTTM/HuggingFace BPE path, or Chinese.
4. Build a command template.
5. Ask before running because training uses CUDA, W&B, and checkpoint writes.

## WebDataset workflow

1. Confirm key names, e.g. image key `jpg` and caption key `json`.
2. Confirm source type: tar file, shard folder, HTTP/HTTPS stream, or GCS path.
3. Use `--wds image_key,caption_key` and pass the source through `--image_text_folder`.
4. Treat remote streams as network side effects and shard folders as potentially large.

## Attention/model options

- `--attn_types full`: dense attention.
- `--attn_types axial_row,axial_col,conv_like`: package sparse-like attention over image tokens without DeepSpeed sparse attention.
- `--attn_types full,sparse`: includes DeepSpeed sparse attention and requires compatible DeepSpeed/Triton setup.
- `--reversible`: uses reversible layers to trade extra compute for lower memory.
- `--stable_softmax`: applies a stable softmax helper for large values.
- `--shift_tokens`, `--rotary_emb`, shared attention/FF ids, and input/output embedding sharing are construction-time choices; keep them compatible when resuming.

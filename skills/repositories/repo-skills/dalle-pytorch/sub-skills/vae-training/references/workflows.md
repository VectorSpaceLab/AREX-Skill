# VAE workflows

## Train a `DiscreteVAE` with the public API

Use this when the user has a pip install or wants a controlled custom training loop instead of a long helper script.

```python
import torch
from torch.optim import Adam
from dalle_pytorch import DiscreteVAE

vae = DiscreteVAE(
    image_size=128,
    num_layers=3,
    num_tokens=8192,
    codebook_dim=512,
    hidden_dim=256,
    num_resnet_blocks=2,
    smooth_l1_loss=False,
    kl_div_loss_weight=0.0,
)
opt = Adam(vae.parameters(), lr=1e-3)

images = torch.randn(8, 3, 128, 128)
loss, recons = vae(images, return_loss=True, return_recons=True)
loss.backward()
opt.step()
```

Core checks:

- `image_size` must be a power of two.
- `num_layers` determines token grid size: `image_size // (2 ** num_layers)` per side.
- `num_tokens` is the visual vocabulary size consumed by `DALLE`.
- Save `hparams` and `weights` if the VAE will be loaded by DALL-E training.

Example checkpoint payload:

```python
torch.save({
    "hparams": {
        "image_size": 128,
        "num_layers": 3,
        "num_tokens": 8192,
        "channels": 3,
        "codebook_dim": 512,
        "hidden_dim": 256,
        "num_resnet_blocks": 2,
    },
    "weights": vae.state_dict(),
}, "vae.pt")
```

## Build a training command template

The repo's historical helper accepted image-folder, model, optimizer, temperature, and distributed flags. Use the bundled builder to print a shell-safe template:

```bash
python scripts/build_train_vae_command.py \
  --image-folder /data/images \
  --image-size 128 \
  --epochs 20 \
  --batch-size 8 \
  --num-tokens 8192
```

The helper command writes `vae.pt` periodically and `vae-final.pt` at the end. It also logs to W&B on the root worker. Do not run it without user approval for GPU, checkpoint writes, and W&B side effects.

## Expected image folder

The VAE helper uses `torchvision.datasets.ImageFolder`. That means the image root must contain class subdirectories even if labels are irrelevant:

```text
image-root/
  class-or-dummy-name/
    img001.png
    img002.jpg
```

If the user has a flat folder, either create a dummy subfolder or use a custom API loop.

## Pretrained VAE choices

### OpenAI VAE

`OpenAIDiscreteVAE()` uses OpenAI encoder/decoder pickle files and exposes `image_size=256`, `num_layers=3`, and `num_tokens=8192`. The source asserts torch `<=1.10`, so modern torch environments fail before download. Use it only in a legacy environment or when the user's stack is already compatible.

### VQGAN VAE

`VQGanVAE(vqgan_model_path=None, vqgan_config_path=None)` uses Taming Transformers. With no paths it downloads default weights/configs. With explicit paths, both the model checkpoint and YAML config are required.

Typical DALL-E training choices:

- `--vae_path <vae.pt>`: use a trained `DiscreteVAE` checkpoint.
- no VAE path: use `OpenAIDiscreteVAE`; requires legacy torch compatibility and downloads.
- `--taming`: use `VQGanVAE`; default or explicit model/config paths.

## Temperature and codebook monitoring

The helper anneals Gumbel-softmax temperature from `--starting_temp` down to `--temp_min` using `--anneal_rate`. Watch reconstruction loss, hard reconstructions, and codebook usage. Codebook collapse means the model uses only a small subset of available visual tokens; consider training longer, changing temperature, adjusting hidden/codebook size, or improving data diversity.

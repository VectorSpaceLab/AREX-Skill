# Generation and public-API workflows

These workflows use only the public `dalle2_pytorch` package API. They assume package version 1.15.6 and require only the installed package plus user-provided checkpoints or data when relevant.

## 1. Safe install and import check

```bash
python -m pip install dalle2-pytorch
python scripts/check_dalle2_runtime.py --mode imports
```

The imports check verifies the package version when available, core public classes, the CLI module, and PyTorch availability. It does not instantiate CLIP adapters and therefore should not download model weights.

## 2. Tiny CPU forward-loss smoke test

Use this before attempting GPU training or real generation when you only need to know that public model constructors and synthetic forward losses work in the current environment.

```bash
python scripts/check_dalle2_runtime.py --mode tiny-forward
```

The check constructs tiny CPU objects using dimensions proven safe for inspection:

- `DiffusionPriorNetwork(dim=16, depth=1, dim_head=8, heads=2, num_timesteps=8, max_text_len=8)`.
- `DiffusionPrior(..., image_embed_dim=16, timesteps=8, sample_timesteps=2, condition_on_text_encodings=False)`.
- `Unet(dim=16, image_embed_dim=16, cond_dim=8, dim_mults=(1,), channels=3)`.
- `Decoder(..., image_size=16, timesteps=8, sample_timesteps=2, learned_variance=False)`.

It runs a prior scalar loss from precomputed text/image embeddings and a decoder scalar loss from synthetic images plus image embeddings. It intentionally does not call CLIP adapters, does not download weights, does not sample images, and does not train.

## 3. Tokenize prompts for `DALLE2` or prior sampling

The high-level `DALLE2` object accepts a string/list and tokenizes automatically. If you need explicit tokens, use the package tokenizer:

```python
from dalle2_pytorch.tokenizer import tokenizer

text = tokenizer.tokenize(["a corgi wearing sunglasses"], context_length=256)
```

Notes:

- `context_length` defaults to 256 for the package simple tokenizer.
- Long inputs raise a runtime error unless `truncate_text=True` is passed.
- OpenAI CLIP adapters use CLIP's own context length internally; make prompt length compatible with the CLIP model used during training.
- Some data loaders use `clip.tokenize` from `clip-anytorch`, but high-level `DALLE2.forward` uses the package tokenizer for raw strings.

## 4. Build a prior for precomputed embeddings

For smoke tests or embedding-dataset training where CLIP is not attached:

```python
import torch
from dalle2_pytorch import DiffusionPriorNetwork, DiffusionPrior

net = DiffusionPriorNetwork(
    dim=768,
    depth=24,
    dim_head=64,
    heads=32,
    num_timesteps=1000,
)

prior = DiffusionPrior(
    net=net,
    image_embed_dim=768,
    timesteps=1000,
    cond_drop_prob=0.1,
    condition_on_text_encodings=False,
)

text_embed = torch.randn(4, 768)
image_embed = torch.randn(4, 768)
loss = prior(text_embed=text_embed, image_embed=image_embed)
```

This route cannot high-level sample from raw prompt tokens unless a CLIP adapter is attached, because `DiffusionPrior.sample` calls `self.clip.embed_text(...)`.

## 5. Build a prior with OpenAI CLIP or OpenCLIP

Use a CLIP adapter when the prior should tokenize/encode prompts and score sampled image embeddings by text-image similarity.

```python
from dalle2_pytorch import DiffusionPriorNetwork, DiffusionPrior, OpenAIClipAdapter

clip = OpenAIClipAdapter("ViT-L/14")
net = DiffusionPriorNetwork(dim=768, depth=24, dim_head=64, heads=32, num_timesteps=1000)
prior = DiffusionPrior(
    net=net,
    clip=clip,
    image_embed_dim=768,
    timesteps=1000,
    cond_drop_prob=0.1,
    condition_on_text_encodings=True,
)
```

OpenCLIP variant:

```python
from dalle2_pytorch import OpenClipAdapter
clip = OpenClipAdapter(name="ViT-B/32", pretrained="laion400m_e32")
```

Operational cautions:

- Adapter construction may download weights through `clip-anytorch` or `open-clip-torch`; use a cache or network-enabled environment.
- The adapter latent dimension must match `DiffusionPriorNetwork.dim` and `DiffusionPrior.image_embed_dim`.
- `cond_scale` above `1` only works if the prior was trained with conditional dropout.

## 6. Build a single-stage decoder

```python
import torch
from dalle2_pytorch import Unet, Decoder

unet = Unet(
    dim=128,
    image_embed_dim=512,
    cond_dim=128,
    channels=3,
    dim_mults=(1, 2, 4, 8),
)

decoder = Decoder(
    unet=unet,
    image_size=256,
    timesteps=1000,
    image_cond_drop_prob=0.1,
    text_cond_drop_prob=0.5,
)

image_embed = torch.randn(1, 512)
images = decoder.sample(image_embed=image_embed, cond_scale=2.0)
```

Training-loss call with precomputed embeddings:

```python
batch_images = torch.rand(4, 3, 256, 256)
batch_embeds = torch.randn(4, 512)
loss = decoder(batch_images, image_embed=batch_embeds)
```

If you pass raw `text` or need `text_encodings`, the decoder must have a CLIP adapter and a Unet configured with `cond_on_text_encodings=True` plus a compatible `text_embed_dim`.

## 7. Build a cascaded decoder

Cascaded decoders use multiple Unets ordered from low resolution to high resolution. Provide one image size per Unet.

```python
from dalle2_pytorch import Unet, Decoder

unet1 = Unet(dim=64, image_embed_dim=512, cond_dim=128, dim_mults=(1, 2, 4))
unet2 = Unet(dim=64, image_embed_dim=512, cond_dim=128, dim_mults=(1, 2, 4))

decoder = Decoder(
    unet=(unet1, unet2),
    image_sizes=(64, 256),
    timesteps=1000,
    sample_timesteps=(250, 50),
    image_cond_drop_prob=0.1,
    text_cond_drop_prob=0.5,
)
```

Rules:

- `len(unets) == len(image_sizes)`.
- The first Unet is the base image generator. Later Unets are cast for low-resolution conditioning and super-resolution.
- `cond_scale` may be a scalar or tuple/list with one value per Unet.
- If sampling from a later Unet only (`start_at_unet_number > 1`), provide the already generated lower-resolution `image`.

## 8. Chain prior and decoder with `DALLE2`

```python
from dalle2_pytorch import DALLE2

dalle2 = DALLE2(prior=prior, decoder=decoder, prior_num_samples=2)
image = dalle2(
    "a corgi wearing sunglasses",
    prior_cond_scale=1.0,
    cond_scale=2.0,
    return_pil_images=False,
)
```

- `prior_num_samples` controls how many candidate prior embeddings are sampled per prompt.
- `prior_cond_scale` affects prior classifier-free guidance.
- `cond_scale` affects decoder classifier-free guidance.
- For a single prompt, the return is one image tensor (or one PIL image if requested). For a list of prompts, the return is a batch/list.
- Meaningful outputs require trained prior and decoder checkpoints with architectures matching the instantiated objects.

## 9. Decoder inpainting

`Decoder.sample` supports inpainting by passing both an image and a boolean mask:

```python
import torch

image_embed = torch.randn(1, 512)
inpaint_image = torch.rand(1, 3, 256, 256)
inpaint_mask = torch.zeros(1, 256, 256, dtype=torch.bool)
inpaint_mask[:, 64:192, 64:192] = True

images = decoder.sample(
    image_embed=image_embed,
    cond_scale=2.0,
    inpaint_image=inpaint_image,
    inpaint_mask=inpaint_mask,
    inpaint_resample_times=5,
)
```

Mask semantics are important: `True` means keep the corresponding regions from `inpaint_image`; `False` means let the decoder synthesize/repaint those pixels. The mask must have shape `[batch, height, width]`, not `[batch, 1, height, width]`. The inpaint image should have shape `[batch, channels, height, width]`.

## 10. The installed `dream` command

The package installs two console entry points: `dalle2_pytorch` and `dream`. The `dream` command is the generation entry point.

```bash
dream --help
dream --model /path/to/trained_dalle2_checkpoint.pt --cond_scale 2 "a corgi wearing sunglasses"
```

Behavior:

- `--model` defaults to `./dalle2.pt`, but a real trained model file is required.
- The command loads a checkpoint with `torch.load`, reconstructs `DiffusionPrior(**init_params.prior)`, `Decoder(**init_params.decoder)`, chains `DALLE2(prior, decoder)`, and calls `load_state_dict(model_params)`.
- It writes a PNG in the current working directory using a slug derived from the prompt, for example `a_corgi_wearing_sunglasses.png`.
- `--cond_scale` is declared by Click with default integer `2`; pass integer-looking values for best CLI compatibility.
- The checkpoint must contain the package-expected keys `version`, `init_params.prior`, `init_params.decoder`, and `model_params`. Trainer checkpoints may have different wrappers; route checkpoint-conversion or trainer save/load issues to `training-and-configs`.

## CPU and GPU distinctions

- CPU: imports, CLI help, tokenizer checks, config parsing, tiny synthetic forward-loss tests, and small shape debugging.
- GPU recommended: real CLIP encoding, prior sampling over many timesteps, decoder image sampling, inpainting at useful resolutions, and all training.
- Network/cache required in many real workflows: first construction of `OpenAIClipAdapter` / `OpenClipAdapter`, metric downloads, and remote checkpoint/data access.

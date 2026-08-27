# Generation workflows

These recipes are intentionally tiny. They validate shapes, route behavior, and common setup details without pretrained weights or large tensors.

## Unconditional generator

Tiny CPU smoke:

```py
import torch
from audio_diffusion_pytorch import DiffusionModel, UNetV0, VDiffusion, VSampler

model = DiffusionModel(
    net_t=UNetV0,
    in_channels=1,
    channels=[4, 4],
    factors=[1, 2],
    items=[1, 1],
    attentions=[0, 0],
    resnet_groups=1,
    diffusion_t=VDiffusion,
    sampler_t=VSampler,
)

audio = torch.randn(1, 1, 16)
loss = model(audio)
noise = torch.randn_like(audio)
sample = model.sample(noise, num_steps=2)
```

Validation signals:
- `loss.ndim == 0`.
- `sample.shape == audio.shape == (1, 1, 16)`.
- No pretrained weights or external data are required.

## Text-conditioned generator

Constructor-safe setup:

```py
from audio_diffusion_pytorch import DiffusionModel, UNetV0, VDiffusion, VSampler

model = DiffusionModel(
    net_t=UNetV0,
    in_channels=1,
    channels=[8, 8],
    factors=[1, 2],
    items=[1, 1],
    attentions=[0, 0],
    cross_attentions=[0, 1],
    attention_heads=1,
    attention_features=8,
    resnet_groups=1,
    use_text_conditioning=True,
    use_embedding_cfg=True,
    embedding_max_length=64,
    embedding_features=768,
    diffusion_t=VDiffusion,
    sampler_t=VSampler,
)
```

Notes:
- `transformers` must be available for the text-conditioning path.
- The default text path is built around T5-base embeddings, so `embedding_features=768` is required.
- If any `cross_attentions` entry is nonzero, provide `attention_heads` and `attention_features` as part of the tiny constructor.
- The first build can consult Hugging Face cache state and may touch the network if the model is not already cached.
- If you want an end-to-end smoke, pass `text=["short prompt"]` and keep the list length equal to the batch size.

Validation signals:
- Constructor succeeds with text-conditioning flags enabled.
- No list-length or embedding-dimension assertions are raised.
- Any optional forward/sample run uses batch-aligned text inputs and can be skipped when offline.

## Inpainting

Tiny CPU smoke:

```py
import torch
from audio_diffusion_pytorch import UNetV0, VInpainter

net = UNetV0(
    dim=1,
    in_channels=1,
    channels=[4, 4],
    factors=[1, 2],
    items=[1, 1],
    attentions=[0, 0],
    resnet_groups=1,
)

inpainter = VInpainter(net=net)
source = torch.randn(1, 1, 16)
mask = torch.zeros_like(source, dtype=torch.bool)
mask[..., :8] = True
output = inpainter(source=source, mask=mask, num_steps=2, num_resamples=1)
```

Validation signals:
- `mask.dtype is torch.bool` and `mask.shape == source.shape`.
- `True` entries keep the source region; `False` entries are generated.
- `output.shape == source.shape == (1, 1, 16)`.

## DiffusionAR expert note

Use this only when an expert user explicitly asks for autoregressive chunked diffusion.

- Pick a length divisible by `num_splits`.
- Keep `use_time_conditioning=False` and `use_modulation=False` through the wrapper defaults.
- Treat the route as experimental and under-documented compared with the main generator workflow.
- If the user is really asking for upsampling, vocoding, or autoencoding, route to `../conditioning/` instead.

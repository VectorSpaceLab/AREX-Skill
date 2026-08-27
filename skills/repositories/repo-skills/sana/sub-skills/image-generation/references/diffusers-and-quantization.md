# Diffusers and Quantized Sana Image Generation

This reference covers Python snippets for Diffusers `SanaPipeline`,
`SanaPAGPipeline`, `SanaSprintPipeline`, 2K/4K VAE tiling, 8-bit bitsandbytes,
and 4-bit SVDQuant/Nunchaku image inference.

## Diffusers Baseline: SanaPipeline

Use this for ordinary text-to-image generation from a Diffusers model id.

```python
import torch
from diffusers import SanaPipeline

model_id = "Efficient-Large-Model/SANA1.5_1.6B_1024px_diffusers"
pipe = SanaPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
)
pipe.to("cuda")

# Keep the VAE and text encoder in bf16 or fp32 for reliable Sana outputs.
pipe.vae.to(torch.bfloat16)
pipe.text_encoder.to(torch.bfloat16)

prompt = 'a cyberpunk cat with a neon sign that says "Sana"'
image = pipe(
    prompt=prompt,
    height=1024,
    width=1024,
    guidance_scale=4.5,
    num_inference_steps=20,
    generator=torch.Generator(device="cuda").manual_seed(42),
)[0][0]
image.save("sana.png")
```

Validation after running:

```python
from PIL import Image
img = Image.open("sana.png")
assert img.size == (1024, 1024)
```

For fp16 models such as `Efficient-Large-Model/Sana_1600M_1024px_diffusers`,
load the transformer weights with `variant="fp16"` and
`torch_dtype=torch.float16`, then explicitly move `pipe.vae` and
`pipe.text_encoder` to `torch.bfloat16` or `torch.float32`.

## PAG Guidance: SanaPAGPipeline

Use PAG when a user asks for PAG guidance or when tuning prompt adherence with
linear-attention Sana models.

```python
import torch
from diffusers import SanaPAGPipeline

pipe = SanaPAGPipeline.from_pretrained(
    "Efficient-Large-Model/SANA1.5_1.6B_1024px_diffusers",
    torch_dtype=torch.bfloat16,
    pag_applied_layers="transformer_blocks.8",
)
pipe.to("cuda")
pipe.text_encoder.to(torch.bfloat16)
pipe.vae.to(torch.bfloat16)

image = pipe(
    prompt='a cyberpunk cat with a neon sign that says "Sana"',
    guidance_scale=5.0,
    pag_scale=2.0,
    num_inference_steps=20,
    generator=torch.Generator(device="cuda").manual_seed(42),
)[0][0]
image.save("sana_pag.png")
```

Notes:

- PAG only applies as intended when the model uses linear attention and
  `pag_scale > 1.0`.
- Native code falls back to classifier-free guidance if those conditions are not
  met. Treat unexpected “no PAG effect” as a configuration issue before blaming
  the checkpoint.

## Sprint: SanaSprintPipeline

Use Sprint for one/few-step 1024px image generation.

```python
import torch
from diffusers import SanaSprintPipeline

pipe = SanaSprintPipeline.from_pretrained(
    "Efficient-Large-Model/Sana_Sprint_1.6B_1024px_diffusers",
    torch_dtype=torch.bfloat16,
)
pipe.to("cuda:0")

prompt = "a tiny astronaut hatching from an egg on the moon"
image = pipe(
    prompt=prompt,
    num_inference_steps=2,
    generator=torch.Generator(device="cuda").manual_seed(42),
).images[0]
image.save("sana_sprint.png")
```

Optional VAE swap for speed:

```python
from diffusers import AutoencoderDC
vae = AutoencoderDC.from_pretrained("mit-han-lab/dc-ae-lite-f32c32-sana-1.1-diffusers")
pipe.vae = vae.to("cuda", dtype=torch.bfloat16)
```

Compiling the VAE can reduce decode latency but requires a recent PyTorch and
may increase first-run compile time. Treat `torch.compile` failures as optional
optimization failures, not generation blockers.

## 2K and 4K Diffusers Generation

Use the bf16 2K/4K model IDs and plan for much higher memory than 1024px.
For 4K, enable VAE tiling before the call.

```python
import torch
from diffusers import SanaPipeline

pipe = SanaPipeline.from_pretrained(
    "Efficient-Large-Model/Sana_1600M_4Kpx_BF16_diffusers",
    variant="bf16",
    torch_dtype=torch.bfloat16,
)
pipe.to("cuda")
pipe.vae.to(torch.bfloat16)
pipe.text_encoder.to(torch.bfloat16)

# Avoid common 4096x4096 VAE decode OOM. Adjust tile sizes if still OOM.
if getattr(pipe.transformer.config, "sample_size", None) == 128:
    pipe.vae.enable_tiling(
        tile_sample_min_height=1024,
        tile_sample_min_width=1024,
        tile_sample_stride_height=896,
        tile_sample_stride_width=896,
    )

image = pipe(
    prompt='a cyberpunk cat with a neon sign that says "Sana"',
    height=4096,
    width=4096,
    guidance_scale=5.0,
    num_inference_steps=20,
    generator=torch.Generator(device="cuda").manual_seed(42),
)[0][0]
image.save("sana_4k.png")
```

If 4K still fails, reduce batch size and number of images first; then reduce
resolution, lower steps, use a 2K model, or move to quantized inference. Do not
fall back to CPU for 4K generation.

## 8-bit Diffusers Components

Use 8-bit quantization when memory pressure is primarily in the text encoder or
transformer and the bitsandbytes stack is installed.

```python
import torch
from diffusers import BitsAndBytesConfig as DiffusersBitsAndBytesConfig
from diffusers import SanaPipeline, SanaTransformer2DModel
from transformers import AutoModel, BitsAndBytesConfig as TransformersBitsAndBytesConfig

model_id = "Efficient-Large-Model/Sana_1600M_1024px_diffusers"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

text_encoder_8bit = AutoModel.from_pretrained(
    model_id,
    subfolder="text_encoder",
    quantization_config=TransformersBitsAndBytesConfig(load_in_8bit=True),
    torch_dtype=torch.float16,
)
transformer_8bit = SanaTransformer2DModel.from_pretrained(
    model_id,
    subfolder="transformer",
    quantization_config=DiffusersBitsAndBytesConfig(load_in_8bit=True),
    torch_dtype=torch.float16,
)

pipe = SanaPipeline.from_pretrained(
    model_id,
    text_encoder=text_encoder_8bit,
    transformer=transformer_8bit,
    torch_dtype=torch.float16,
    device_map="balanced",
)
pipe.to(device)
image = pipe("a tiny astronaut hatching from an egg on the moon").images[0]
image.save("sana_8bit.png")
```

8-bit caveats:

- It requires compatible bitsandbytes, transformers, diffusers, CUDA, and GPU
  support.
- Quality and speed can differ from bf16/fp16. Validate output visually and
  check image size and mode after the first run.
- The source dtype recommendation for plain Sana still applies: avoid blindly
  downcasting every component to fp16.

## 4-bit SVDQuant/Nunchaku Sana

Use this only when the Nunchaku/SVDQuant engine is installed and CUDA is
available. It is not enabled by a Diffusers `load_in_4bit` flag.

```python
import torch
from diffusers import SanaPipeline
from nunchaku.models.transformer_sana import NunchakuSanaTransformer2DModel

transformer = NunchakuSanaTransformer2DModel.from_pretrained(
    "mit-han-lab/svdq-int4-sana-1600m"
)
pipe = SanaPipeline.from_pretrained(
    "Efficient-Large-Model/Sana_1600M_1024px_BF16_diffusers",
    transformer=transformer,
    variant="bf16",
    torch_dtype=torch.bfloat16,
).to("cuda")
pipe.text_encoder.to(torch.bfloat16)
pipe.vae.to(torch.bfloat16)

image = pipe(
    prompt="A cute panda eating bamboo, ink drawing style",
    height=1024,
    width=1024,
    guidance_scale=4.5,
    num_inference_steps=20,
    generator=torch.Generator(device="cuda").manual_seed(42),
).images[0]
image.save("sana_4bit.png")
```

4-bit caveats:

- Nunchaku wheels/builds are backend-sensitive. Verify installation before
  promising a low-VRAM run.
- Source guidance shows 4-bit image inference below 8 GB VRAM, but that is a
  workflow expectation, not a guarantee for every GPU, driver, resolution, or
  batch size.
- For `SanaPAGPipeline` with Nunchaku, use the Nunchaku PAG-specific example
  pattern for the installed engine version rather than assuming the plain
  `SanaPipeline` transformer replacement is enough.

## Generator Seeding and Output Checks

- Use `torch.Generator(device="cuda").manual_seed(seed)` after moving the
  pipeline to CUDA for reproducible GPU noise.
- Reuse the same seed, prompt, height, width, steps, guidance, and model dtype
  when comparing variants.
- After every smoke run, assert that the saved image exists, opens with PIL,
  has the requested dimensions, and is not a zero-byte file.

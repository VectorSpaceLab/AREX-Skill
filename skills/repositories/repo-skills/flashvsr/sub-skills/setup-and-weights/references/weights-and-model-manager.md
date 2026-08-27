# Weights and ModelManager reference

## Hugging Face Git LFS bundles

The README documents two official repositories:

| Version | Hugging Face repository | Application model-directory label |
|---|---|---|
| v1 | `JunhaoZhuang/FlashVSR` | `FlashVSR/` |
| v1.1 | `JunhaoZhuang/FlashVSR-v1.1` | `FlashVSR-v1.1/` |

Acquire exactly one version-atomic directory in an application-owned model
root. The official sources are `JunhaoZhuang/FlashVSR` for v1 and
`JunhaoZhuang/FlashVSR-v1.1` for v1.1:

```bash
git lfs install
git lfs clone https://huggingface.co/JunhaoZhuang/FlashVSR <MODEL_DIR>       # v1
git lfs clone https://huggingface.co/JunhaoZhuang/FlashVSR-v1.1 <MODEL_DIR>   # v1.1
```

The five-file completeness contract is:

```text
diffusion_pytorch_model_streaming_dmd.safetensors
Wan2.1_VAE.pth
LQ_proj_in.ckpt
TCDecoder.ckpt
README.md
```

The four tensor files are the weights; `README.md` is the upstream manifest
that appears with them in the documented model directory. A Git LFS pointer
file is not a downloaded checkpoint. Check the directory without network use:

```bash
python <skill-root>/sub-skills/setup-and-weights/scripts/check_weights.py \
  <MODEL_DIR> --version v1.1
```

All five files must be regular, non-empty files, and the four tensor files must
not begin with the Git LFS pointer signature. The checker never invokes Git,
Hugging Face, ModelScope, or a downloader.

## CPU-first manager construction

`ModelManager` defaults to CUDA, so set both `torch_dtype` and `device` for the
initial load. Its `load_models()` calls the detector chain from
`diffsynth/configs/model_config.py`; for FlashVSR the expected names are
`wan_video_dit` and `wan_video_vae`.

```python
from pathlib import Path
import torch
from diffsynth import ModelManager

model_dir = Path("<MODEL_DIR>")
mm = ModelManager(torch_dtype=torch.bfloat16, device="cpu")
mm.load_models([
    str(model_dir / "diffusion_pytorch_model_streaming_dmd.safetensors"),
    str(model_dir / "Wan2.1_VAE.pth"),
])
```

For full inference, load both files before:

```python
pipe = FlashVSRFullPipeline.from_model_manager(mm, device="cuda")
assert pipe.denoising_model() is not None
assert pipe.vae is not None
```

For tiny or tiny-long, load the DiT file and construct the selected pipeline.
Those pipelines use the conditional decoder path and do not require the VAE
file for decoding. The five-file gate is still useful because it detects an
incomplete upstream bundle before route selection.

If the manager prints `We cannot detect the model type`, stop. A missing model
or `fetch_model(...) is None` is also a setup failure. Common causes are an LFS
pointer, a mixed-version file, a truncated checkpoint, or a detector mismatch
from using a package/environment other than the pinned one.

## Projection, decoder, and context injection

The official recipes use support modules for the projection and tiny decoder.
They are not stable public exports of `diffsynth`; package their implementations
into an application-owned support module for a checkout-independent deployment.

### LQ projection

Create the projection with `in_dim=3`, `out_dim=1536`, and `layer_num=1`, then
load the local checkpoint on CPU with `strict=True` before moving it to CUDA:

```python
projection = ProjectionClass(in_dim=3, out_dim=1536, layer_num=1).to(
    "cuda", dtype=torch.bfloat16
)
state = torch.load(model_dir / "LQ_proj_in.ckpt",
                   map_location="cpu", weights_only=True)
projection.load_state_dict(state, strict=True)
pipe.denoising_model().LQ_proj_in = projection
```

Use `Buffer_LQ4x_Proj` only for v1. Use `Causal_LQ4x_Proj` only for v1.1.
The classes have streaming cache state; do not mix a class and checkpoint
across versions.

### Tiny conditional decoder

For tiny and tiny-long only:

```python
pipe.TCDecoder = build_tcdecoder(
    new_channels=[512, 256, 128, 128],
    new_latent_channels=16 + 768,
)
tc_state = torch.load(model_dir / "TCDecoder.ckpt",
                       map_location="cpu", weights_only=True)
load_result = pipe.TCDecoder.load_state_dict(tc_state, strict=False)
print(load_result)
```

`strict=False` is the documented example behavior, not permission to ignore a
large or unexpected mismatch. Preserve the returned missing/unexpected key
report for review.

### Final transfer and cross-attention cache

```python
pipe.to("cuda")
pipe.enable_vram_management(num_persistent_param_in_dit=None)
context = torch.load("<POSITIVE_CONTEXT_PATH>",
                     map_location="cpu", weights_only=True)
assert tuple(context.shape) == (1, 512, 4096)
pipe.init_cross_kv(context_tensor=context)
pipe.load_models_to_device(["dit", "vae"])
```

The context is an application runtime asset, not a sixth Hugging Face model
file. Initialize the cross-attention cache once before streaming inference.
For full decode-only runs, the examples additionally set
`pipe.vae.model.encoder = None` and `pipe.vae.model.conv1 = None` to reduce
memory; retain them only if the VAE will not encode later.

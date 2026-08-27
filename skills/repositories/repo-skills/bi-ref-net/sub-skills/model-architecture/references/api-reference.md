# BiRefNet model API reference

This reference distills the model-facing APIs and loading patterns that future agents need without reopening the source checkout.

## Construction and loading surfaces

| Surface | Verified signature / form | Use it for | Important implications |
|---|---|---|---|
| `Config()` | `Config() -> None` | Reading the active model, task, size, precision, backbone, decoder, and path defaults that `BiRefNet` instantiates internally. | `BiRefNet.__init__` creates a fresh `Config`; source-checkout workflows that edit `config.py` affect all new model instances. Full configuration and data-routing details belong in `../configuration-and-data/SKILL.md`. |
| `BiRefNet` | `BiRefNet(bb_pretrained=True)` | Constructing the source-code model class directly. | `bb_pretrained=True` attempts to initialize/load backbone weights. Use `False` when loading a complete BiRefNet checkpoint or when probing architecture without downloads/backbone files. |
| Hugging Face hub mixin | `BiRefNet.from_pretrained(model_id_or_path, ...)` | Loading a BiRefNet class that inherits `PyTorchModelHubMixin`. | Requires `huggingface_hub` and local/remote model assets. It uses the source class and current code, so the effective `Config.bb` and architecture flags must match the weights. |
| Transformers auto model | `AutoModelForImageSegmentation.from_pretrained(model_id, trust_remote_code=True)` | One-line Hugging Face loading when the `transformers` integration is desired. | Requires `transformers`; `trust_remote_code=True` executes model code supplied by the model repository/cache. Missing `transformers` is separate from missing `huggingface_hub`. |
| Local `.pth` checkpoint | `BiRefNet(bb_pretrained=False)` + `torch.load(..., weights_only=True)` + `check_state_dict(...)` + `load_state_dict(...)` | Loading release or training checkpoints from disk. | This is the safest local-weight path because full-model checkpoints already contain backbone parameters and should not require separate backbone pretraining files. |

## Minimal local checkpoint recipe

```python
import torch
from models.birefnet import BiRefNet
from utils import check_state_dict

model = BiRefNet(bb_pretrained=False)
state_dict = torch.load("BiRefNet-weights.pth", map_location="cpu", weights_only=True)
state_dict = check_state_dict(state_dict)
model.load_state_dict(state_dict)
model.eval()
```

If `load_state_dict` reports many missing or unexpected keys after prefix cleanup, suspect an architecture/config mismatch rather than only a checkpoint-format problem. Check `config.bb`, multi-scale input, decoder attention, decoder block, and supervision flags in [backbones-and-architecture.md](backbones-and-architecture.md).

## Hugging Face loading choices

```python
# Source-code class path. Requires huggingface_hub and BiRefNet source class.
from models.birefnet import BiRefNet
model = BiRefNet.from_pretrained("zhengpeng7/BiRefNet")

# Transformers auto path. Requires transformers and trusted remote code.
from transformers import AutoModelForImageSegmentation
model = AutoModelForImageSegmentation.from_pretrained(
    "zhengpeng7/BiRefNet",
    trust_remote_code=True,
)
```

Known public model IDs include the standard BiRefNet family and variants such as portrait, legacy, DIS5K, HRSOD, COD, and lite/tiny releases. Treat the model ID as a weight/config contract: a lite/tiny checkpoint must be paired with the tiny Swin config key used by the current code (`swin_v1_t`), while standard large checkpoints use the large Swin key (`swin_v1_l`).

## Forward-output conventions

- In evaluation mode, `model(input_tensor)` returns a list of scaled prediction tensors. The final high-resolution mask logit is conventionally `model(input_tensor)[-1]`; image workflows apply `.sigmoid()` and resize back to the original image.
- In training mode, the top-level return includes decoder predictions plus classification-list structure: `[scaled_preds, class_preds_lst]`. When gradient-reference output is active, the decoder returns gradient prediction/label lists together with scaled masks. Training and loss handling belong in `../training-and-evaluation/SKILL.md`.
- Inputs are RGB tensors normalized like ImageNet in the notebooks: resize to the configured resolution (default `1024x1024`), convert to tensor, and normalize mean `[0.485, 0.456, 0.406]`, std `[0.229, 0.224, 0.225]`. Full image-directory inference is owned by `../inference-and-postprocessing/SKILL.md`.

## Patch helper APIs

`image2patches(image, grid_h=2, grid_w=2, patch_ref=None, transformation="b c (hg h) (wg w) -> (b hg wg) c h w")`

- Splits a tensor with shape `(B, C, H, W)` into a patch batch using `einops.rearrange`.
- With the default transformation, the output shape is `(B * grid_h * grid_w, C, H / grid_h, W / grid_w)`.
- If `patch_ref` is supplied, `grid_h` and `grid_w` are derived as `image.shape[-2] // patch_ref.shape[-2]` and `image.shape[-1] // patch_ref.shape[-1]`.
- The decoder also uses a channel-concatenating transformation, for example `"b c (hg h) (wg w) -> b (c hg wg) h w"`, to feed split image context into decoder input blocks.

`patches2image(patches, grid_h=2, grid_w=2, patch_ref=None, transformation="(b hg wg) c h w -> b c (hg h) (wg w)")`

- Reassembles a patch batch back into an image tensor.
- With a compatible default `image2patches` call, `patches2image(image2patches(x, grid_h, grid_w), grid_h, grid_w)` should recover `x` exactly for tensor layouts that divide evenly.
- If `patch_ref` is supplied, the grid is derived from the reference output size and patch size.

## `check_state_dict` behavior

`check_state_dict(state_dict, unwanted_prefixes=['module.', '_orig_mod.'])`

- Cleans state-dict keys in place and returns the same dictionary object.
- Handles common `DistributedDataParallel` and `torch.compile` prefixes: `module.` and `_orig_mod.`.
- The implementation walks the unwanted-prefix list in order at the current key offset. A key such as `module._orig_mod.decoder.weight` becomes `decoder.weight`; a key with only `_orig_mod.` becomes the unprefixed key.
- Use it before `model.load_state_dict(...)` for checkpoints saved from DDP, Accelerate-wrapped, or compiled models.
- If keys still mismatch afterward, verify that the checkpoint was produced with the same architecture flags and backbone rather than repeatedly stripping arbitrary prefixes.

## Safe probe script

Run the bundled probe from any working directory. It does not add the current working directory to `sys.path`; it imports source code only when `--repo-root` is explicitly supplied.

```bash
python scripts/birefnet_model_probe.py
python scripts/birefnet_model_probe.py --repo-root /path/to/BiRefNet
python scripts/birefnet_model_probe.py --repo-root /path/to/BiRefNet --construct-model
```

The default run performs local prefix-cleanup and patch-roundtrip checks without downloading model or backbone weights. `--construct-model` instantiates `BiRefNet(bb_pretrained=False)` only when a source repo root is provided.

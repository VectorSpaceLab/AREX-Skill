# Model architecture troubleshooting

## `BiRefNet(bb_pretrained=True)` cannot find backbone weights

Symptoms:

- `FileNotFoundError` from `torch.load(config.weights[model_name], ...)`.
- `Weights are not successfully loaded. Check the state dict of weights file.` from the backbone loader.
- Construction fails later because the backbone object is `None`.

Causes and fixes:

- `bb_pretrained=True` asks the backbone builder to load separate backbone pretraining files for Swin/PVT/DINO or torchvision weights for VGG/ResNet. Supply the expected backbone checkpoint file, use the relevant torchvision cache, or construct with `bb_pretrained=False`.
- If the next step is loading a full BiRefNet checkpoint, prefer `BiRefNet(bb_pretrained=False)`. Full checkpoints already contain backbone weights.
- Confirm `config.bb` first. A Swin-L checkpoint with `config.bb='swin_v1_t'` or a lite/tiny checkpoint with `config.bb='swin_v1_l'` will not be fixed by downloading more backbone files.

## Lite/tiny weights fail with wrong `config.bb`

Symptoms:

- Large groups of `size mismatch` errors in backbone and decoder layers.
- Unexpected/missing keys after a successful `check_state_dict` cleanup.
- ONNX tutorial or model-zoo text refers to `swin_v1_tiny`, but the current source config does not accept that exact string.

Fix:

- Use `config.bb='swin_v1_t'` for current-code Swin tiny/lite weights.
- Use `config.bb='swin_v1_l'` for standard large model-zoo weights.
- Recheck other architecture flags if the backbone is right but mismatches remain: `mul_scl_ipt`, `dec_att`, `dec_blk`, `dec_ipt`, `dec_ipt_split`, `cxt_num`, `squeeze_block`, `ms_supervision`, and `out_ref`.

## DDP or compiled checkpoint key mismatch

Symptoms:

- `load_state_dict` reports keys starting with `module.` or `_orig_mod.`.
- A checkpoint saved from DistributedDataParallel, Accelerate wrapping, or `torch.compile` does not load into a plain model.

Fix:

```python
from utils import check_state_dict
state_dict = check_state_dict(state_dict)
model.load_state_dict(state_dict)
```

Notes:

- `check_state_dict` strips the configured unwanted prefixes in place and returns the dictionary.
- It handles common nested `module._orig_mod.` keys.
- If errors remain after cleanup, stop and verify architecture compatibility rather than stripping arbitrary substrings from every key.

## Hugging Face loading errors

### `AutoModelForImageSegmentation` is missing

Symptoms:

- `ModuleNotFoundError: No module named 'transformers'`.
- `ImportError` when using `from transformers import AutoModelForImageSegmentation`.

Fix:

- Install `transformers` for the auto-model path, or use the source class path with `BiRefNet.from_pretrained(...)` if `huggingface_hub` and the BiRefNet source class are available.
- Keep `trust_remote_code=True` only when you intend to execute model code from the Hugging Face model repository or cache.

### `BiRefNet.from_pretrained` fails

Symptoms:

- Missing `huggingface_hub`.
- Network/cache errors for model files.
- Key/shape mismatches after the model is fetched.

Fix:

- Confirm `huggingface_hub` is installed.
- Work from an already-cached model ID or provide an explicit local model directory when offline.
- Match the local source architecture to the model variant. In particular, lite/tiny variants need `swin_v1_t` in the current code.

## ONNX deform-conv export failure

Symptoms:

- Export errors mention `deform_conv2d`, `torchvision.ops`, symbolic registration, unsupported operator, or unknown custom op.
- The model exports only after disabling or changing `dec_att`, but the exported output no longer matches the checkpoint.

Fix:

- The default `dec_att='ASPPDeformable'` uses deformable convolution and needs a registered deform-conv ONNX exporter.
- Use an exporter version tested against the installed PyTorch/torchvision/ONNX stack.
- Do not change `dec_att` for an existing checkpoint unless the checkpoint was trained with that architecture.
- See [onnx-and-export-notes.md](onnx-and-export-notes.md) for the source conversion flow and memory/provider cautions.

## ONNX provider, opset, or package failure

Symptoms:

- `onnxruntime` cannot create a session with `CUDAExecutionProvider`.
- Runtime silently uses CPU or is much slower than expected.
- Export fails around opset or ONNXScript symbols.

Fix:

- Install `onnx`, `onnxscript`, and either `onnxruntime` or `onnxruntime-gpu` as appropriate.
- Use a provider that exists in `onnxruntime.get_available_providers()`.
- Check the compatibility among `onnxruntime-gpu`, CUDA, cuDNN, PyTorch, and torchvision.
- Start from `opset_version=17`, the opset used by the source tutorial, unless a downstream runtime requires and validates another opset.

## CPU/GPU memory failures

Symptoms:

- Process is killed during model construction, export, or first forward pass.
- CUDA out-of-memory during Swin-L inference/export or high-resolution inputs.
- Training or export succeeds for tiny/lite but not standard large weights.

Fix:

- Do not use `--construct-model` or model instantiation as a default smoke in memory-constrained CPU environments; use the bundled probe without `--construct-model` first.
- Prefer `BiRefNet(bb_pretrained=False)` for local full checkpoints to avoid extra backbone-loading work.
- Use Swin-T/lite weights for constrained ONNX conversion, or reduce input resolution for exploratory export.
- The source ONNX notes report about `19.7GB` GPU memory for standard conversion; plan more headroom for different versions/providers.
- For inference memory and postprocessing choices, route to `../inference-and-postprocessing/SKILL.md`. For training memory, batch size, precision, and compile choices, route to `../training-and-evaluation/SKILL.md`.

## Patch helper shape errors

Symptoms:

- `einops` reports that height/width cannot be divided into the requested grid.
- `patches2image` reconstructs the wrong shape.

Fix:

- Ensure `H % grid_h == 0` and `W % grid_w == 0` for default `image2patches`.
- When using `patch_ref`, ensure the reference spatial size is the intended patch size and divides the source or output size exactly.
- Keep the transformation pair compatible: the default split transformation must be reassembled by the default inverse transformation.

## `torch.compile` prefix and version issues

Symptoms:

- Checkpoint keys include `_orig_mod.`.
- Compilation fails or consumes unexpected CPU memory.

Fix:

- Use `check_state_dict` before loading compiled checkpoints into an uncompiled model.
- Treat source comments about compile performance and PyTorch versions as version-sensitive. Disable compile for diagnosis if model behavior differs between eager and compiled execution.

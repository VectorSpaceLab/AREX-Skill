# Install, Dependencies, Models, And Devices

## Package And Dependencies

GroundingDINO installs as the `groundingdino` distribution and imports as `groundingdino`. The verified package version for this skill baseline is `0.1.0`.

Runtime dependencies from package metadata are:

- `torch`
- `torchvision`
- `transformers`
- `addict`
- `yapf`
- `timm`
- `numpy`
- `opencv-python`
- `supervision>=0.22.0`
- `pycocotools`

Optional workflow dependencies are not all base requirements. Folder pseudo-labeling uses FiftyOne, and Gradio/web/Hugging Face flows use `gradio` and `huggingface_hub` when those features are selected.

## Setup Behavior

The package `setup.py` imports Torch while preparing the build and tries to build a custom `groundingdino._C` extension when CUDA build conditions are satisfied. If CUDA is unavailable or `CUDA_HOME` is not set, setup may skip the extension and the package can still import with a warning that custom C++ ops are unavailable.

Use `pip install -e .` for a local checkout. If setup fails while trying to install or import Torch during metadata generation, install a compatible Torch/TorchVision pair first, then retry the package install. If CUDA custom ops are required, ensure the CUDA toolkit path matches the Torch CUDA build before reinstalling.

## Model Configs And Checkpoints

The included config files define two released model variants:

| Config | Backbone | Key live facts | Typical checkpoint |
| --- | --- | --- | --- |
| `GroundingDINO_SwinT_OGC.py` | `swin_T_224_1k` | `num_queries=900`, `max_text_len=256`, `bert-base-uncased` | `groundingdino_swint_ogc.pth` |
| `GroundingDINO_SwinB_cfg.py` | `swin_B_384_22k` | `num_queries=900`, `max_text_len=256`, `bert-base-uncased` | `groundingdino_swinb_cogcoor.pth` |

Always pair the config with the matching checkpoint. Mismatches can load with non-strict state dict behavior but produce poor detections or invalid benchmark results.

## Device Selection

The public API defaults to `device="cuda"`. For CPU-only runs, pass `device="cpu"` to API calls or `--cpu-only`/`--device cpu` to bundled helpers. Use CUDA only when `torch.cuda.is_available()` is true and the config/checkpoint are suitable for the target hardware.

CPU runs are useful for import, preprocessing, CLI validation, and small smoke checks. Full inference, Gradio demos, pseudo-labeling large folders, and COCO evaluation can be slow on CPU.

## Validation

Run the root helper when diagnosing an environment:

```bash
python scripts/check_grounding_dino_install.py
```

It checks distribution metadata, important imports, API signatures, config loading, Torch backend facts, and optional dependency presence without loading model weights or downloading files.

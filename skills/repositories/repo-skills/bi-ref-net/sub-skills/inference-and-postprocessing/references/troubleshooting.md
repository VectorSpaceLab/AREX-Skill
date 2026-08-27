# BiRefNet Inference Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `--repo-root` is missing or invalid | The helper imports source modules only from an explicit checkout root | Pass a root containing `config.py`, `models/`, `utils.py`, and `image_proc.py` |
| Import fails before model loading | Missing base dependencies or wrong checkout root | Install the base requirements and verify `torch`, `torchvision`, `Pillow`, `opencv-python`, `timm`, `kornia`, `einops`, and `huggingface_hub` as needed |
| HF load fails with cache/network errors | `--model-source hf` needs hub access or a populated cache | Re-run with local `.pth`, prefetch the model once, or verify the repo ID |
| README one-line load fails on `transformers` | The shortcut uses `AutoModelForImageSegmentation` | Install `transformers` or use the bundled helper's HF mode |
| Local `.pth` load fails or reports missing keys | Wrong backbone/config, DDP prefixes, compiled prefixes, or a non-BiRefNet checkpoint | Use a matching BiRefNet config/checkpoint; the helper applies `check_state_dict` to remove `module.` and `_orig_mod.` prefixes |
| `Could not find a tensor state dict` | Checkpoint wraps model weights under an unexpected key or is not a weight file | Extract the real model state dict or save a plain `.pth` weight dictionary |
| CUDA is unavailable | The selected backend has no GPU or a CPU-only PyTorch build | Use `--device auto` or `--device cpu`; install a CUDA PyTorch build only when GPU inference is required |
| Autocast errors on CPU | CUDA autocast was enabled in a CPU run | Do not enable autocast outside CUDA; the helper uses plain inference mode on CPU |
| Invalid `--resolution` value | The helper accepts `config.size`, `default`, `original`, `keep`, `none`, square integers, or `WxH` | Use `--resolution config.size` for the repo default or a concrete value such as `1024x1024` |
| Input file is skipped or rejected | Unsupported extension or a video file passed to the image helper | Use `.jpg/.jpeg/.png/.bmp/.webp/.tif/.tiff` for images; route videos to `video-workflows.md` |
| GPU memory runs out on large images | Resolution is too high or comparison/refinement adds extra memory | Lower `--resolution`, disable comparison/matting, or use CPU for the smoke check |
| Transparent or comparison output is missing | `--foreground-refine` or `--save-comparison` was not enabled | Enable the relevant flag; the mask file is always separate from foreground/comparison exports |
| Video output is blank or broken | FPS is zero, the codec is unavailable, or the writer was not released | Keep the source FPS, use a supported codec/container, and always release writers |
| Native `inference.py` crashes before parsing arguments | Its default `ckpt_folder` glob resolves to an empty list | Create the expected `ckpts/` tree or pass explicit checkpoint arguments |

## Other notes

- If you use a non-square `config.size`, remember that the repo stores sizes as `(width, height)` and the resize transform needs the reversed order.
- Run `scripts/birefnet_refine_smoke.py --repo-root <checkout>` when you need a CPU-only check that `refine_foreground` works on tiny PIL inputs.
- Keep output directories outside long-lived source image directories when possible; the helper skips files under `--output-dir` during directory scans.

# Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'fiftyone'` | Dataset annotation/export uses optional FiftyOne APIs that are not part of the base package requirements. | Install the smallest workflow extra with `pip install fiftyone`, then rerun. If only single-image inference is needed, route to `../inference/` instead. |
| `ModuleNotFoundError: No module named 'typer'` | A Typer-based script is being run instead of this bundled helper. | Use `scripts/grounding_dino_pseudolabel.py`, which uses `argparse`, or install `typer` only for that separate script. |
| Help fails before showing options | Optional dependencies were imported at module import time by another script. | Run `python scripts/grounding_dino_pseudolabel.py --help`; this helper imports optional packages only after parsing. |
| Empty detections | Prompt categories do not match the image, thresholds are too high, checkpoint/config mismatch, or the wrong device failed silently upstream. | Test one image via `../inference/`, try period-separated prompts, lower `--box-threshold` or `--text-threshold`, and verify the config/checkpoint pair. |
| Noisy detections | Thresholds are too low or the prompt combines too many similar concepts. | Raise `--box-threshold`, raise `--text-threshold`, split prompts into smaller class groups, and inspect `--draw-labels` output before export. |
| Boxes appear shifted or scaled incorrectly | Relative `cxcywh` model boxes were treated as absolute pixels, or relative `xywh` boxes were multiplied before assigning to FiftyOne. | Keep GroundingDINO output normalized until `torchvision.ops.box_convert(..., 'cxcywh', 'xywh')`; assign the resulting relative `xywh` values directly to `fo.Detection.bounding_box`. |
| Output directory already exists | The helper protects existing `coco_dataset` and `images_with_bounding_boxes` outputs. | Choose a new `--output-dir` or pass `--overwrite` to remove the managed output subdirectories first. |
| Large folder is slow | Images are processed sequentially and each image runs a full model forward pass. | Start with `--subsample 25`, use GPU with `--device cuda` when available, and export only after prompt/threshold review. |
| FiftyOne GUI fails, hangs, or is unreachable | `--view` launches a local FiftyOne App/server, which may not work in headless or remote shells. | Omit `--view` for non-GUI runs, rely on `--draw-labels`, or configure the host/port according to the local FiftyOne environment. |
| Missing config or checkpoint | The helper requires existing local files and never downloads models. | Provide explicit `--config-path` and `--weights-path`; route to root install/model guidance for model selection. |
| `torchvision` import or operator errors | Torch/torchvision versions are incompatible or torchvision is missing. | Install a torchvision build compatible with the installed torch version; the helper needs `torchvision.ops.box_convert`. |
| CUDA unavailable or out of memory | `--device cuda` was requested on a machine without usable GPU memory. | Use `--device cpu` for small smoke runs, reduce image count with `--subsample`, or move to a GPU environment. |

## Recovery case: missing FiftyOne

1. Confirm the helper itself works: `python scripts/grounding_dino_pseudolabel.py --help`.
2. Install only the optional dataset dependency: `pip install fiftyone`.
3. Run a non-GUI smoke pass with `--subsample 5 --draw-labels` and no `--view`.
4. Inspect annotated images, then add `--export-coco` when labels are acceptable.

## Recovery case: 25-image COCO export without GUI

Use a fresh output directory and keep GUI disabled:

```bash
python scripts/grounding_dino_pseudolabel.py \
  --image-directory ./images \
  --text-prompt "bus . car ." \
  --config-path ./GroundingDINO_SwinT_OGC.py \
  --weights-path ./groundingdino_swint_ogc.pth \
  --subsample 25 \
  --export-coco \
  --draw-labels \
  --output-dir ./pseudolabel-25
```

If output exists, use a new directory first; use `--overwrite` only when the previous managed export can be deleted.

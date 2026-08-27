# Pseudo-label Workflow

This workflow adapts GroundingDINO folder annotation into a self-contained helper that avoids Typer and keeps FiftyOne as an explicit optional dependency for dataset export, image review, and GUI viewing.

## Dependencies

Base GroundingDINO inference needs an installed `groundingdino` package with compatible `torch`, `torchvision`, image libraries, a config file, and a checkpoint file. Dataset annotation additionally needs:

```bash
pip install fiftyone
```

The bundled helper uses `argparse`, so `typer` is not required. Install `typer` only if you intentionally run a separate Typer-based script outside this skill.

## Core command

```bash
python scripts/grounding_dino_pseudolabel.py \
  --image-directory ./images \
  --text-prompt "bus . car ." \
  --box-threshold 0.15 \
  --text-threshold 0.10 \
  --config-path ./GroundingDINO_SwinT_OGC.py \
  --weights-path ./groundingdino_swint_ogc.pth \
  --export-coco \
  --draw-labels \
  --output-dir ./pseudolabel-output
```

Use `--subsample 25` for a fast review pass before labeling a large directory. The default does not launch a GUI; add `--view` only when a FiftyOne session should be opened.

## Processing steps

1. Validate the image directory, prompt, thresholds, config path, checkpoint path, output directory, and optional subsample.
2. Import optional runtime modules only after argument parsing so `--help` works in minimal environments.
3. Load the model with `groundingdino.util.inference.load_model(config_path, weights_path, device=device)`.
4. Create a FiftyOne dataset from the image directory, optionally clone a deterministic `take(subsample)` view.
5. For each image, call `load_image(sample.filepath)` and `predict(model, image, caption, box_threshold, text_threshold, device)`.
6. Convert each normalized `cxcywh` prediction to normalized top-left `xywh` with `torchvision.ops.box_convert`.
7. Store each phrase/logit as a `fo.Detection(label=phrase, bounding_box=xywh, confidence=score)` under the `detections` field.
8. Optionally export COCO data to `output-dir/coco_dataset` and draw review images to `output-dir/images_with_bounding_boxes`.
9. Optionally launch FiftyOne with `--view` after detections are saved.

## CLI options

| Option | Meaning | Default |
| --- | --- | --- |
| `--image-directory` | Folder containing input images. | Required |
| `--text-prompt` | Open-vocabulary prompt; separate categories with periods for clearer labels. | Required |
| `--box-threshold` | Filters candidate boxes by maximum token confidence. | `0.15` |
| `--text-threshold` | Filters phrase tokens used to decode labels. | `0.10` |
| `--config-path` | Existing GroundingDINO model config file. | Required |
| `--weights-path` | Existing GroundingDINO checkpoint file. | Required |
| `--device` | Torch device passed to model loading and prediction, such as `cuda` or `cpu`. | `cuda` |
| `--export-coco` | Export a COCO detection dataset under `output-dir/coco_dataset`. | Off |
| `--draw-labels` | Render annotated review images under `output-dir/images_with_bounding_boxes`. | Off |
| `--view` | Launch the FiftyOne App after labeling. | Off |
| `--output-dir` | Parent directory for exported artifacts. | `grounding_dino_pseudolabel_output` |
| `--subsample` | Label only the first sampled subset of images. | All images |
| `--overwrite` | Remove existing managed output subdirectories before writing. | Off |

## Choosing thresholds and prompts

Start with the source workflow defaults, `--box-threshold 0.15 --text-threshold 0.10`, when recall is more important than precision. Raise thresholds if review images are noisy. Lower thresholds cautiously if expected objects are missing.

Prefer prompts like `"bus . car . traffic light ."` rather than comma-only lists. GroundingDINO lowercases and period-terminates captions internally, but explicit period-separated categories make phrase decoding and review easier.

## Output policy

The helper writes only when `--export-coco`, `--draw-labels`, or `--view` is requested. It refuses to write into existing managed output subdirectories unless `--overwrite` is passed. Use a fresh `--output-dir` for repeatable experiments when comparing thresholds or prompts.

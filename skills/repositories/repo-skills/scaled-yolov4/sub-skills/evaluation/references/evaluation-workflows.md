# Evaluation workflows

## Main function

The bundled concrete evaluation entrypoint is `runtime/test.py`. Run it through `scripts/run_evaluation.py` so the working directory and `PYTHONPATH` point at the packaged runtime mirror:

```bash
python sub-skills/evaluation/scripts/run_evaluation.py --dry-run -- --weights weights.pt --data data/coco.yaml --task val --img-size 896 --batch-size 8
```

The standalone evaluation function centers on:

- `test(data, weights=None, batch_size=16, imgsz=640, conf_thres=0.001, iou_thres=0.6, save_json=False, single_cls=False, augment=False, verbose=False, model=None, dataloader=None, save_dir='', merge=False, save_txt=False)`

The same function is used in two ways:

- called directly for standalone validation,
- called from training at epoch boundaries.

## Key run modes

### `val`

Validate the chosen checkpoint against the validation split.

### `test`

Run the test split instead of the validation split.

### `study`

Sweep image sizes, save the metric/time results, and zip the collected study files.

## Important inputs

- `--weights` for one or more checkpoints.
- `--data` for the dataset YAML.
- `--batch-size` and `--img-size` for validation sizing.
- `--conf-thres` and `--iou-thres` for prediction filtering.
- `--save-json` to produce COCO-compatible JSON output.
- `--single-cls` when the dataset should be treated as one class.
- `--augment` for TTA-style validation.
- `--merge` to enable merge NMS.
- `--save-txt` to write normalized prediction text files.

## Metric outputs

The evaluation loop reports:

- precision
- recall
- mAP@0.5
- mAP@0.5:0.95
- per-class AP when verbose output is enabled
- inference and NMS speed per image

## COCO JSON path

When `save_json` is active and the dataset matches the COCO workflow, the evaluator writes a JSON file and then tries to score it with `pycocotools`.

If the optional COCO package is missing, the JSON path can still be produced, but the COCO-specific summary will fail.

## Study mode behavior

`study` runs the evaluation helper over a range of image sizes, writes a text file for each point, and archives the results.

Use it when you want to understand how much AP changes as you scale the input size.

## Validation checklist

- The runtime bundle is complete: `python scripts/check_runtime_bundle.py`.
- The checkpoint loads.
- The dataset split resolves.
- The image size is compatible with the model stride.
- `single_cls` matches the dataset definition.
- Optional JSON scoring dependencies are installed if you want COCO results.

Use `scripts/prepare_evaluation_run.py` for a safe plan check, then use `scripts/run_evaluation.py --dry-run -- ...` to preview the concrete bundled `runtime/test.py` command before removing `--dry-run`.

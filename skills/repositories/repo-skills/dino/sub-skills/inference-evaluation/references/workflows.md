# Inference and evaluation workflows

## 1. Evaluate a pretrained checkpoint on COCO

### Inputs and preflight

Collect these before starting the run:

- DINO project root and commit/version.
- One local checkpoint file, plus whether the selected state is `model` or an
  explicitly requested EMA state.
- Matching config: 4-scale or 5-scale, backbone, class count, and model
  vocabulary.
- COCO root with the required image/annotation layout.
- A writable output directory and a device with the compiled
  `MultiScaleDeformableAttention` extension.

The source entry point constructs both train and validation datasets before the
`--eval` branch, so a missing train directory can fail an evaluation even when
only validation is conceptually needed. See the setup sibling route for data
repair; do not invent a second layout in this route.

Check the extension and key bbox imports before a long command:

```bash
python -c "import torch, torchvision, timm, pycocotools, MultiScaleDeformableAttention; print(torch.__version__, torchvision.__version__)"
```

For panoptic or mask evaluation only, additionally run `python -c "import panopticapi"`.
The ordinary bbox route must not be blocked by that optional dependency.

In the verified environment this should report the approved Torch pair
`2.5.1+cu121` and `0.20.1+cu121` and complete the extension/import checks.
The shell's current environment may differ; treat that as a setup mismatch,
not as evidence that the model is broken.

### Single-process evaluation

Use the checked-in wrapper for the README-style 4-scale run:

```bash
cd /path/to/DINO
bash scripts/DINO_eval.sh /path/to/COCODIR /path/to/checkpoint
```

The wrapper passes `--eval --resume`, uses `DINO_4scale.py`, and applies the
DINO denoising overrides documented in the API reference. It writes under its
configured `logs/` path. For a controlled output location, run explicitly:

```bash
python main.py \
  --output_dir /tmp/dino-eval-r50-ms4 \
  -c config/DINO/DINO_4scale.py \
  --coco_path /path/to/COCODIR \
  --eval --resume /path/to/checkpoint \
  --num_workers 2 \
  --options dn_scalar=100 embed_init_tgt=TRUE \
    dn_label_coef=1.0 dn_bbox_coef=1.0 use_ema=False \
    dn_box_noise_scale=1.0
```

For the reference 5-scale model, change the config and use the 5-scale wrapper
when appropriate. Do not use the eight-GPU distributed wrappers as a first
check; they add launch and synchronization failure modes and are outside this
route's bounded smoke scope.

### Expected artifacts and interpretation

A completed run should provide:

- console/log output ending with COCO evaluator summary;
- `output_dir/log.txt` containing `test_coco_eval_bbox` entries when the
  output directory is active;
- `output_dir/eval.pth` with the COCO bbox evaluator state when saved by
  `main.py`; and
- the exact command, config, checkpoint, dataset root, device, and any options
  recorded alongside the result.

The first COCO AP summary is the usual `AP@[IoU=0.50:0.95]` box AP. Do not
compare it with the README's model-zoo number unless split (val/test-dev),
epoch/checkpoint, scale, backbone, options, and evaluation procedure match.
An interrupted run, a checkpoint load without evaluator output, or a custom
score threshold is not a COCO AP result.

`engine.evaluate` calls the model in eval/no-grad mode, uses
`orig_size=[H,W]` for bbox postprocessing, converts results to COCO
`xywh` for the evaluator, synchronizes across ranks, and summarizes after
accumulation. Its default top-k is 300 per image from the config. It does not
apply the custom-image threshold used by the smoke tool.

## 2. Single-image/custom-image inference

Use the bundled script for a reproducible one-image path that is independent of
the notebook and source visualizer:

```bash
python skills/disco/dino/sub-skills/inference-evaluation/scripts/inference_smoke.py \
  --project-root /path/to/DINO \
  --config config/DINO/DINO_4scale.py \
  --checkpoint /path/to/checkpoint \
  --image /path/to/image.jpg \
  --device cuda \
  --score-threshold 0.30 \
  --max-detections 50 \
  --output-json /tmp/predictions.json \
  --visualize /tmp/predictions.png
```

The script validates the project root, input files, threshold, resize limits,
device, and output collisions before importing the project. It does one RGB
image, one deterministic resize (`--resize 800 --max-size 1333` by default), one
ImageNet normalization, and one forward pass. It loads the selected
`--checkpoint-key` (`model` by default, with `ema_model`/`state_dict` available)
strictly after removing a leading `module.` prefix. Existing output files
require `--overwrite`. It does not download anything, invoke the notebook, use
COCO data, or run a dataset loop.

The JSON contains:

- original and transformed `[H,W]` sizes;
- portable config/checkpoint identities, selected checkpoint key, and device;
- the `[1,1]` normalized postprocess target size;
- each retained score and label/category ID;
- normalized `cxcywh` and `xyxy`; and
- transformed-image pixel `xyxy` coordinates.

If `--visualize` is supplied, the script draws the normalized boxes on the
transformed RGB image with Pillow. It clamps only the drawing coordinates to the
canvas; JSON retains the un-clamped normalized values for diagnosis. A missing
label map leaves numeric labels intact. The default COCO map is loaded only if
`util/coco_id2name.json` exists under the supplied project root; use
`--label-map` for an explicit custom map. Output records use portable relative
identities rather than exposing absolute local paths. Add `--overwrite` only
when replacing an existing output is intentional.

### Notebook correspondence

The checked-in notebook demonstrates two data sources:

1. COCO `build_dataset('val', args)`, then a target-aware visualizer for ground
   truth and predictions; and
2. a custom PIL image, `RandomResize([800], max_size=1333)`, `ToTensor`, ImageNet
   `Normalize`, a model forward, `PostProcess`, a `0.3` score mask, and a
   `COCOVisualizer` call.

The bundled script retains the useful custom-image logic but replaces notebook
state and `COCOVisualizer` with explicit CLI inputs, JSON, and an optional
Pillow drawing. For source visualizer parity, remember that its `boxes` field is
normalized `cxcywh` and its `size` field is `[H,W]`; do not pass absolute
`xyxy` into that visualizer.

## 3. Inspect output without drawing

For a machine-readable smoke output and no image dependency beyond the model's
input loader:

```bash
python skills/disco/dino/sub-skills/inference-evaluation/scripts/inference_smoke.py \
  --project-root /path/to/DINO \
  --config config/DINO/DINO_5scale.py \
  --checkpoint /path/to/checkpoint \
  --image /path/to/image.png \
  --device cuda \
  --score-threshold 0.05 \
  --output-json /tmp/dino.json
```

Use a low threshold only to inspect low-confidence behavior. It will not make a
model's COCO AP comparable to a run with a different config or checkpoint.

# Segmentation workflows

These are guarded command templates for the standalone
`semantic_segmentation/` project. Replace all placeholders with approved
paths. Train and validation commands are run from the
`semantic_segmentation/` directory; the demo examples are run from
`semantic_segmentation/demo/` so the relative paths match the source README.
The bundled scripts are source-independent and read-only.

## 1. Environment and static gate

The repository README describes a historical Python 3.8/CUDA 10.2/Paddle
2.1.0 environment. `requirements.txt` pins:

```text
cityscapesScripts==2.2.0
numpy==1.20.3
opencv-python==4.4.0
scipy==1.6.3
yacs==0.1.8
```

The supplied live facts are Paddle GPU 2.6.2, passing yacs/PyYAML/OpenCV/SciPy/
cityscapesScripts imports, and a CUDA smoke. Re-probe the active shell rather
than treating those facts as proof of a different environment:

```bash
python -c 'import paddle; print(paddle.__version__, paddle.get_device(), paddle.is_compiled_with_cuda())'
python -c 'import yacs, yaml, cv2, scipy; print("segmentation dependencies import")'
```

Then validate paths without importing PaddleViT or touching data:

```bash
python skills/disco/paddlevit/sub-skills/segmentation/scripts/validate_segmentation_layout.py \
  --dataset ADE20K --root /path/to/ADEChallengeData2016 --mode val \
  --num-classes 150 --check-labels
```

For demo paths and YAML fields:

```bash
python skills/disco/paddlevit/sub-skills/segmentation/scripts/segmentation_demo_check.py \
  --config /path/to/config.yaml --model_path /path/to/model.pdparams \
  --pretrained_backbone /path/to/backbone.pdparams \
  --img_dir /path/to/image-only-dir --results_dir /path/to/new-results
```

A static/layout pass proves neither model construction nor a CUDA forward. Do
not download data or weights as part of these checks.

## 2. Training

```bash
cd /path/to/PaddleViT/semantic_segmentation
CUDA_VISIBLE_DEVICES=0 python train.py \
  --config configs/setr/SETR_MLA_Large_480x480_80k_pascal_context_bs_8.yaml
```

The source distributed form is:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 python -u -m paddle.distributed.launch train.py \
  --config CONFIG
```

Before launching, inspect the final YAML (including recursive `BASE` files),
class count, dataset root, crop size, normalization, GPU count, batch size,
`SAVE_DIR`, and an explicit iteration/time budget. `DATA.NUM_WORKERS: 0` is
the safe source default. A distributed batch size is per process, not a
replacement for reviewing the learning-rate assumptions.

Training accepts `--resume`, not `--model_path`. The source expects a model
filename such as `iter_8000_model_state.pdparams`; it derives the optimizer
sibling by replacing `.pdparams` with `.pdopt` and `model` with `opt`, i.e.
`iter_8000_opt_state.pdopt`. Both files must exist. The optimizer scheduler
`last_epoch` controls the resumed iteration and the dataloader start. The loop
writes pairs at `SAVE_FREQ_CHECKPOINT` and the final iteration, then retains at
most `KEEP_CHECKPOINT_MAX` pairs. The source may remove a non-directory path
at `SAVE_DIR` and create the directory; use an explicitly disposable output.

## 3. Validation and metrics

Single-scale validation:

```bash
cd /path/to/PaddleViT/semantic_segmentation
CUDA_VISIBLE_DEVICES=0 python val.py \
  --config CONFIG --model_path /path/to/full_segmentation_model.pdparams
```

Multi-scale validation is a separate, expensive operation:

```bash
CUDA_VISIBLE_DEVICES=0 python val.py \
  --config CONFIG --model_path MODEL --multi_scales True
```

Distributed validation follows the source launcher:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 python -u -m paddle.distributed.launch val.py \
  --config CONFIG --model_path MODEL
```

`--model_path` is a full segmentation state dict. If omitted, `val.py` falls
back to `SAVE_DIR/iter_{TRAIN.ITERS}_model_state.pdparams`. It builds the model,
loads weights, reads the validation dataset, and invokes single-scale or
multi-scale sliding inference. `VAL.IS_SLIDE`, `VAL.CROP_SIZE`,
`VAL.STRIDE_SIZE`, `VAL.IMAGE_BASE_SIZE`, `VAL.SIZE_DIVISOR`, and
`VAL.RESCALE_FROM_ORI` control geometry. Multi-scale loops over
`VAL.SCALE_RATIOS` and horizontal flips; it is not merely a flag for another
GPU.

The reported values are overall `mIoU`, accuracy, Kappa, and arrays of
per-class IoU/accuracy. `metrics.calculate_area` excludes the dataset
`ignore_index` (normally 255), then aggregates class intersections,
predicted area, and label area. A real task result requires a real split and a
compatible checkpoint; a demo overlay is not a metric result.

The parser declares `--multi_scales` with `type=bool`. In ordinary argparse,
the nonempty string `False` is truthy. Omit the flag for single-scale and use
`--multi_scales True` only for an approved multi-scale run. Validation uses a
distributed sampler with `drop_last=True`; record any dropped remainder.

## 4. Directory demo inference

```bash
cd /path/to/PaddleViT/semantic_segmentation/demo
CUDA_VISIBLE_DEVICES=0 python demo.py \
  --config ../configs/setr/SETR_PUP_Large_768x768_80k_cityscapes_bs_8.yaml \
  --model_path /path/to/full_segmentation_model.pdparams \
  --pretrained_backbone /path/to/backbone.pdparams \
  --img_dir /path/to/image-only-dir \
  --results_dir /path/to/new-results
```

`demo.py` reads each entry from `img_dir` with OpenCV, converts BGR to RGB,
resizes/normalizes on CPU, sends a CHW tensor to Paddle, runs single-scale
sliding inference, and writes two files per image: a blended overlay and a
palette mask named with `_color.png`. It does not load labels or calculate
mIoU. Keep the input directory image-only: the source does not filter
`os.listdir` entries and a JSON, directory, or hidden file can cause an OpenCV
failure.

The source recursively deletes an existing `results_dir` before creating it.
Run the read-only demo checker first and use a new directory unless deletion
has been explicitly approved. The demo's `config.update_config` path also
contains a compatibility seam: it tests membership in an argparse Namespace
for `pretrained_backbone`. If that fails in the active Python, stop, record the
error, and make only an approved minimal `hasattr`/attribute-access patch
before retrying. Do not claim the backbone was applied when this path was not
executed.

## 5. Checkpoint and conversion boundaries

Keep these artifacts distinct:

- **Full segmentation weights:** `--model_path` for `val.py` or demo; class
  count, decoder, backbone, and tensor shapes must match the config.
- **Backbone weights:** `--pretrained_backbone`, wired into
  `MODEL.PRETRAINED` by `update_config` for model initialization; not a
  substitute for a trained segmentation head.
- **Resume pair:** `--resume` model/optimizer files, restoring optimizer and
  scheduler state as well as model parameters; not an inference checkpoint
  contract.

`load_pretrained_model` copies matching keys and may interpolate some ViT
positional embeddings. It cannot repair arbitrary decoder, class-head, or
architecture mismatches. Review loaded/missing keys and shapes.

Dataset conversion is not inference and may mutate source trees:

- `tools/voc2010_to_pascalcontext.py` needs external `mmcv` and `detail`,
  maps VOC/detail masks to the selected 60-class context indices, and writes
  context PNGs and train/val lists under the selected dataset tree.
- `tools/convert_cityscapes.py` needs `mmcv` and `cityscapesscripts`, turns
  polygon JSON into `*_labelTrainIds.png`, and writes split lists. Its helper
  writes labels by replacing the polygon suffix, so inspect/stage a copied
  dataset rather than assuming `--out-dir` relocates every file.

Never run a converter without an explicit disposable output root and a
mutation approval. Do not imply that a `.pdparams` state dict is a Paddle
Inference export, an ONNX artifact, or a cross-framework weight conversion.
The repository's generic export/port documentation requires a separate
static-graph or parameter-mapping contract and equivalence check.

## 6. Evidence tiers

Record one of these in every handoff:

1. **Static/parser:** help/YAML/path/layout checks only.
2. **CPU construction:** Paddle imports and the selected model builds on CPU.
3. **GPU smoke:** selected model performs an approved tiny forward/batch on
   the target CUDA environment.
4. **Task validation:** real data and compatible weights produce metrics.

Slide inference, multi-scale inference, distributed launch, and training are
separately budgeted expensive operations; a lower tier must not be reported as
one of the higher tiers.

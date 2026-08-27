---
name: segmentation
description: "Operate PaddleViT semantic_segmentation for SETR, UperNet, DPT,
  Segmenter, Trans2Seg, SegFormer, and TopFormer: select compatible configs,
  validate dataset layouts, run train/val/demo inference, manage checkpoints and
  metrics, and keep conversion and GPU-expense boundaries explicit."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PaddleViT semantic segmentation

Use this operating skill for the standalone `semantic_segmentation/` toolkit:
pixel-wise semantic prediction, dataset preparation, model-family/config
selection, training, validation, directory demo inference, checkpoint resume,
metrics, and dataset conversion boundaries. It is not a general export skill
and it does not download data or weights.

## Route before acting

Establish these facts before constructing a command:

1. **Operation:** train, single-scale validation, multi-scale validation, or
   unlabeled directory demo.
2. **Config:** an existing YAML under `semantic_segmentation/configs/` (or a
   copied, explicitly reviewed variant). Treat `DATA.DATASET`,
   `DATA.DATA_PATH`, `DATA.NUM_CLASSES`, `DATA.CROP_SIZE`, model wiring, loss,
   validation geometry, and `SAVE_DIR` as one contract.
3. **Data:** the exact root and split. Do not infer the dataset from a model
   name or checkpoint filename.
4. **Weights:** a full segmentation `--model_path`, an optional backbone
   `--pretrained_backbone`, a training `--resume` pair, or a deliberate
   train-from-scratch choice.
5. **Compute:** CPU parser/layout checks versus CPU model allocation versus a
   real GPU forward; requested GPU count and an explicit budget for slide,
   multi-scale, distributed, or training work.
6. **Output ownership:** `SAVE_DIR` and demo `--results_dir`. The source demo
   recursively deletes an existing results directory; never point it at
   valuable data without explicit approval.

Run the source-independent preflight before importing PaddleViT:

```bash
python skills/disco/paddlevit/sub-skills/segmentation/scripts/validate_segmentation_layout.py --help
python skills/disco/paddlevit/sub-skills/segmentation/scripts/segmentation_demo_check.py --help
```

Read the smallest supporting reference needed:

- [references/model-overview.md](references/model-overview.md): registry,
  family/head compatibility, and config invariants.
- [references/workflows.md](references/workflows.md): command templates,
  train/val/demo/resume, compute tiers, and conversion boundaries.
- [references/data-formats.md](references/data-formats.md): built-in roots,
  pairing, class ids, custom data, and transforms.
- [references/troubleshooting.md](references/troubleshooting.md): known source
  seams, failure classification, and recovery order.

## Supported model registry

`src/models/__init__.py` dispatches by substring in `MODEL.NAME` to SETR,
UperNet, DPT, Segmenter, Trans2Seg, Segformer, and TopFormer. The current
TopFormer dispatch has a source typo: it checks `"TopFomer"` (missing `r`),
so use that spelling in this checkout unless a separately tested source patch
changes both factory and configs. See the model reference for exact family
wiring and known UperNet/auxiliary-head constraints.

## Source command contract

Run training and validation from `semantic_segmentation/`:

```bash
python train.py --config CONFIG [--resume CHECKPOINT]
python val.py --config CONFIG [--model_path MODEL] [--multi_scales True]
```

Run the demo from `semantic_segmentation/demo/` (or make every relative path
explicit):

```bash
python demo.py --config CONFIG --model_path MODEL \
  --pretrained_backbone BACKBONE --img_dir IMAGE_DIR --results_dir OUTPUT_DIR
```

The training parser exposes `--config` and `--resume`, not `--model_path`.
Validation's `--model_path` is a full segmentation state dict and falls back
to `SAVE_DIR/iter_{TRAIN.ITERS}_model_state.pdparams` when omitted. The demo
accepts the five named paths above; `--pretrained_backbone` is used to set
`MODEL.PRETRAINED`, while `--model_path` loads the segmentation model.

The validation parser declares `--multi_scales` with `type=bool`: omit the flag
for single-scale; passing the string `False` is truthy in ordinary argparse.
The demo reads every entry in `img_dir`, not only recognized image suffixes,
so keep that directory image-only. It writes an overlay and a palette PNG per
input under `results_dir`, and deletes that directory first if it exists.

## Verification ladder and stop conditions

Record the evidence tier; never promote one tier to another:

- **Static/parser:** CLI help, YAML/BASE inspection, path checks, and layout
  pairing. No Paddle model is built.
- **CPU model construction:** Paddle imports and a model is allocated/built on
  CPU. This does not validate CUDA kernels, memory, or data quality.
- **GPU smoke:** the selected model performs an approved tiny forward/batch on
  the target Paddle/CUDA environment. The supplied live facts are Paddle GPU
  2.6.2, yacs/PyYAML/OpenCV/SciPy/cityscapesScripts passing, and a CUDA smoke;
  re-probe the active shell before a real run.
- **Task validation:** a real split and compatible full checkpoint produce
  mIoU, accuracy, Kappa, and class-wise values.

Stop instead of claiming success when the config is absent, required pairings
are incomplete, class ids are ambiguous, the checkpoint is missing or
incompatible, the requested backend/budget is unavailable, or a conversion
would mutate an uncontrolled tree. Multi-scale, slide, distributed, and
training commands are expensive operations requiring an explicit budget and
stop condition.

## Evidence boundary

This skill was distilled from the available segmentation README,
`requirements.txt`, `config.py`, `train.py`, `val.py`, `demo/demo.py`, the
segmentation `src` dataset/model/transform/checkpoint/metric utilities, family
configs and READMEs, `tutorial/custom_dataset.md`, and `tools/*.py`. The
requested `docs/paddlevit-predict.md` is absent in this checkout; the available
`docs/paddlevit-predict-cn.md` describes classification prediction rather than
this segmentation demo, so it is not treated as segmentation evidence. The
available export/port docs are used only for the conversion boundary: a
`.pdparams` state dict is not automatically an inference export or a
cross-framework weight conversion.

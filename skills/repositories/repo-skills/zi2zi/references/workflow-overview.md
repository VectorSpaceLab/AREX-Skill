# zi2zi workflow overview

zi2zi turns font pairs into a conditional GAN training set, trains a generator
conditioned on style labels, then uses a trained checkpoint to synthesize or
interpolate glyph styles.

## Artifact flow

```text
source font + target font(s) + charset
  -> paired JPGs named <label>_<index>.jpg
  -> train.obj and val.obj pickle streams
  -> experiment/checkpoint, experiment/logs, experiment/sample
  -> inferred PNGs, interpolation frames/GIFs, or exported generator checkpoint
```

## Stage 1: render paired glyph images

Each rendered example is a single RGB image with width twice the canvas size:

- left half: target style glyph;
- right half: source style glyph;
- filename prefix: integer style label, such as `0_0000.jpg`.

Typical command shape:

```sh
python font2img.py \
  --src_font=<source-font.ttf> \
  --dst_font=<target-font.otf> \
  --charset=CN \
  --sample_count=1000 \
  --sample_dir=<samples-dir> \
  --label=0 \
  --filter=1 \
  --shuffle=1
```

Use [data-preparation](../sub-skills/data-preparation/SKILL.md) for charset,
label, image-schema, and validation details. For command planning without
running the original renderer, use
[zi2zi_font_pair_planner.py](../sub-skills/data-preparation/scripts/zi2zi_font_pair_planner.py).

## Stage 2: package rendered images

`package.py` scans a directory of `*.jpg` files, parses each integer label from
the filename prefix before `_`, and writes pickled `(label, image_bytes)`
records to `train.obj` and `val.obj`.

```sh
mkdir -p <experiment>/data
python package.py \
  --dir=<samples-dir> \
  --save_dir=<experiment>/data \
  --split_ratio=0.1
```

Validate that both object files exist and contain records before training. Use
[inspect_zi2zi_obj.py](../sub-skills/data-preparation/scripts/inspect_zi2zi_obj.py)
for a safe Python 3 inspection of `.obj` streams.

## Stage 3: train or fine-tune

`train.py` creates `checkpoint/`, `logs/`, and `sample/` directories under the
experiment directory and trains the `UNet` model from `experiment/data`.

```sh
python train.py \
  --experiment_dir=<experiment> \
  --experiment_id=0 \
  --batch_size=16 \
  --lr=0.001 \
  --epoch=40 \
  --sample_steps=50 \
  --schedule=20 \
  --L1_penalty=100 \
  --Lconst_penalty=15
```

Use [training-and-model](../sub-skills/training-and-model/SKILL.md) for loss
meaning, checkpoint naming, fine-tuning, `flip_labels`, and monitoring. Use
[plan_zi2zi_training.py](../sub-skills/training-and-model/scripts/plan_zi2zi_training.py)
before launching expensive jobs.

## Stage 4: infer, interpolate, or export

For normal generation from a checkpoint:

```sh
python infer.py \
  --model_dir=<checkpoint-dir> \
  --batch_size=16 \
  --source_obj=<source.obj> \
  --embedding_ids=0 \
  --save_dir=<output-dir>
```

For interpolation:

```sh
python infer.py \
  --model_dir=<checkpoint-dir> \
  --batch_size=10 \
  --source_obj=<source.obj> \
  --embedding_ids=0,1,2 \
  --save_dir=<frames-dir> \
  --interpolate=1 \
  --steps=10 \
  --output_gif=transition.gif \
  --uroboros=1
```

For generator export:

```sh
python export.py \
  --model_dir=<checkpoint-dir> \
  --batch_size=16 \
  --save_dir=<export-dir>
```

Use [inference-and-export](../sub-skills/inference-and-export/SKILL.md) for
checkpoint expectations, output names, interpolation semantics, and export
pitfalls. Use
[plan_zi2zi_inference.py](../sub-skills/inference-and-export/scripts/plan_zi2zi_inference.py)
to validate arguments and print command templates.

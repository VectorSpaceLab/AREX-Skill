# Training Configuration and Data Contract

## Merge Model

The YAML is merged over in-code defaults. An omitted field therefore does not
mean "unset"; it inherits a default. This matters most for dataset names and
paths. Validate the merged result, not just the visible YAML.

The maintained defaults include:

| Field | Default | Training significance |
| --- | ---: | --- |
| `CUDA` | `true` | Descriptive only for training; the actual path still calls `.cuda()` |
| `TRAIN.EXEMPLAR_SIZE` | `127` | Template crop side |
| `TRAIN.SEARCH_SIZE` | `255` | Search crop side |
| `TRAIN.OUTPUT_SIZE` | `25` | Training point-grid side under base defaults |
| `TRAIN.BATCH_SIZE` | `32` | Per-process loader batch |
| `TRAIN.NUM_WORKERS` | `8` | Loader worker processes |
| `TRAIN.EPOCH` | `20` | Number of inferred training epochs |
| `TRAIN.START_EPOCH` | `0` | Scheduler/loop start; must match a resume checkpoint |
| `TRAIN.BASE_LR` | `0.005` | SGD base learning rate |
| `POINT.STRIDE` | `8` | Point-grid stride under base defaults |
| `DATASET.VIDEOS_PER_EPOCH` | `600000` | Samples per epoch before multiplying by epochs |
| `DATASET.GOT.ROOT` | `data/GOT-10k/crop511` | Cropped GOT-10k training root |
| `DATASET.GOT.ANNO` | `data/GOT-10k/train.json` | Training annotation JSON |

These base defaults are not a complete launch config: notably `BAN.BAN` defaults
to false, while the training loader and model path require a BAN dataset/head.
The default dataset list also includes entries whose paths are empty.

## Critical Sections

### `TRAIN`

- `EXEMPLAR_SIZE`, `SEARCH_SIZE`, `OUTPUT_SIZE`, and `BASE_SIZE` define training
  geometry. Template and search sides should be positive odd integers, with the
  search larger than the template.
- A historical consistency heuristic is
  `(SEARCH_SIZE - EXEMPLAR_SIZE) / POINT.STRIDE + 1 + BASE_SIZE`. It equals 25
  for base defaults and 16 for V1/V2 settings. The original runtime disabled
  this assertion, and V3 intentionally uses output 15; treat mismatch as a
  warning requiring architecture evidence, not an automatic rewrite.
- `NEG_NUM`, `POS_NUM`, and `TOTAL_NUM` control point-label subsampling. Positive
  samples use at most `POS_NUM` positives and `TOTAL_NUM - POS_NUM` negatives.
  A negative pair uses at most `NEG_NUM` negatives and leaves all other labels
  ignored.
- `CLS_WEIGHT` and `LOC_WEIGHT` combine classification and IoU losses. Keep
  non-negative and do not set both to zero.
- `BATCH_SIZE` is per process. `NUM_WORKERS=0` is useful for diagnosing loader
  failures; increase only after a one-sample and one-batch probe.
- `BASE_LR`, `MOMENTUM`, `WEIGHT_DECAY`, and `GRAD_CLIP` configure SGD and
  clipping. The backbone parameter group uses
  `BACKBONE.LAYERS_LR * TRAIN.BASE_LR`; neck and BAN head use `BASE_LR`.
- `LR.TYPE` supports `log`, `step`, `multi-step`, `linear`, or `cos`. Scheduler
  keyword values live under `LR.KWARGS`. Warmup is a separate scheduler prefix
  controlled by `LR_WARMUP`.
- `LOG_DIR` and `SNAPSHOT_DIR` are interpreted relative to launch cwd when not
  absolute. Use unique run-specific locations.
- `RESUME` is a complete training checkpoint. `PRETRAINED` is model-only. If
  both are non-empty, resume wins for this branch.

### `DATASET`

- `NAMES` is the exact active list. Every listed name is looked up as a child
  mapping such as `DATASET.GOT`.
- Each child requires `ROOT`, `ANNO`, `FRAME_RANGE`, and `NUM_USE`.
  `FRAME_RANGE` limits search-frame selection around a randomly chosen template
  frame. `NUM_USE=-1` means the number of videos; a positive value samples with
  reshuffling/repetition. Zero creates unusable sampling.
- `VIDEOS_PER_EPOCH>0` overrides the summed `NUM_USE`; the dataset length is
  `VIDEOS_PER_EPOCH * TRAIN.EPOCH`. Otherwise it uses the summed sample count
  times epochs.
- `NEG` is the probability of choosing unrelated template/search targets.
  `GRAY` is the probability of grayscale conversion. Both must be in `[0,1]`.
- `TEMPLATE` and `SEARCH` hold augmentation values. `SHIFT` is a pixel-scale
  range; `SCALE` is a fractional range. `BLUR`, `FLIP`, and `COLOR` are
  application probabilities. The maintained configs use template
  shift/scale `4/0.05`, search `64/0.18`, and color probability `1.0`; the
  variant YAMLs set search blur to `0.2`.

### `BACKBONE`, `ADJUST`, and `BAN`

- `BACKBONE.TYPE` and `KWARGS` must construct the requested backbone.
- `BACKBONE.PRETRAINED`, when non-empty, is resolved from the launch project and
  loaded before `TRAIN.RESUME` or `TRAIN.PRETRAINED`.
- The entire backbone starts frozen, including BatchNorm in eval mode. At
  `BACKBONE.TRAIN_EPOCH`, named `TRAIN_LAYERS` are unfrozen and the optimizer
  and scheduler are rebuilt. Every layer name must exist on the backbone.
- `BACKBONE.LAYERS_LR` scales the backbone group's learning rate.
- When `ADJUST.ADJUST` is true, `TYPE`/`KWARGS` build a neck and its parameters
  enter SGD.
- `BAN.BAN` must be true for this training path. `TYPE`/`KWARGS` build the BAN
  head. Backbone output, neck input/output, and BAN input/output channels must
  be mutually compatible. Static YAML checks cannot prove the implementation
  selected by package imports.

### `POINT`

`POINT.STRIDE`, `TRAIN.SEARCH_SIZE`, and `TRAIN.OUTPUT_SIZE` create a centered
point grid. For a positive target, localization labels are left/top/right/bottom
distances from each point to the target edges. Classification positives occupy
an inner ellipse, negatives lie outside a larger ellipse, and the rest are
ignored.

## GOT-10k Training Crop Layout

The training loader does not read ordinary GOT-10k sequence frames directly.
It expects pre-cropped files and a training annotation index:

```text
<NANOTRACK_ROOT>/
  data/GOT-10k/
    train.json
    crop511/
      <video-key>/
        000001.<track-key>.x.jpg
        000002.<track-key>.x.jpg
```

The path formula is exactly:

```text
DATASET.<NAME>.ROOT / video / "{frame:06d}.{track}.x.jpg"
```

A minimal structural annotation example is:

```json
{
  "train/sequence-000001": {
    "00": {
      "000001": [120, 130, 260, 290],
      "000002": [118, 132, 258, 292]
    }
  }
}
```

Requirements and edge cases:

- Top level is a mapping of video keys; each video maps track keys to frame
  mappings.
- Frame keys are read as digits, converted to integers for sampling, then
  formatted back to six digits for both JSON lookup and crop filename. Use
  zero-padded six-digit keys to avoid lookup failure.
- A box may contain `[x1, y1, x2, y2]` or `[width, height]`. Width and height
  must be positive. Four-value boxes with non-positive extent are filtered.
- A video or track with no surviving frames is removed.
- `cv2.imread` must return an image for every sampled crop. A missing or corrupt
  crop otherwise fails later with an unhelpful shape-related exception.
- Positive pairs come from one track. The search frame is sampled within
  `FRAME_RANGE` positions of the selected template. Negative pairs may use a
  random target from another configured subdataset.

Do not confuse this with benchmark evaluation layout. Dataset licenses,
downloads, and crop generation remain the operator's responsibility.

## `BANDataset` Sample Construction

For each index, the dataset:

1. Uses a pre-shuffled cross-dataset pick list.
2. Chooses grayscale and negative-pair decisions by configured probability.
3. Loads template/search crops with OpenCV.
4. Converts the annotation box to a centered, context-scaled box based on
   `EXEMPLAR_SIZE`.
5. Applies shift/scale crop warping, then optional color, blur, and flip.
6. Generates point classification and localization targets from the augmented
   search box.
7. Transposes images from HWC to CHW and casts them to float32.

The loader does not normalize pixel values in the dataset path. Any expected
normalization is part of the selected model implementation and must be checked
for that variant.

## Variant Configuration Relationship

The three maintained YAML profiles are related but not interchangeable:

| Profile | Backbone/config channels | Batch | Train output | Dataset mix |
| --- | --- | ---: | ---: | --- |
| V1 | MobileNetV3 small, adjust/BAN 64 | 32 | 16 | GOT only, 100k samples/epoch |
| V2 | MobileNetV3 small, adjust/BAN 64 | 32 | 16 | GOT + five additional sets, 400k samples/epoch |
| V3 | MobileNetV3 small V3, adjust/BAN 96 | 64 | 15 | GOT + five additional sets, 400k samples/epoch |

All three profiles specify 50 epochs, point stride 16, base size 7, a pretrained
backbone path, and a staged backbone start at epoch 10. V1 and V2 differ in
variant head selection outside YAML as well as dataset mix and tracker-time
hyperparameters. V3 also changes backbone/head channels and output geometry.
Route exact implementation selection to **variant-catalog**.

V2/V3 list datasets whose inherited roots and annotations are empty unless the
operator supplies them. A profile is therefore evidence of intended training,
not proof that its data are available.

## Minimal Checker Inputs

Validate a copied YAML:

```bash
python scripts/check_training_config.py --config candidate.yaml \
  --project-root "$NANOTRACK_ROOT" --require-cuda
```

Or validate a minimal mapping merged over bundled defaults without any project
imports:

```bash
python scripts/check_training_config.py --mapping \
  '{"BAN":{"BAN":true,"TYPE":"DepthwiseBAN"},"DATASET":{"NAMES":["GOT"]}}'
```

The second form validates structure but cannot prove files, architecture
imports, tensor shapes, GPU capacity, or a successful training step.

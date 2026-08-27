# DINO configuration contract

`config.py` starts with a yacs `CfgNode`, optionally merges a YAML file (and
its `BASE` files), then applies a small set of CLI overrides. YAML values are
not a complete standalone schema; unspecified values come from `config.py`.
Use `check_dino_config.py` before constructing a model.

## Data

| Key | Source default / example | Operational meaning |
|---|---:|---|
| `DATA.DATASET` | `imagenet2012` | Required for the source DINO multi-crop path. |
| `DATA.DATA_PATH` | `/dataset/imagenet/` | Root containing list files and image paths. |
| `DATA.IMAGE_SIZE` | `224` | Both global crop dimensions and base positional embedding size. |
| `DATA.SMALL_CROP_IMAGE_SIZE` | `96` | Local crop dimensions. |
| `DATA.GLOBAL_CROPS_SCALE` | `[0.25, 1.0]` | Random resized crop scale range for each global view. |
| `DATA.LOCAL_CROPS_SCALE` | `[0.05, 0.25]` | Random resized crop scale range for each local view. |
| `DATA.LOCAL_CROPS_NUMBER` | `10` | Number of local views; total student views are this plus 2. |
| `DATA.BATCH_SIZE` | `16` | Local/per-GPU batch size. |
| `DATA.NUM_WORKERS` | `2` | Data loader workers; tune only after a tiny check. |
| `DATA.IMAGENET_MEAN/STD` | ImageNet values | Applied after `ToTensor` to every DINO crop. |

The global and local scale values must be finite, ordered, positive, and no
larger than 1. `SMALL_CROP_IMAGE_SIZE` should be at least `PATCH_SIZE` and
usually be divisible by it; otherwise patch/positional behavior needs an
explicit test.

## Model and DINO head

| Key | Small example / default | Operational meaning |
|---|---:|---|
| `MODEL.TYPE` | `ViT` / `dino_vit` | Label only; builder is `build_vit`. |
| `MODEL.TRANS.PATCH_SIZE` | `16` | Conv patch stride for both crop sizes. |
| `MODEL.TRANS.IN_CHANNELS` | `3` | RGB input. |
| `MODEL.TRANS.EMBED_DIM` | `384` or `768` | Backbone CLS embedding. |
| `MODEL.TRANS.DEPTH` | `12` | Transformer layer count. |
| `MODEL.TRANS.NUM_HEADS` | `6` or `12` | Must divide `EMBED_DIM`. |
| `MODEL.TRANS.MLP_RATIO` | `4.0` | MLP expansion. |
| `MODEL.TRANS.QKV_BIAS` | `true` | Attention QKV bias. |
| `MODEL.DROPPATH` | `0.1` | Student stochastic depth; teacher is rebuilt at 0. |
| `MODEL.OUT_DIM` | `65536` | DINO head output classes/bins. |
| `MODEL.NORM_LAST_LAYER` | `true`/`false` | Intended last-layer freeze flag; source wiring is inconsistent. |
| `MODEL.PRETRAINED` | `None` | Optional initialization state, not exact resume. |
| `MODEL.RESUME` | `None` | Intended checkpoint prefix; verify suffixes first. |

The `DINOHead` is constructed with input `EMBED_DIM`, output `OUT_DIM`, three
MLP layers, hidden size 2048, bottleneck 256, and optional batch norm. The
entrypoints hard-code much of this and do not consistently consume every YAML
head field. `OUT_DIM` must be positive and identical for student, teacher, and
`DINOLoss` center.

## Training schedules

| Key | Example | Meaning |
|---|---:|---|
| `TRAIN.NUM_EPOCHS` | `400` / `800` | Long-running full schedule; never start implicitly. |
| `TRAIN.WARMUP_EPOCHS` | `10` | Student LR warmup. |
| `TRAIN.BASE_LR` / `END_LR` | `7.5e-4` / `2e-6` | Cosine LR endpoints. |
| `TRAIN.WEIGHT_DECAY` / `_END` | `0.04` / `0.4` | Cosine weight-decay values in current code. |
| `TRAIN.MOMENTUM_TEACHER` | `0.996` | EMA starting momentum; schedule approaches 1. |
| `TRAIN.WARMUP_TEACHER_TEMP` | `0.04` | Teacher temperature at start of warmup. |
| `TRAIN.TEACHER_TEMP` | `0.07` | Teacher temperature after warmup. |
| `TRAIN.WARMUP_TEACHER_TEMP_EPOCHS` | `50` | Must not exceed `NUM_EPOCHS`. |
| `TRAIN.FREEZE_LAST_LAYER` | `3` | Student DINO head last-layer freeze epochs. |
| `TRAIN.GRAD_CLIP` | `0.3` or `None` | Global norm clipping when truthy. |
| `TRAIN.OPTIMIZER.NAME` | `AdamW` | Source also names `SGD`; verify typos before use. |
| `TRAIN.ACCUM_ITER` | `1` | CLI/config field, but shown source steps each batch. |

`DINOLoss` expects `ncrops = LOCAL_CROPS_NUMBER + 2`. It chunks student
outputs into that many equal batches and teacher outputs into two. Changing
crop count without changing the transform output is a hard mismatch.

## Runtime and launch fields

`SAVE`, `SAVE_FREQ`, `REPORT_FREQ`, `SEED`, `AMP`, `NGPUS`, and `TRAIN.LAST_EPOCH`
control output, reporting, determinism, AMP, worker count, and resume epoch.
`-dataset`, `-batch_size`, `-image_size`, `-data_path`, `-output`, `-ngpus`,
`-pretrained`, `-resume`, `-last_epoch`, and `-amp` are the main CLI overrides.
`-eval` is inherited by the entrypoint but the shown DINO validation path is
commented out; do not treat it as a supported DINO evaluation workflow.

## Minimum invariant checklist

- `DATA.DATASET == imagenet2012` for the unmodified DINO entrypoints.
- `IMAGE_SIZE % PATCH_SIZE == 0` and local size is patch-compatible.
- `EMBED_DIM > 0`, `NUM_HEADS > 0`, and `EMBED_DIM % NUM_HEADS == 0`.
- Exactly two teacher crops; total student crops are `LOCAL_CROPS_NUMBER + 2`.
- `OUT_DIM > 0`; teacher temperatures and their warmup are valid.
- Dataset lists and image paths exist before any training launch.
- CUDA/AMP/distributed claims are supported by the corresponding backend
  smoke, not by YAML parsing alone.

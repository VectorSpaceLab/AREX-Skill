# Training, validation, inference, and extension workflows

## Configuration skeleton

Use a user-owned YAML with these sections. A train-and-test file normally has
all three data sections; an only-test file needs a test section and model
architecture settings. Paths below are placeholders and must be replaced by the
user; this reference intentionally contains no machine-specific paths.

```yaml
BASE: ['']
TOOLBOX_MODE: train_and_test  # or only_test
TRAIN:
  BATCH_SIZE: 4
  EPOCHS: 30
  LR: 0.001
  MODEL_FILE_NAME: experiment_model
  DATA:
    FS: 30
    DATASET: PURE
    DATA_FORMAT: NCDHW       # choose per model catalog
    DATA_PATH: <user raw data or loader source>
    CACHED_PATH: <user cache>
    DO_PREPROCESS: false
    PREPROCESS:
      DATA_TYPE: [DiffNormalized]
      LABEL_TYPE: DiffNormalized
      DO_CHUNK: true
      CHUNK_LENGTH: 128
VALID:
  DATA: <same schema, subject-disjoint split>
TEST:
  USE_LAST_EPOCH: true
  DATA: <same schema for the test dataset>
  METRICS: [MAE, RMSE, Pearson, SNR, BA]
DEVICE: cpu
NUM_OF_GPU_TRAIN: 0
MODEL:
  NAME: Physnet
INFERENCE:
  BATCH_SIZE: 4
  EVALUATION_METHOD: FFT
  MODEL_PATH: ''
```

`config.py` derives file-list/cache subdirectories and the model directory from
`LOG.PATH`, experiment names, and `MODEL.MODEL_DIR`. A configured
`TEST.OUTPUT_SAVE_DIR` is also normalized under the experiment log directory.
Treat those derived locations as user-controlled; do not copy paths from a
foreign machine or put generated outputs into the runtime skill tree.

## Run sequence

1. **Choose a compatible cache.** Read the model row in
   [model-overview.md](model-overview.md), then validate a representative cache
   with [data-preparation](../../data-preparation/SKILL.md). Confirm that labels
   have the same temporal convention as model output. Do not set
   `DO_PREPROCESS: true` merely to make a missing cache disappear: it is an
   expensive, writing operation.
2. **Set model geometry.** Use `NCDHW` and a complete temporal chunk for the
   3-D models. Use `NDCHW` for frame-wise TSM models and ensure the chunk contains
   complete `FRAME_DEPTH` groups. Use the two-stream BigSmall settings exactly,
   and use `NDCHW` for RhythmFormer. Keep train, valid, and test resize/chunk
   choices compatible with checkpoint architecture and evaluation slicing.
3. **Choose labels deliberately.** `Raw`, `DiffNormalized`, and `Standardized`
   are distinct label contracts. Most supplied PhysNet/PhysMamba examples use
   `DiffNormalized`; iBVPNet and FactorizePhys examples commonly use `Raw`
   video with `Standardized` labels. A model does not convert an incompatible
   label representation into the intended one.
4. **Select a split policy.** `BEGIN`/`END` define each split; keep subjects
   disjoint. For cross-dataset evaluation, put the training dataset in
   `TRAIN.DATA`, an optional held-out training dataset in `VALID.DATA`, and the
   external dataset in `TEST.DATA`. This is the supported PURE-to-UBFC-style
   pattern, not a promise that different resolutions or labels are compatible.
5. **Probe without training.** Run `python scripts/model_smoke.py --help`, then
   select one exact model and `--device cpu` for a metadata/device check. Use a
   requested CUDA device only after the backend and optional imports are known.
6. **Run only after confirmation.** `python main.py --config_file <user yaml>`
   is expensive and may preprocess, train, save checkpoints, evaluate, and write
   plots. The parent agent must obtain user approval for those operations.

## `train_and_test` checkpoint route

`main.py` constructs a trainer through the model dispatch and calls `train`,
then `test`. Trainers save at the end of each zero-based epoch using
`TRAIN.MODEL_FILE_NAME`. Selection is controlled by `TEST.USE_LAST_EPOCH`:

- `true`: validation is not required, and most trainers test the last file at
  epoch `TRAIN.EPOCHS - 1`. This is the simplest route when no validation split
  is available, but it is not best-epoch selection.
- `false`: a valid `VALID.DATA` must be present. Trainers evaluate each epoch,
  retain the minimum validation loss (or their documented selection metric),
  and test the selected epoch. BigSmall tracks its selected `used_epoch`.
- Do not infer a one-based epoch number from a filename. The first file ends in
  `_Epoch0.pth`.

A partially completed run can leave earlier epoch files. Do not pick one by
mtime alone: confirm model name, architecture settings, label type, frame
length, and the selection policy. Resume/restart decisions and overwrite
permission remain user-controlled.

## `only_test` checkpoint route

Set `TOOLBOX_MODE: only_test`, `TEST.DATA` and the full architecture block, and
set `INFERENCE.MODEL_PATH` to the intended `.pth` state dict. The trainer checks
that the path exists, instantiates the model, loads the state dict, moves the
model to `DEVICE`, and evaluates test batches. It does not use
`TRAIN.MODEL_FILE_NAME` to locate the pretrained file. Keep `TRAIN` defaults
present when a trainer reads them during construction; PhysFormer's only-test
constructor in particular reads train-side resize defaults while building the
model, so state the effective geometry consistently rather than relying on
implicit defaults.

A checkpoint built under DataParallel may contain `module.` keys. Some source
trainers wrap the model before loading and FactorizePhys uses `strict=False`;
that does not make mismatched channels, frame depth, or spatial dimensions safe.
If the load reports missing/unexpected keys, first compare exact model spelling,
wrapper policy, model-specific config, and checkpoint provenance. Only then
perform a deliberate key-prefix conversion in a user-owned utility; never
rewrite the original checkpoint in place.

## Pseudo labels and motion augmentation

For data without high-fidelity synchronous PPG, the repository can use POS-based
pseudo labels that are band-limited and Hilbert-envelope normalized. Set the
exact key `PREPROCESS.USE_PSUEDO_PPG_LABEL: true` only when the selected loader
and experiment intend this weakly supervised contract. It provides a periodic
proxy, not the original morphology; record it in the experiment report.

Motion augmentation is an input-data operation performed outside this skill.
When already-generated augmented caches are supplied, the relevant split may
use `DATA_AUG: ['Motion']`; the config update may add an `MA-` prefix to model
file-name components. Do not generate motion data, download driving videos, or
silently mix augmented and unaugmented splits. Use [data-preparation](../../data-preparation/SKILL.md)
for cache provenance.

BigSmall is a separate pseudo-label/multitask route: use the BP4D+ BigSmall
loader, its two streams, 3-frame chunks, 144/9 spatial settings, 12 AU labels,
BVP, and respiration. Read the known missing scheduler/model-selection state in
[model-overview.md](model-overview.md) before attempting training.

## Outputs and evaluation handoff

Trainers compute metrics after reconstructing per-subject/per-chunk prediction
maps. With output saving enabled, the shared saver writes a pickle with:

- `predictions`: subject -> chunk index -> predicted signal/task values;
- `labels`: matching subject/chunk labels;
- `label_type`: test preprocessing label type;
- `fs`: test sampling rate.

Output pickle names are derived from the model file root and test dataset in
only-test mode, or the training model file name in train-and-test mode. The
shared config derives the saved-output directory under the test experiment log.
Use [evaluation-and-visualization](../../evaluation-and-visualization/SKILL.md)
for reading this schema, FFT/peak windows, Bland--Altman plots, and BigSmall
metrics. Do not duplicate evaluator implementation here.

## Safe model extension

A user-owned extension should proceed in this order:

1. Define a model with an explicit constructor and a synthetic tensor boundary.
2. Add a trainer that implements `__init__(config, data_loader)`, `train`,
   `valid`, `test`, and `save_model`; use `BaseTrainer.save_test_outputs` for
   the common pickle contract.
3. Add model defaults to config, exact dispatch branches to both `train_and_test`
   and `only_test`, and a train/infer YAML that states all geometry.
4. Add a deterministic construction/forward test using a tiny tensor and no
   dataset. Check output length, channels, dtype, device, and state-dict load.
5. Verify one cache boundary, one checkpoint route, and one evaluator handoff.

Keep experimental tests, source-relative imports, downloaded weights, and
vendor code outside the generated operating skill. A new backend requirement
must be explicit and must not degrade to a silent CPU path.

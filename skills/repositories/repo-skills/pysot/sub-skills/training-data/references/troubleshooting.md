# PySOT training/data troubleshooting

Start with the safe validator:

```bash
python scripts/validate_training_config.py \
  --repo-root <pysot-checkout> \
  --config <config.yaml> \
  --check-files
```

If the validator passes, remember it has not loaded every crop image or run CUDA training. Use the symptom sections below for the next check.

## Import and build issues

### `ModuleNotFoundError: No module named 'pysot'`

PySOT's `setup.py` defines the `toolkit` distribution and extension; the `pysot` package is normally imported from the checkout.

Fix patterns:

```bash
cd <pysot-checkout>
export PYTHONPATH=$PWD:${PYTHONPATH}
python tools/train.py --help
```

or install/use an editable-development style environment that places the checkout root on `PYTHONPATH`.

### `ImportError: cannot import name region` or extension build failures

The evaluation toolkit extension is built from the repository setup metadata. For legacy PySOT, Cython 3 can break the `toolkit.utils.region` extension; use `Cython<3` when building it.

```bash
pip install 'Cython<3'
python setup.py build_ext --inplace
```

Training itself does not use the region extension directly, but mixed workflows often run test/eval after training, so keep this in the environment troubleshooting path.

### `No module named tensorboardX`

`tools/train.py` imports `tensorboardX` before argument parsing. Install the documented runtime dependency before expecting even `--help` to work:

```bash
pip install tensorboardX yacs pyyaml tqdm colorama matplotlib opencv-python
```

## Config validation failures

### `size not match!`

`TrkDataset` raises this when:

```text
(TRAIN.SEARCH_SIZE - TRAIN.EXEMPLAR_SIZE) / ANCHOR.STRIDE + 1 + TRAIN.BASE_SIZE != TRAIN.OUTPUT_SIZE
```

Typical fixes:

- For default `SEARCH_SIZE=255`, `EXEMPLAR_SIZE=127`, `ANCHOR.STRIDE=8`, and `BASE_SIZE=8`, use `OUTPUT_SIZE=25`.
- For AlexNet-style configs with smaller output maps, verify all four terms together rather than editing only `OUTPUT_SIZE`.
- Re-run the bundled validator after changing search/exemplar/stride/base values.

### Anchor count mismatch

`ANCHOR.ANCHOR_NUM` must equal `len(ANCHOR.RATIOS) * len(ANCHOR.SCALES)`. If the config also sets `RPN.KWARGS.anchor_num`, keep it equal to the same value. A mismatch can surface later as head/label shape errors.

## Dataset path and JSON failures

### Missing `ROOT` or `ANNO`

If `DATASET.NAMES` includes a custom name, the base defaults do not help unless `DATASET.<NAME>` defines all required fields. Add:

```yaml
DATASET:
  NAMES: ['MYDATA']
  MYDATA:
    ROOT: 'training_dataset/mydata/crop511'
    ANNO: 'training_dataset/mydata/train.json'
    FRAME_RANGE: 1
    NUM_USE: -1
```

Then rerun the validator.

### Annotation JSON missing or stale

Signals:

- `FileNotFoundError` while loading `self.anno`;
- validator failure for `ANNO` with `--check-files`;
- a helper script generated `val.json` but the config points at `train.json` or `train2017.json`.

Fixes:

- Confirm the configured `ANNO` path under the checkout root.
- Regenerate the dataset JSON after changing raw data, symlinks, or crops.
- For VID, run `parse_vid.py` before `gen_json.py` because `gen_json.py` reads `vid.json`.

### Missing or unreadable crop images

Signals:

- `AttributeError: 'NoneType' object has no attribute 'shape'` or similar errors from `_get_bbox`/augmentation;
- OpenCV warnings from `cv2.imread`;
- training starts loading JSON but fails inside a DataLoader worker.

Fixes:

1. Pick a JSON entry `(video, track, frame)`.
2. Compute `<ROOT>/<video>/<frame:06d>.<track>.x.jpg`.
3. Verify that file exists and can be read by OpenCV.
4. If `.z.jpg` exists but `.x.jpg` does not, rerun the appropriate `par_crop.py`; training uses `.x.jpg`.

### All frames/tracks disappear after filtering

`SubDataset._filter_zero()` drops boxes with non-positive width or height. It then removes empty tracks and videos.

Signals:

- log warnings like `<video>/<track> has no frames` or `<video> has no tracks`;
- unexpectedly tiny dataset length;
- repeated sampling from too few videos.

Fixes:

- Inspect the JSON bboxes; for four-coordinate boxes, ensure `x2 > x1` and `y2 > y1`.
- Check whether a conversion script emitted `[x, y, w, h]` without converting to `[x1, y1, x2, y2]`. COCO helpers convert `bbox` to `[x, y, x+w, y+h]`; custom data must do the same.
- Rebuild the JSON after fixing coordinate conversion.

## Distributed/CUDA failures

### Direct `python tools/train.py --cfg ...` fails

`tools/train.py` calls distributed initialization and CUDA paths. A direct command often lacks `RANK`/`WORLD_SIZE` and still reaches `.cuda()`.

Use a launcher command from [training-workflow.md](training-workflow.md), for example:

```bash
CUDA_VISIBLE_DEVICES=0,1 \
python -m torch.distributed.launch \
  --nproc_per_node=2 \
  --master_port=2333 \
  tools/train.py --cfg experiments/<experiment>/config.yaml
```

### `KeyError: 'RANK'`, local-rank parsing, or NCCL init errors

- Use the legacy `python -m torch.distributed.launch` template for unmodified PySOT.
- Make sure the number of visible GPUs matches `--nproc_per_node`.
- Choose a free `--master_port`; for multi-node, confirm network connectivity and identical launch arguments on all nodes except `--node_rank`.
- If using `torchrun`, be prepared to patch PySOT for modern `LOCAL_RANK`/`--local-rank` conventions.

### CUDA not available or incompatible PyTorch

The historical installation guidance targeted Python 3.7-era PyTorch 0.4.1/CUDA 9.0 and Nvidia GPUs. Modern hosts may import PyTorch successfully but still not reproduce historical CUDA training behavior.

Do not claim full training verification from CPU-only config checks. If CUDA fails:

- confirm `python -c "import torch; print(torch.cuda.is_available(), torch.cuda.device_count())"`;
- check driver/runtime compatibility;
- use a PyTorch/CUDA stack that can run the target GPU and the PySOT code, or patch the legacy code deliberately.

## Pretrained/resume failures

### Backbone pretrained path missing

`BACKBONE.PRETRAINED` is resolved relative to the checkout root by `tools/train.py`. If set to `pretrained_models/resnet50.model`, the file must exist under that path before training.

### Resume checkpoint missing or incompatible

`TRAIN.RESUME` is asserted with `os.path.isfile`. Relative paths are relative to the launch CWD, not the config file. If the file exists but restore fails, compare model architecture keys, GPU count assumptions, and optimizer state with the original run.

### `size mismatch` or unexpected/missing state-dict keys

Check whether the config architecture matches the pretrained file:

- backbone type and used layers;
- RPN/head type and `anchor_num`;
- mask/refine settings;
- whether the file is a backbone-only model (`BACKBONE.PRETRAINED`) or a full training checkpoint (`TRAIN.PRETRAINED`/`TRAIN.RESUME`).

Route deeper architecture diagnosis to the sibling `configuration-models` sub-skill.

## Old dependency symptoms

- `np.float` errors in crop/augmentation scripts indicate a too-new NumPy for unpatched legacy code; use a compatible NumPy or patch aliases intentionally.
- OpenCV import/GUI problems are separate from training data validation; crop scripts need image IO, while training uses OpenCV to read crops.
- Full benchmark/test/eval after training needs snapshots and benchmark datasets; route result-format and metric failures to `evaluation-toolkit`.

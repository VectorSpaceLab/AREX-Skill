# Training and evaluation workflows

This reference distills the Torchreid 1.4.0 unified training/evaluation flow into self-contained operating steps. Use the bundled helper `../scripts/torchreid_train_eval.py` for command planning and config dry-runs; it does not run training.

## Workflow chooser

| Request | Primary choice | Critical settings | Verification before running |
| --- | --- | --- | --- |
| Train OSNet/ResNet on one image dataset | Image softmax workflow | `data.type image`, source=target, `loss.name softmax`, model key, dataset root | Dataset layout exists; generated config has `test.evaluate False` |
| Evaluate a checkpoint | Image/video test-only workflow | `model.load_weights`, `test.evaluate True`, target dataset(s), optional `test.visrank True` | Weight file exists; `visrank` only with evaluate/test-only |
| Cross-domain evaluation | Train on source, evaluate target(s) | `data.sources`, `data.targets`, often `color_jitter` not `random_erase` | Both source and target layouts exist |
| Multi-source training | Image/video data manager with multiple sources | `data.sources [a,b,...]`, optional `RandomDatasetSampler` | Every source dataset key/layout valid |
| Video ReID | `VideoDataManager` + video engine | `data.type video`, video dataset key, `video.seq_len`, `video.sample_method` | Tracklet metadata/layout exists; CPU is only a semantics check |
| Triplet training | Triplet engine | `loss.name triplet`, `sampler.train_sampler RandomIdentitySampler`, `sampler.num_instances` | Batch has enough identities/instances; model supports triplet output |
| Split-log aggregation | Bundled parser | Directory with split subdirectories and `test.log*` files | Run parser on a tiny fake log first if format is uncertain |
| Dataset mean/std | Bundled stats helper | Dataset root + image source key | Run `--check-only`; compute requires explicit `--compute` |

## Build command/config plans safely

The helper constructs unified Torchreid train/eval command plans using bundled templates and installed-package APIs.

### Same-domain OSNet training on Market1501

```bash
python scripts/torchreid_train_eval.py \
  --template im_osnet_x1_0_softmax_256x128_amsgrad_cosine \
  --mode train \
  --root /path/to/reid-data \
  --source market1501 \
  --target market1501 \
  --transforms random_flip random_erase \
  --save-dir log/osnet_x1_0_market1501_softmax_cosinelr \
  --dry-run
```

Expected important opts in the printed plan:

```text
data.root /path/to/reid-data
data.sources ['market1501']
data.targets ['market1501']
data.transforms ['random_flip', 'random_erase']
test.evaluate False
data.save_dir log/osnet_x1_0_market1501_softmax_cosinelr
```

### DukeMTMC-reID same-domain training

Use the same OSNet cosine template and override dataset/save-dir:

```bash
python scripts/torchreid_train_eval.py \
  --template im_osnet_x1_0_softmax_256x128_amsgrad_cosine \
  --mode train \
  --root /path/to/reid-data \
  --source dukemtmcreid \
  --target dukemtmcreid \
  --transforms random_flip random_erase \
  --save-dir log/osnet_x1_0_dukemtmcreid_softmax_cosinelr \
  --dry-run
```

### Evaluate a checkpoint with visrank

This is the most common difficult case. Evaluation must set `test.evaluate True`; `visrank` is valid only in this test-only mode.

```bash
python scripts/torchreid_train_eval.py \
  --template im_osnet_x1_0_softmax_256x128_amsgrad_cosine \
  --mode eval \
  --root /path/to/reid-data \
  --target market1501 \
  --weights /path/to/model.pth.tar-250 \
  --visrank \
  --save-dir log/eval_osnet_x1_0_market1501 \
  --dry-run
```

The plan must include all of these dotted opts:

```text
model.load_weights /path/to/model.pth.tar-250
test.evaluate True
test.visrank True
data.save_dir log/eval_osnet_x1_0_market1501
```

If the checkpoint path is missing, do not proceed to runtime evaluation. If using direct API code, load weights with `torchreid.utils.load_pretrained_weights(model, weight_path)` before `engine.run(test_only=True, ...)`.

### Cross-domain Duke to Market1501

The official examples use `random_flip color_jitter` for unseen-target generalization.

```bash
python scripts/torchreid_train_eval.py \
  --template im_osnet_x1_0_softmax_256x128_amsgrad \
  --mode train \
  --root /path/to/reid-data \
  --source dukemtmcreid \
  --target market1501 \
  --transforms random_flip color_jitter \
  --save-dir log/osnet_x1_0_duke2market_softmax \
  --dry-run
```

To test on both source and target, use multiple `--target` values:

```bash
--target dukemtmcreid market1501
```

### Multi-source image training

```bash
python scripts/torchreid_train_eval.py \
  --mode train \
  --data-type image \
  --model osnet_x1_0 \
  --root /path/to/reid-data \
  --source market1501 dukemtmcreid cuhk03 msmt17 \
  --target market1501 dukemtmcreid cuhk03 msmt17 \
  --train-sampler RandomDatasetSampler \
  --num-datasets 2 \
  --batch-size 64 \
  --save-dir log/osnet_multisource \
  --dry-run
```

For `RandomDatasetSampler`, the training batch is divided evenly across `sampler.num_datasets`; choose a batch size divisible by that number.

### Video ReID planning

Use video keys such as `mars`, `ilidsvid`, `prid2011`, or `dukemtmcvidreid`.

```bash
python scripts/torchreid_train_eval.py \
  --mode train \
  --data-type video \
  --model resnet50 \
  --root /path/to/reid-data \
  --source mars \
  --target mars \
  --batch-size 3 \
  --test-batch-size 3 \
  --seq-len 15 \
  --sample-method evenly \
  --save-dir log/resnet50_softmax_mars \
  --dry-run
```

For `sample_method all`, set the effective video batch size to 1 because each tracklet can produce a different number of frames.

## Direct API recipe: image softmax

Use this when the task requires a Python implementation instead of a command plan. Replace dataset and compute paths deliberately; this recipe can train if executed.

```python
import torch
import torchreid

use_gpu = torch.cuda.is_available()

datamanager = torchreid.data.ImageDataManager(
    root="/path/to/reid-data",
    sources="market1501",
    targets="market1501",
    height=256,
    width=128,
    transforms=["random_flip", "random_erase"],
    batch_size_train=64,
    batch_size_test=300,
    workers=4,
    train_sampler="RandomSampler",
    use_gpu=use_gpu,
)

model = torchreid.models.build_model(
    name="osnet_x1_0",
    num_classes=datamanager.num_train_pids,
    loss="softmax",
    pretrained=True,
    use_gpu=use_gpu,
)
if use_gpu:
    model = model.cuda()

optimizer = torchreid.optim.build_optimizer(
    model,
    optim="amsgrad",
    lr=0.0015,
    weight_decay=5e-4,
)
scheduler = torchreid.optim.build_lr_scheduler(
    optimizer,
    lr_scheduler="cosine",
    max_epoch=250,
)

engine = torchreid.engine.ImageSoftmaxEngine(
    datamanager,
    model,
    optimizer=optimizer,
    scheduler=scheduler,
    use_gpu=use_gpu,
    label_smooth=True,
)
engine.run(
    save_dir="log/osnet_x1_0_market1501_softmax_cosinelr",
    max_epoch=250,
    fixbase_epoch=10,
    open_layers=["classifier"],
    eval_freq=-1,
    print_freq=20,
    test_only=False,
)
```

## Direct API recipe: checkpoint evaluation

```python
import os
import torch
import torchreid

weight_path = "/path/to/model.pth.tar"
if not os.path.isfile(weight_path):
    raise FileNotFoundError(weight_path)

use_gpu = torch.cuda.is_available()

datamanager = torchreid.data.ImageDataManager(
    root="/path/to/reid-data",
    sources="market1501",
    targets="market1501",
    height=256,
    width=128,
    transforms=None,
    batch_size_train=64,
    batch_size_test=300,
    use_gpu=use_gpu,
)
model = torchreid.models.build_model(
    name="osnet_x1_0",
    num_classes=datamanager.num_train_pids,
    loss="softmax",
    pretrained=False,
    use_gpu=use_gpu,
)
torchreid.utils.load_pretrained_weights(model, weight_path)
if use_gpu:
    model = model.cuda()

optimizer = torchreid.optim.build_optimizer(model, optim="amsgrad", lr=0.0015)
scheduler = torchreid.optim.build_lr_scheduler(optimizer, lr_scheduler="cosine", max_epoch=250)
engine = torchreid.engine.ImageSoftmaxEngine(datamanager, model, optimizer, scheduler=scheduler, use_gpu=use_gpu)
engine.run(
    save_dir="log/eval_osnet_x1_0_market1501",
    test_only=True,
    dist_metric="euclidean",
    normalize_feature=False,
    visrank=True,
    visrank_topk=10,
    ranks=[1, 5, 10, 20],
)
```

## Triplet-loss recipe constraints

Triplet engines expect the model built with `loss="triplet"` and usually require identity-balanced batches.

```python
datamanager = torchreid.data.ImageDataManager(
    root="/path/to/reid-data",
    sources="market1501",
    targets="market1501",
    train_sampler="RandomIdentitySampler",
    num_instances=4,
    batch_size_train=64,
)
model = torchreid.models.build_model(
    name="resnet50",
    num_classes=datamanager.num_train_pids,
    loss="triplet",
    pretrained=True,
)
engine = torchreid.engine.ImageTripletEngine(
    datamanager,
    model,
    optimizer,
    margin=0.3,
    weight_t=1.0,
    weight_x=1.0,
    scheduler=scheduler,
)
```

Avoid `fixbase_epoch > 0` when pure triplet loss has `loss.triplet.weight_x == 0`; the unified config check rejects this because classifier outputs are not in the computational graph.

## Resume, fine-tune, and two-stepped transfer

- **Resume interrupted training**: set `model.resume /path/to/checkpoint.pth.tar` or call `torchreid.utils.resume_from_checkpoint(path, model, optimizer, scheduler)` and pass the returned `start_epoch` to `engine.run`.
- **Load weights for fine-tuning**: set `model.load_weights /path/to/weights.pth.tar` or call `torchreid.utils.load_pretrained_weights`; keep `test.evaluate False` for continued training.
- **Two-stepped transfer learning**: set `train.fixbase_epoch N` and `train.open_layers ['classifier']` or `['fc', 'classifier']`. The fixed-base epochs are counted inside `train.max_epoch`.
- **Staged learning rate**: set `train.staged_lr True`, `train.new_layers ['classifier']`, and `train.base_lr_mult 0.1` so base layers use `lr * base_lr_mult`.

## Mean/std workflow

First check prerequisites without constructing a Torchreid dataset:

```bash
python scripts/compute_mean_std.py /path/to/reid-data market1501 --check-only
```

Only compute when the local dataset is present and the user accepts the cost:

```bash
python scripts/compute_mean_std.py /path/to/reid-data market1501 --compute --batch-size 100 --workers 4
```

The computation uses image training data with normalization mean `[0, 0, 0]` and std `[1, 1, 1]`, then averages per-batch channel mean/std.

## Split-log parsing workflow

Expected layout:

```text
log/eval_dataset/
  split_0/test.log-YYYY-mm-dd-HH-MM-SS
  split_1/test.log-YYYY-mm-dd-HH-MM-SS
  ...
```

Run:

```bash
python scripts/parse_test_results.py log/eval_dataset
```

The parser recognizes lines like:

```text
mAP: 76.5%
Rank-1  : 88.8%
Rank-5  : 95.0%
Rank-10 : 97.0%
Rank-20 : 98.0%
```

Use `--strict` when a missing split log should fail the command instead of being reported and skipped.

# Gluon Workflows

Use these workflows only when the user has or intentionally wants an MXNet Gluon setup. Gluon was optional and not installed in the minimum inspected environment, so every executable step is conditional.

## Safe local smoke workflow

Purpose: confirm that a user's installed MXNet and installed `resnest.gluon` package can build a model and run a forward pass without downloading weights or touching datasets. Bundled helper: [`../scripts/gluon_tiny_inference.py`](../scripts/gluon_tiny_inference.py). Launch it by path from any current working directory after installing ResNeSt in the same Python environment as MXNet.

```bash
python <gluon-models-skill-root>/scripts/gluon_tiny_inference.py --model resnest50 --batch-size 1 --image-size 64 --ctx cpu
```

Expected result when MXNet is available: the script prints a JSON object containing the model name, context, input shape, and output shape. For `classes=1000`, the output shape should be `[batch_size, 1000]`.

Expected result when MXNet is missing: the script exits cleanly with a short message explaining that Gluon checks are skipped until MXNet is installed.

Use `--pretrained` only when downloads or a populated cache are acceptable:

```bash
python <gluon-models-skill-root>/scripts/gluon_tiny_inference.py --model resnest50 --pretrained --root ~/.mxnet/models --ctx cpu
```

That mode may download a zip archive and verify SHA-1 before loading `.params`. Keep no-pretrained smoke passing before debugging pretrained cache issues.

## Minimal Gluon API inference pattern

```python
import mxnet as mx
from resnest.gluon import get_model

ctx = mx.cpu(0)
net = get_model('resnest50', pretrained=False, ctx=ctx, classes=1000)
net.initialize(ctx=ctx)
net.hybridize()
x = mx.nd.random.uniform(shape=(1, 3, 224, 224), ctx=ctx)
y = net(x)
assert tuple(y.shape) == (1, 1000)
```

Key points:

- Initialize manually when `pretrained=False`; otherwise the first forward fails with uninitialized parameters.
- With `pretrained=True`, the factory loads parameters and should not be manually initialized afterward.
- Keep `classes=1000` for released ImageNet parameters.
- Use `ctx=mx.gpu(0)` only with a CUDA-enabled MXNet wheel matching the machine CUDA stack.

## ImageNet validation recipe

The Gluon validation recipe is for measuring published classifier accuracy and throughput, not for a default smoke check.

Inputs:

- A compatible MXNet installation.
- `resnest` importable with `resnest.gluon`.
- PIL and GluonCV if validating from raw ImageNet image directories.
- Either raw ImageNet validation images in an ImageNet classification layout, or RecordIO validation files.
- Optional CUDA devices if using `--num-gpus > 0`.

Important arguments and semantics:

| Argument idea | Meaning |
|---|---|
| `--model resnest50` | Any local Gluon model name from the API reference. |
| `--crop-size 224` | Input crop; published core models use 224/256/320/416 depending on model. |
| `--crop-ratio 0.875` | Validation resize is `ceil(crop_size / crop_ratio)` for ordinary center crop. |
| `--num-gpus 0` | CPU validation. Values above 0 split batches across `mx.gpu(i)`. |
| `--batch-size 32` | Per-device batch size before multiplying by number of GPUs. |
| `--data-dir <imagenet-root>` | Raw-image validation root for GluonCV ImageNet loading. |
| `--rec-dir <recordio-root>` | Directory containing `val.rec` and usually `val.idx`; takes precedence over raw images. |
| `--resume <params>` | Load a local `.params` file instead of using `pretrained=True`. |
| `--dilation <n>` | Pass dilation into the model builder for stride/dense variants. |
| `--dtype float32` | Data type for inference. `float16` requires appropriate backend support. |

Validation transform summary:

- Normalize with ImageNet mean `[0.485, 0.456, 0.406]` and std `[0.229, 0.224, 0.225]`.
- For crop sizes below 320: resize with aspect ratio, center crop, convert to tensor, normalize.
- For crop sizes 320 and above: convert to PIL, use extended center crop, convert back to NDArray/tensor, normalize.
- Metrics are top-1 and top-5 error; throughput is measured after a short warm-up.

Use RecordIO for fair throughput comparisons. The public project note says paper inference speed was measured with the Gluon implementation and RecordIO data, while raw-image validation is simpler but not throughput-equivalent.

## RecordIO data expectations

For Gluon validation with `--rec-dir`, the validation RecordIO directory should contain:

```text
<recordio-root>/
  val.rec
  val.idx
```

For Gluon training, RecordIO is effectively required. The training recipe expects:

```text
<recordio-root>/
  train.rec
  train.idx
  val.rec
  val.idx
```

Keep the data path on fast local storage. Copying data to RAM disk was an optional performance optimization in the source recipe, not a correctness requirement and not safe as a default automated action.

## Distributed Gluon training recipe, reference-only

The Gluon training recipe is a multi-host or multi-GPU ImageNet workflow. Do not run it as a default verification case and do not install Horovod/MPI/CUDA automatically.

Prerequisites before constructing a real command:

- MXNet build matching the requested CPU or CUDA backend.
- Horovod with MXNet support and MPI launcher if using distributed execution.
- RecordIO ImageNet train and validation files.
- Enough GPU memory, storage bandwidth, and wall-clock budget.
- Agreement on save directory, resume files, world size, hosts, and whether networked filesystems are involved.

Command shape to interpret or adapt for a user's own launcher:

```bash
horovodrun -np <world-size> --hostfile <hosts-file> \
  python <gluon-training-entrypoint>.py \
  --use-rec \
  --rec-train <recordio-root>/train.rec \
  --rec-val <recordio-root>/val.rec \
  --model resnest50 \
  --lr 0.05 \
  --num-epochs 270 \
  --batch-size 128 \
  --dtype float32 \
  --warmup-epochs 5 \
  --last-gamma \
  --no-wd \
  --label-smoothing \
  --mixup \
  --save-dir <params-output-dir> \
  --log-interval 50 \
  --eval-frequency 5 \
  --auto_aug \
  --input-size 224
```

Training semantics distilled from the recipe:

- Horovod initializes `size`, `rank`, and `local_rank`; by default each rank is pinned to `mx.gpu(local_rank)`, unless CPU mode is explicitly chosen.
- The learning rate uses cosine scheduling and scales the base LR by the number of workers.
- Data loading uses a split sampler so each rank reads its partition of RecordIO data.
- `--last-gamma`, `--label-smoothing`, `--mixup`, `--auto_aug`, `--no-wd`, and DropBlock are training tricks used by the published recipe.
- Training saves model parameters and trainer states periodically; resuming requires both parameter and state paths when continuing optimizer state.
- Evaluation, when enabled, computes accuracy/top-5 and gathers metrics across MPI ranks when MPI is available.

## Choosing crop sizes

| Model | Published validation crop |
|---|---|
| `resnest50` | 224 |
| `resnest101` | 256 |
| `resnest200` | 320 |
| `resnest269` | 416 |
| `resnest50_fast_*` | 224 unless the user's experiment says otherwise |

Use smaller synthetic image sizes only for smoke tests. For real pretrained accuracy checks, match the published crop size and preprocessing.

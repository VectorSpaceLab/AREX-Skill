# Training CLI reference

The six legacy training entry points use `argparse` and expose the same
controls except that the segmentation example names its CSV option
`--train_csv`. The following help probe is safe and should be the first
application command in a compatible environment:

```bash
cd <application-directory>
python train.py --help
```

The installed TensorFlow 1.15.0 probe returned exit status 0 for all six
parsers. A modern TensorFlow environment may fail before parsing because the
scripts import DLTK networks at module import time; that is a compatibility
failure, not a reason to patch the application in place.

## Exact option sets

### Five standard options

Age regression, sex classification, feature-only CAE, artificial
super-resolution, and the custom LSGAN use:

```text
usage: train.py [-h] [--run_validation RUN_VALIDATION] [--restart] [--verbose]
                [--cuda_devices CUDA_DEVICES] [--model_path MODEL_PATH]
                [--data_csv DATA_CSV]
```

A checked, data-bound invocation has this form:

```bash
python train.py \
  --model_path /absolute/path/to/a/new-or-approved-run \
  --data_csv /absolute/path/to/a/validated.csv \
  --cuda_devices ""
```

The `--data_csv` filename is the IXI demographic CSV for the five recipes.
The GAN uses the same option even though it consumes image slices and noise.
Use `--cuda_devices 0` or another explicitly approved device string when a
GPU is available; an empty string is the explicit CPU choice for these legacy
scripts.

### Segmentation option set

The MRBrainS segmentation example uses:

```text
usage: train.py [-h] [--run_validation RUN_VALIDATION] [--restart] [--verbose]
                [--cuda_devices CUDA_DEVICES] [--model_path MODEL_PATH]
                [--train_csv TRAIN_CSV]
```

A checked invocation has this form:

```bash
python train.py \
  --model_path /absolute/path/to/a/new-or-approved-run \
  --train_csv /absolute/path/to/a/validated-training.csv \
  --cuda_devices ""
```

The CSV rows must resolve to the registered subject folders expected by the
reader. A placeholder or credential-gated CSV is not a smoke fixture.

## Flag semantics and safe gates

| Flag | Historical default | Meaning and gate |
|---|---:|---|
| `--run_validation RUN_VALIDATION` | `True` | A value-taking argument, not a boolean switch. Omit it for the default. Passing the string `False` remains truthy in Python and does not reliably disable validation; change code only in a reviewed copy if disabling is required. |
| `--restart` | off | The examples implement this with recursive shell deletion. Reject it. Use a new model directory or an approved archive/rename instead. |
| `--verbose` | off | Raises TensorFlow logging verbosity and lowers the TensorFlow C++ log suppression. It does not make a run bounded. |
| `--cuda_devices`, `-c` | `0` | Sets `CUDA_VISIBLE_DEVICES` inside the script. Choose an existing GPU explicitly or pass an empty string for a CPU check. |
| `--model_path`, `-p` | recipe-specific historical default | Checkpoint, event, evaluation-summary, and export base. Prefer an absolute, unique path and inspect existing checkpoints before reuse. |
| `--data_csv` | recipe-specific IXI relative path | CSV for all applications except segmentation. Resolve it explicitly; do not rely on the caller's current directory. |
| `--train_csv` | `mrbrains.csv` | Segmentation CSV. Resolve subject folders and registration access before running. |

The scripts set NumPy and TensorFlow seeds inside `train`, but readers may
still perform random patch extraction and crop selection. Reproducibility is
therefore limited to a controlled environment and does not imply identical
medical predictions.

## Recommended command progression

Use the following gates, stopping at the first failure:

```bash
python train.py --help
python - <<'PY'
import tensorflow as tf
from dltk.version import __version__
assert tf.__version__.startswith('1.')
assert __version__ == '0.2.1'
assert all(hasattr(tf, x) for x in ('Session', 'layers', 'contrib', 'estimator'))
print('legacy training API is present')
PY
# Only after a tiny fixture or reviewed data check:
python train.py --model_path /absolute/path/to/new-run --data_csv /absolute/path/to/data.csv --cuda_devices ""
```

Do not add `--restart` to the last command. To resume, point the same command
at a compatible existing directory and verify its latest global step first.
To start over, change only `--model_path` to a path confirmed not to contain a
checkpoint. Full defaults are intentionally large: 50,000 steps for age,
classification, and segmentation; 100,000 for CAE; 250,000 for super-
resolution; and 35,000 for LSGAN. The applications have no general-purpose
`--steps` limit, so bounded verification belongs in the bundled synthetic
smoke, not in a full application invocation.

## Monitoring command

After a run has written events, use:

```bash
tensorboard --logdir /absolute/path/to/run
```

This is read-only with respect to checkpoints but may create TensorBoard
cache files depending on the installation. Point it at a dedicated run, not a
shared model directory. Evaluation summaries in the examples are placed
under an `eval` child directory; inspect both that child and the training
log when comparing steps.

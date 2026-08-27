# BAPPS Training Workflows

## Purpose

Read this when you need the exact command shape for training, fine-tuning, or checkpoint smoke tests.

## Smoke fixture first

Before running a training smoke test, create a tiny fixture:

```bash
python skills/disco/perceptual-similarity/scripts/make_tiny_bapps_fixture.py --output-root /tmp/perceptual-similarity-fixture
```

Then point the training helper at `/tmp/perceptual-similarity-fixture/dataset`.

## Bundled training helper

Run a bounded smoke train with the default tiny step limit:

```bash
python skills/disco/perceptual-similarity/sub-skills/bapps-training/scripts/train_bapps.py
```

Train on the official BAPPS training splits:

```bash
python skills/disco/perceptual-similarity/sub-skills/bapps-training/scripts/train_bapps.py \
  --dataset_root dataset \
  --datasets train/traditional train/cnn train/mix \
  --name alex_smoke
```

Useful flags:

- `--model lpips|baseline|l2|ssim`
- `--net squeeze|alex|vgg`
- `--from_scratch`
- `--train_trunk`
- `--epochs N`
- `--max_steps N` (`0` means no step limit)
- `--save_every N`
- `--print_every N`
- `--checkpoints_dir path`

## Train-then-score wrapper

The wrapper mirrors the old repo flow but uses the bundled helpers:

```bash
python skills/disco/perceptual-similarity/sub-skills/bapps-training/scripts/train_test_metric.sh smoke alex
```

Wrapper configuration uses environment variables when needed:

- `DATASET_ROOT`
- `TRAIN_DATASETS`
- `VAL_DATASETS`
- `MODEL`
- `VERSION`
- `BATCH_SIZE`
- `EPOCHS`
- `MAX_STEPS`
- `CHECKPOINTS_DIR`
- `USE_GPU`
- `FROM_SCRATCH`
- `TRAIN_TRUNK`
- `LR`
- `BETA1`

## Scratch and tune variants

- `scripts/train_test_metric_scratch.sh` sets `FROM_SCRATCH=1` and `TRAIN_TRUNK=1`.
- `scripts/train_test_metric_tune.sh` sets `TRAIN_TRUNK=1`.

## Checkpoint outputs

The bundled helper writes checkpoints under:

```text
<checkpoints_dir>/<name>/
```

Typical files:

- `latest_net_.pth`
- `latest_net_rank.pth`
- `<epoch>_net_.pth`
- `<epoch>_net_rank.pth`
- `train_log.txt`

## Smoke-test expectations

For a tiny fixture, a one-step run should:

- create the checkpoint directory,
- print loss and ranking accuracy,
- save a latest checkpoint,
- and exit cleanly without needing the old HTML/visdom stack.

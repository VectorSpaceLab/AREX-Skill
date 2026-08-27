# Training CLI Reference

## Bundled training runtime flags

| Flag | Required | Default | Meaning |
| --- | --- | --- | --- |
| `--checkpoint-dir CHECKPOINT_DIR` | yes | none | Existing directory where TensorFlow checkpoints are saved. |
| `--style STYLE` | yes | none | Style image path. |
| `--train-path TRAIN_PATH` | no | `data/train2014` | Directory of content training images. |
| `--test TEST` | no | false | Optional content image used for checkpoint previews. |
| `--test-dir TEST_DIR` | required if `--test` set | false | Existing directory for preview images. |
| `--slow` | no | false | Debugging direct optimization path; not normal fast training. |
| `--epochs EPOCHS` | no | `2` | Number of passes over training targets. Must be positive. |
| `--batch-size BATCH_SIZE` | no | `4` | Training batch size. Must be positive. |
| `--checkpoint-iterations CHECKPOINT_ITERATIONS` | no | `2000` | Iteration interval for printing and checkpointing. Must be positive. |
| `--vgg-path VGG_PATH` | no | `data/imagenet-vgg-verydeep-19.mat` | VGG network `.mat` path. |
| `--content-weight CONTENT_WEIGHT` | no | `7.5` | Non-negative content loss weight. |
| `--style-weight STYLE_WEIGHT` | no | `100.0` | Non-negative style loss weight. |
| `--tv-weight TV_WEIGHT` | no | `200.0` | Non-negative total-variation weight. |
| `--learning-rate LEARNING_RATE` | no | `0.001` | Non-negative Adam learning rate. |

The bundled training runtime's `check_opts` asserts that required paths exist and that numeric values are in range before training begins.

## `optimize.optimize` signature

Verified source/inspection signature:

```python
optimize.optimize(
    content_targets,
    style_target,
    content_weight,
    style_weight,
    tv_weight,
    vgg_path,
    epochs=2,
    print_iterations=1000,
    batch_size=4,
    save_path='saver/fns.ckpt',
    slow=False,
    learning_rate=0.001,
    debug=False,
)
```

It is a generator yielding `(preds, losses, i, epoch)` at print/checkpoint intervals. In the normal path it saves checkpoints through a `Saver`; in slow mode it optimizes pixel values directly.

## Important defaults and constants

| Constant | Value |
| --- | --- |
| `CONTENT_WEIGHT` | `7.5e0` |
| `STYLE_WEIGHT` | `1e2` |
| `TV_WEIGHT` | `2e2` |
| `LEARNING_RATE` | `1e-3` |
| `NUM_EPOCHS` | `2` |
| `CHECKPOINT_ITERATIONS` | `2000` |
| `VGG_PATH` | `data/imagenet-vgg-verydeep-19.mat` |
| `TRAIN_PATH` | `data/train2014` |
| `BATCH_SIZE` | `4` |
| `DEVICE` | `/gpu:0` |

The `DEVICE` constant is not exposed as a bundled training flag in the inspected script; training code uses TensorFlow sessions without a top-level device option.

## Validator helper mapping

The bundled `scripts/validate_training_inputs.py` mirrors the path and numeric checks but does not import TensorFlow or train. It adds JSON reporting and image sampling so agents can diagnose likely failures before launching the expensive script.

# YOLOX Training Workflows

This reference covers training/evaluation commands, distributed flags, image-size controls, freezing, assignment visualization, and metric loggers. Full training/evaluation requires suitable datasets, checkpoints when requested, and accelerator resources.

## Command patterns

| Goal | Command pattern | Notes |
|---|---|---|
| Train packaged default | `python -m yolox.tools.train -n yolox-s -d 1 -b 8 --fp16` | `-n` accepts `yolox-s`, `yolox-m`, `yolox-l`, `yolox-x`, `yolox-tiny`, `yolox-nano`, `yolov3`. |
| Train custom Exp | `python -m yolox.tools.train -f path/to/exp.py -d 1 -b 8 -c pretrained.pth` | Use for custom data, class counts, sizes, model variants, freezing, evaluators. |
| Resume training | `python -m yolox.tools.train -f path/to/exp.py --resume -c latest_ckpt.pth -e 42` | Resume checkpoints need optimizer/training state; fine-tune weights do not. |
| Evaluate checkpoint | `python -m yolox.tools.eval -f path/to/exp.py -c best_ckpt.pth -b 8 -d 1 --conf 0.001 --fp16 --fuse` | Match checkpoint, Exp, evaluator, and dataset. |
| Visualize assignment | `python -m yolox.tools.visualize_assign -f path/to/exp.py -d 1 -b 8 --max-batch 2` | Reference-only diagnostic that starts the training dataloader/model and exits after a few batches. |
| Inspect config only | `python scripts/inspect_yolox_exp.py --name yolox-s --expected-format none` | Run from this sub-skill directory; never starts training. |

## Train CLI flags

| Flag | Meaning | Guidance |
|---|---|---|
| `-n, --name` | Built-in experiment name | Hyphens map to default modules such as `yolox_s`. |
| `-f, --exp_file` | Python file containing class `Exp` | Use for custom data/classes/evaluator/freezing/architecture. |
| `-expn, --experiment-name` | Output run name | Defaults to `exp.exp_name`. |
| `-d, --devices` | Number of GPU processes | Requested count must not exceed visible devices. |
| `-b, --batch-size` | Total batch size | Common starting point is `devices * 8`; tune for memory and labels. |
| `--fp16` | Mixed precision | Requires compatible CUDA AMP. |
| `--cache [ram|disk]` | Cache images | Bare `--cache` means RAM; `--cache disk` needs writable space. |
| `--resume` | Resume full training state | Use only with YOLOX training checkpoints. |
| `-c, --ckpt` | Checkpoint | Fine-tune weights without `--resume`; resume state with `--resume`. |
| `--dist-url`, `--num_machines`, `--machine_rank` | Distributed setup | Multi-node needs a reachable shared URL and unique ranks. |
| `-l, --logger` | `tensorboard`, `mlflow`, or `wandb` | W&B/MLflow need optional packages and credentials/services. |
| trailing `opts` | Existing `Exp` key/value overrides | Must be even-length pairs; quote tuples/lists. |

## Eval flags

`python -m yolox.tools.eval` loads the `Exp`, merges trailing `opts`, constructs model/evaluator, loads checkpoint unless `--speed` or `--trt`, then evaluates. Use `--conf`, `--nms`, `--tsize`, `--fp16`, `--fuse`, `--legacy`, `--test`, and `--speed` deliberately. TensorRT eval requires a generated `model_trt.pth`, batch size 1, no distributed eval, and no fuse.

## Custom Exp workflow

1. Subclass `yolox.exp.Exp` or a packaged default Exp.
2. Set `num_classes`, `depth`, `width`, `input_size`, `test_size`, and `exp_name` in `__init__`.
3. Override `get_dataset(self, cache=False, cache_type="ram")` for training data.
4. Override `get_eval_dataset(self, **kwargs)` for non-standard eval splits.
5. Override `get_evaluator(self, batch_size, is_distributed, testdev=False, legacy=False)` for VOC/custom metrics.
6. Override `get_data_loader(...)` only when the standard mosaic/data-loader behavior is insufficient, and preserve the cache contract.

## Image-size controls

- `input_size` and `test_size` are `(height, width)` and should usually match.
- Values should be multiples of 32.
- Default 640 models use `(640, 640)`; tiny/nano use `(416, 416)`.
- If `random_size` is absent, `multiscale_range=5` around 640 yields 480–800.
- For single-scale training set `multiscale_range = 0` and do not set `random_size`.

## Freezing and assignment visualization

Freeze inside `Exp.get_model()` after constructing the model:

```python
class Exp(MyExp):
    def get_model(self):
        from yolox.utils import freeze_module
        model = super().get_model()
        freeze_module(model.backbone.backbone)  # backbone body only
        return model
```

Assignment visualization uses the training parser and a custom trainer that exits after `--max-batch`. It helps inspect mosaic/mixup and unmatched boxes but still needs data, model, and GPU resources like a short training start.

## Loggers

- `tensorboard`: default local scalar logging.
- `wandb`: install/authenticate W&B, use `--logger wandb`, pass `wandb-*` options after known CLI flags.
- `mlflow`: install `mlflow` and `python-dotenv`, configure tracking URI/experiment/model artifact environment variables.

Logger failures are usually package, credentials, network/service, permission, or trailing-option spelling problems before they are model bugs.

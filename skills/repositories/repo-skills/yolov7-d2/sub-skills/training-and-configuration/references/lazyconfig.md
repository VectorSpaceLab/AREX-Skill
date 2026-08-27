# LazyConfig Workflows

YOLOv7-d2 includes Detectron2 LazyConfig examples under Python config files. Use the LazyConfig training launcher pattern for these files.

## Expected config fields

A LazyConfig training config should define:

- `model`: instantiable Detectron2 model object.
- `dataloader.train`, `dataloader.test`, and optionally `dataloader.evaluator`.
- `optimizer` with `optimizer.params.model` set during launch.
- `lr_multiplier` scheduler.
- `train`: output directory, init checkpoint, device, AMP flag, max iter, eval/log periods, DDP/checkpointer settings.

## Command shape

```bash
python tools/lazyconfig_train_net.py --config-file path/to/config.py --num-gpus 1 train.init_checkpoint=path/to/model.pth train.device=cuda
```

Use `--eval-only` for evaluation:

```bash
python tools/lazyconfig_train_net.py --config-file path/to/config.py --eval-only train.init_checkpoint=path/to/model.pth
```

## Do not rely on the LazyConfig demo without checking it

The distilled source `demo_lazyconfig.py` contains a module-level bare `q`, causing a `NameError` before argument parsing. If the user wants LazyConfig visualization, remove that line in their working copy or create a small predictor script from the LazyConfig model pattern. Do not treat this failure as a missing dependency.

## LazyConfig versus Yacs overrides

- Yacs/YAML configs use trailing `KEY VALUE` overrides.
- LazyConfig uses dotted assignment syntax like `train.device=cpu` or `dataloader.test.num_workers=1`.
- Avoid mixing both syntaxes in one command.

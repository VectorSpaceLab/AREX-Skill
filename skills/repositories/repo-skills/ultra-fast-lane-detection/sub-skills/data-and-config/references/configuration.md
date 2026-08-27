# Configuration

## Purpose

Read this when you need to map a user request onto the repo's CULane or TuSimple config files and command-line overrides.

## Verified config files

- `configs/culane.py`
- `configs/tusimple.py`

Both are Python config files loaded through `utils.config.Config.fromfile(...)`.

## Shared override behavior

The repo's command-line parser lets users override selected config fields without editing the config file itself. The most frequently used fields are:

- `dataset`
- `data_root`
- `epoch`
- `batch_size`
- `optimizer`
- `learning_rate`
- `weight_decay`
- `momentum`
- `scheduler`
- `steps`
- `gamma`
- `warmup`
- `warmup_iters`
- `backbone`
- `griding_num`
- `use_aux`
- `sim_loss_w`
- `shp_loss_w`
- `note`
- `log_path`
- `finetune`
- `resume`
- `test_model`
- `test_work_dir`
- `num_lanes`

## Default values that matter

### CULane

- `dataset='CULane'`
- `griding_num=200`
- `use_aux=True`
- `backbone='18'`
- `epoch=50`
- `optimizer='SGD'`
- `scheduler='multi'`
- `num_lanes=4`

### TuSimple

- `dataset='Tusimple'`
- `griding_num=100`
- `use_aux=True`
- `backbone='18'`
- `epoch=100`
- `optimizer='Adam'`
- `scheduler='cos'`
- `num_lanes=4`

## Practical command pattern

A user usually starts from one of the configs and overrides only the environment-dependent fields:

```bash
python train.py configs/culane.py --data_root <CULANE_ROOT> --log_path <LOG_DIR>
python train.py configs/tusimple.py --data_root <TUSIMPLE_ROOT> --log_path <LOG_DIR>
```

Add the minimum extra overrides needed for the run, such as `--batch_size`, `--backbone`, `--resume`, or `--finetune`.

## Config and CLI pitfalls

- `use_aux` is parsed as a boolean-like flag, so pass a clear true/false value when overriding it.
- `log_path` should point outside the repository tree if you do not want the auto-backup logic to copy a large working directory.
- `data_root` must match the documented CULane or TuSimple folder layout exactly.
- The repo does not auto-discover dataset paths; missing or wrong roots surface as runtime file errors later.

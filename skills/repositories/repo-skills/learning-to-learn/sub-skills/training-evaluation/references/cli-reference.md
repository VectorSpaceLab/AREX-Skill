# CLI reference

This sub-skill covers the public training and evaluation entry points in the
repo root.

## Training

Canonical form:

```bash
python train.py --problem=simple --num_epochs=1 --num_steps=2 --unroll_length=1 --log_period=1 --evaluation_period=999999
```

| Flag | Source default | Notes |
| --- | --- | --- |
| `save_path` | `None` | Fresh directory for the best saved optimizer. The script creates it and aborts if it already exists. |
| `num_epochs` | `10000` | Outer training epochs. Each epoch resets the optimizee and optimizer state. |
| `log_period` | `100` | Epoch cadence for `util.print_stats(...)`. |
| `evaluation_period` | `1000` | Epoch cadence for the evaluation loop inside training. |
| `evaluation_epochs` | `20` | Number of fresh evaluation passes per evaluation event. |
| `problem` | `simple` | Problem factory name passed to `util.get_config(...)`. |
| `num_steps` | `100` | Total optimizee steps per epoch, before unroll truncation. |
| `unroll_length` | `20` | Number of steps per meta-unroll. |
| `learning_rate` | `0.001` | Adam learning rate for the outer meta-optimizer. |
| `second_derivatives` | `False` | Enables second derivatives through the optimizee loss. |

### Save behavior
- `train.py` creates `save_path` before training starts.
- If the directory already exists, training stops with `ValueError`.
- When evaluation improves, the script deletes the previous files in that
  directory and writes the new best optimizer as `.l2l` files.
- File names follow the network ids from `util.get_config(...)`.

## Evaluation

Canonical forms:

```bash
python evaluate.py --problem=simple --optimizer=Adam --num_epochs=1 --num_steps=2
python evaluate.py --problem=simple --optimizer=L2L --num_epochs=1 --num_steps=2
```

| Flag | Source default | Notes |
| --- | --- | --- |
| `optimizer` | `L2L` | `Adam` or `L2L`. |
| `path` | `None` | Directory that contains saved `.l2l` files for L2L reloads. |
| `num_epochs` | `100` | Number of fresh evaluation epochs. |
| `seed` | `None` | TensorFlow RNG seed. |
| `problem` | `simple` | Problem factory name passed to `util.get_config(...)`. |
| `num_steps` | `100` | Number of optimizee update steps per epoch. |
| `learning_rate` | `0.001` | Adam learning rate when `optimizer=Adam`. |

### Path semantics
- `path` is a directory, not a single file.
- For L2L, the directory must contain one `.l2l` file per configured network
  id, such as `cw.l2l`, `conv.l2l`, or `fc.l2l`.
- For `mnist` and `cifar*` problems, `path` also switches the problem factory to
  test mode in `evaluate.py`, even if you are evaluating `Adam`.
- If `optimizer=L2L` and `path` is omitted, the script logs that it is
  evaluating an untrained L2L optimizer.

## Helper smoke defaults

The bundled helper script defaults to tiny CPU-safe commands and blocks
MNIST/CIFAR execution unless `--allow-data` is set:

- `train`: `simple`, `num_epochs=1`, `num_steps=2`, `unroll_length=1`,
  `log_period=1`, `evaluation_period=999999`
- `evaluate`: `simple`, `num_epochs=1`, `num_steps=2`

Use those defaults unless you specifically need a longer run, a saved optimizer,
or a data-backed problem.

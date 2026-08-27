# Workflows

## Tiny CPU smoke training

Use this to prove the training CLI works without touching data downloads.
The bundled helper blocks MNIST/CIFAR execution unless `--allow-data` is set.

```bash
cd <repo-root>
python train.py --problem=simple --num_epochs=1 --num_steps=2 --unroll_length=1 --log_period=1 --evaluation_period=999999
```

Expected signals:
- `Optimizee variables`
- `Problem variables`
- optimizer variable names
- `Epoch 1`
- `Log Mean Final Error`
- `Mean epoch time`

## Tiny CPU evaluation baseline

Use `Adam` when you want a baseline that does not depend on a saved L2L
optimizer directory.

```bash
cd <repo-root>
python evaluate.py --problem=simple --optimizer=Adam --num_epochs=1 --num_steps=2
```

Expected signals:
- graph-finalization and session startup warnings from TensorFlow 1.x are normal
- `Epoch 1`
- `Log Mean Final Error`
- `Mean epoch time`

## Tiny CPU L2L evaluation

Use `L2L` when you want to reload a saved optimizer directory or smoke the
learned-optimizer path.

```bash
cd <repo-root>
python evaluate.py --problem=simple --optimizer=L2L --num_epochs=1 --num_steps=2
```

If you have a saved directory from training:

```bash
cd <repo-root>
python train.py --problem=simple --num_epochs=1 --num_steps=2 --unroll_length=1 --log_period=1 --evaluation_period=1 --save_path=<fresh-save-dir>
python evaluate.py --problem=simple --optimizer=L2L --path=<fresh-save-dir> --num_epochs=1 --num_steps=2
```

For the simple problem, the saved directory should contain `cw.l2l`.
For multi-network problems, the file names follow the configured net ids.

## Reading the epoch math

`train.py` computes:

```text
num_unrolls = num_steps // unroll_length
```

That means:
- each outer epoch resets the optimizee and optimizer state
- each epoch performs `num_unrolls` unroll segments
- remainder steps are dropped when `num_steps` is not divisible by
  `unroll_length`

`evaluate.py` uses `num_unrolls = num_steps` and a one-step unroll inside
`meta_loss(...)`, so each evaluation epoch performs `num_steps` updates from a
fresh reset.

## When to switch to problem-factories

If you move beyond the scalar smoke problems and into MNIST/CIFAR or custom
loss construction, switch to `../problem-factories/SKILL.md` for the data and
problem-selection caveats.

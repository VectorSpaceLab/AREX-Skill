# Troubleshooting

## CLI problems

### `python -m tensorlayer.cli --help` fails with `int('')`

An empty `CUDA_VISIBLE_DEVICES` value triggers the current parser bug. Unset the variable before invoking the CLI help.

### The `train` subcommand is missing

Confirm you are running the TensorLayer package entry point and not a different module. The bundled helper checks the help text for the `train` subcommand.

## Training-loop problems

### Accuracy stays flat on a tiny synthetic dataset

Check the label shape and the number of output units. TensorLayer examples usually use integer labels with `tl.cost.cross_entropy` and a final dense layer matching the class count.

### `fit` or `test` expects a batch size you did not provide

Use the same batch size across the tiny smoke or pass `None` for a small evaluation dataset, matching the public examples.

## Distributed-training problems

### Horovod/OpenMPI is missing

That is expected in the minimum CPU-only scope. Keep distributed training help-only unless the user explicitly asks for the extra environment.

### The trainer appears to hang

Long-running distributed examples may block on runtime setup or data access. Prefer the synthetic smoke first and only use real distributed infrastructure when requested.

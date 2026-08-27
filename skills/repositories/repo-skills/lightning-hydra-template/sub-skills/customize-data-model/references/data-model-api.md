# Data and Model API Reference

## Verified public signatures

From installed-package inspection of the template default package:

```text
MNISTDataModule(data_dir='data/', train_val_test_split=(55000, 5000, 10000), batch_size=64, num_workers=0, pin_memory=False)
SimpleDenseNet(input_size=784, lin1_size=256, lin2_size=256, lin3_size=256, output_size=10)
MNISTLitModule(net, optimizer, scheduler, compile)
```

The default config values can differ from constructor defaults. For example `configs/data/mnist.yaml` sets `batch_size: 128`, and `configs/model/mnist.yaml` sets hidden layer sizes `64/128/64`.

## DataModule contract

`MNISTDataModule` implements these key methods:

- `prepare_data()`: downloads MNIST train and test sets. This is a network/data-cache boundary.
- `setup(stage=None)`: loads MNIST train/test, concatenates them, and splits into train/val/test using `train_val_test_split` and a fixed generator seed `42`.
- `train_dataloader()`, `val_dataloader()`, `test_dataloader()`: return `DataLoader` objects.
- `num_classes`: property returning `10`.

Important behavior:

- If attached to a Trainer, `setup()` checks `batch_size % trainer.world_size == 0` and divides per-device batch size by `world_size`.
- `pin_memory` and `num_workers` are config-driven; debug fixtures set both to safe CPU values.
- The datamodule does not provide a prediction dataloader by default.

## Model and component contract

`SimpleDenseNet` flattens input tensors from `(batch, channels, width, height)` to `(batch, features)` and applies linear/batchnorm/ReLU layers ending in `output_size` logits.

`MNISTLitModule`:

- saves hyperparameters with the network excluded from logging warnings only by convention; the source currently passes `logger=False` but not an ignore list, so Lightning may warn that `net` is an `nn.Module`.
- uses `torch.nn.CrossEntropyLoss`.
- logs `train/loss`, `train/acc`, `val/loss`, `val/acc`, `val/acc_best`, `test/loss`, and `test/acc`.
- compiles `self.net` in `setup(stage)` only when `compile` is true and `stage == 'fit'`.
- builds optimizer and scheduler from Hydra partials in `configure_optimizers()`; scheduler monitors `val/loss` by default in the returned LR scheduler dict.

## Config wiring

Default data config:

```yaml
_target_: src.data.mnist_datamodule.MNISTDataModule
data_dir: ${paths.data_dir}
batch_size: 128
train_val_test_split: [55_000, 5_000, 10_000]
num_workers: 0
pin_memory: False
```

Default model config:

```yaml
_target_: src.models.mnist_module.MNISTLitModule
optimizer:
  _target_: torch.optim.Adam
  _partial_: true
  lr: 0.001
scheduler:
  _target_: torch.optim.lr_scheduler.ReduceLROnPlateau
  _partial_: true
  mode: min
net:
  _target_: src.models.components.simple_dense_net.SimpleDenseNet
compile: false
```

Use `_partial_: true` for optimizer/scheduler configs that should be called later with model parameters or the optimizer.

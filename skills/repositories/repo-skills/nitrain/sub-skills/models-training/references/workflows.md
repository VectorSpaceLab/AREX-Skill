# Workflows

## Purpose

Read this for the canonical ways to create and train Nitrain models.

## 1. Discover an architecture

Use `fetch_architecture()` when you know the family name but want the concrete
constructor from `antspynet`.

```python
import nitrain as nt

arch_fn = nt.fetch_architecture("vgg", dim=2)
model = arch_fn((48, 48, 1), number_of_outputs=1, mode="regression")
```

Tips:
- Use `dim=2` or `dim=3` when the architecture family has 2D and 3D variants.
- Call `list_architectures()` when you want to see what the installed
  antspynet-backed build exposes.

## 2. Build a Keras trainer

```python
trainer = nt.Trainer(model, task="regression")
trainer.fit(loader, epochs=2)
trainer.evaluate(loader)
trainer.predict(loader)
trainer.summary()
```

Good fits:
- regression with MSE defaults;
- classification or segmentation with automatic loss choice;
- Keras models that already know their input and output shapes.

## 3. Use a torch model with TorchTrainer

```python
import torch
from monai.networks.nets import DenseNet121
from nitrain.trainers import TorchTrainer

model = DenseNet121(spatial_dims=2, in_channels=1, out_channels=2)
trainer = TorchTrainer(
    model=model,
    optimizer=torch.optim.Adam(model.parameters(), 1e-3),
    loss=torch.nn.MSELoss(),
    metrics=[],
    device="cpu",
)
```

This is the right path when the user wants the torch/MONAI stack instead of a
Keras trainer.

## 4. Pretrained weights

`fetch_pretrained(name, cache_dir=None)` returns the antspynet pretrained
network handle. Treat this as a networked workflow unless you already know the
weights are cached locally.

## 5. Small CPU smoke pattern

When the task is only to prove the model path is wired up, keep it tiny:

- create one architecture;
- instantiate one trainer;
- avoid a long fit;
- use the CPU torch path when you only need to confirm torch/MONAI importability.

## 6. How this connects to the other sub-skills

- A `Loader` from `preprocessing-and-loading` is the normal input to `Trainer`.
- `Dataset` and reader construction from `datasets-readers` usually come first.
- Prediction output handling belongs in `prediction-and-explanation`.

## 7. Smoke helper

Use the bundled helper after install:

```bash
python scripts/check_install.py --mode models
python scripts/check_install.py --mode torch
```

# API Reference

## Purpose

Read this when you need the verified public surface of the package or when you are wiring the bundled helper scripts to the installed `lpips` package.

## Verified package surface

### `lpips.LPIPS`

Verified signature:

```python
LPIPS(
    pretrained=True,
    net='alex',
    version='0.1',
    lpips=True,
    spatial=False,
    pnet_rand=False,
    pnet_tune=False,
    use_dropout=True,
    model_path=None,
    eval_mode=True,
    verbose=True,
)
```

Key behaviors:

- `net` accepts `alex`, `vgg`, or `squeeze`.
- `lpips=True` enables the learned linear heads; `lpips=False` gives the baseline network average.
- `version='0.1'` is the current default; `version='0.0'` keeps the legacy normalization behavior.
- `normalize=True` in `forward(...)` expects inputs in `[0, 1]` and maps them to `[-1, 1]`.
- `spatial=True` returns a spatial distance map instead of a single scalar.
- The default pretrained AlexNet/VGG/SqueezeNet trunk weights may download from torchvision on first use if they are not already cached.

### `lpips.Trainer`

Verified signature for initialization:

```python
Trainer.initialize(
    self,
    model='lpips',
    net='alex',
    colorspace='Lab',
    pnet_rand=False,
    pnet_tune=False,
    model_path=None,
    use_gpu=True,
    printNet=False,
    spatial=False,
    is_train=False,
    lr=0.0001,
    beta1=0.5,
    version='0.1',
    gpu_ids=[0],
)
```

Verified forward signature:

```python
Trainer.forward(self, in0, in1, retPerLayer=False)
```

Key behaviors:

- `model='lpips'` uses the learned LPIPS head.
- `model='baseline'` keeps the trunk without the learned linear head.
- `model='l2'` and `model='ssim'` exist in the stock trainer, but the stock SSIM path depends on a legacy `scikit-image` symbol that is no longer exported.
- Training mode adds the ranking loss head and optimizer.
- The stock `train.py` script wraps this trainer with the HTML/visualization stack; the bundled training helper avoids that stack.

### Scoring helpers

Verified helper signatures:

```python
score_2afc_dataset(data_loader, func, name='')
score_jnd_dataset(data_loader, func, name='')
```

Behavior summary:

- `score_2afc_dataset` computes the fraction of judgments where the metric prefers the same distorted image as humans.
- `score_jnd_dataset` computes an AP-like score by sorting distances and integrating precision/recall.
- Both expect a callable that accepts two `Nx3xHxW` tensors and returns a tensor-like distance output.

### Core utility functions

Verified public helpers in `lpips`:

- `load_image(path)`
- `im2tensor(image)`
- `tensor2im(image_tensor)`
- `tensor2np(tensor_obj)`
- `tensor2tensorlab(image_tensor, to_norm=True, mc_only=False)`
- `tensorlab2tensor(lab_tensor, return_inbnd=False)`
- `l2(p0, p1, range=255.)`
- `dssim(p0, p1, range=255.)`

Notes:

- `dssim(...)` is the legacy helper that imports `skimage.measure.compare_ssim`; use the bundled fallback helpers instead of relying on it in a modern environment.
- `L2.forward(...)` and `DSSIM.forward(...)` are written for batch size 1 in the stock implementation.

### Dataset loader APIs from the source tree

Source evidence only; the bundled evaluation and training helpers replace these with safer runtime code.

```python
CreateDataLoader(datafolder, dataroot='./dataset', dataset_mode='2afc', load_size=64, batch_size=1, serial_batches=True, nThreads=4)
CustomDatasetDataLoader.initialize(self, datafolders, dataroot='./dataset', dataset_mode='2afc', load_size=64, batch_size=1, serial_batches=True, nThreads=1)
TwoAFCDataset.initialize(self, dataroots, load_size=64)
JNDDataset.initialize(self, dataroot, load_size=64)
```

Known source-tree caveat:

- The stock `jnd` path is buggy because `CreateDataset(..., dataset_mode='jnd')` passes a list into `JNDDataset.initialize`, which expects a single root path.

## Model and checkpoint naming

- Learned weights live under `lpips/weights/v0.0/` and `lpips/weights/v0.1/` in the package data.
- `Trainer.save(...)` uses filenames such as `latest_net_.pth` and `latest_net_rank.pth`.

## Read this next

- `references/bapps-dataset.md` for BAPPS layout and smoke-fixture creation.
- `references/troubleshooting.md` for import, backend, dataset, and SSIM issues.
- The sub-skill references for command-level workflows.

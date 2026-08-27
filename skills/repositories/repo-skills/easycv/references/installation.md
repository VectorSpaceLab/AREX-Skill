# Installation and inspection

EasyCV is a legacy computer-vision toolbox with a broad runtime surface. Use the public package when possible and only add optional extras for the workflow you actually need.

## Public install paths

Preferred public install:

```bash
pip install pai-easycv
```

Editable install from a local checkout:

```bash
pip install -e .
```

The README and quick-start docs describe a baseline stack that includes:

- Python 3.6 or newer
- PyTorch 1.5 or newer
- mmcv 1.2 or newer
- nvidia-dali 0.25.0 for DALI-backed data pipelines

## Optional extras by workflow

- `easy_predict` for `easycv.tools.predict` batch prediction.
- `modelscope` for the ModelScope plugin under `easycv.toolkit.modelscope`.
- `pai_nni` and `blade_compression` for prune / quantize / compression flows.
- `onnxruntime` for ONNX-based predictor paths.
- `torchacc` and the documented CUDA 11.3 container for TorchAccelerator flows.
- `nvidia-dali` when you need DALI-backed loaders or configs.

## Minimal inspection check

After installation, confirm the main package and APIs import:

```bash
python -c "import easycv; from easycv.apis import train_model, single_gpu_test, export; print(easycv.__version__)"
```

If you need the packaged CLI modules, use the installed package entry points directly:

```bash
python -m easycv.tools.train --help
python -m easycv.tools.eval --help
python -m easycv.tools.export --help
python -m easycv.tools.predict --help
```

## When to inspect more than the base package

- Prediction and batch inference often need `easy_predict`.
- Export / optimization often need `onnxruntime`, `blade_compression`, or `pai_nni`.
- TorchAccelerator requires the documented CUDA runtime and a dedicated environment.
- ModelScope plugin workflows need `modelscope`.


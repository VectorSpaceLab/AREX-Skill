# DeblurGAN installation

## Recommended runtime shape

DeblurGAN is a source-tree project with no packaging metadata in this checkout.
Install the runtime dependencies into a Python environment, then point the bundled wrappers at the DeblurGAN checkout with `--repo-root`.

## Recommended baseline

- Python 3.11
- CUDA-enabled PyTorch and TorchVision for training or any perceptual-loss path
- `dominate` for HTML output
- `opencv-python-headless` for the pair-concatenation helper
- Optional: `ssim` if you want to run the source `test.py` verbatim, and `visdom` if you want live training plots

## Example installation commands

### Conda

```bash
conda create --yes --prefix "/absolute/path/to/deblurgan-inspection" python=3.11 pip
conda install --yes --prefix "/absolute/path/to/deblurgan-inspection" -c pytorch -c nvidia pytorch torchvision pytorch-cuda=12.4
"/absolute/path/to/deblurgan-inspection/bin/python" -m pip install dominate opencv-python-headless ssim visdom
```

### Pip-only or venv

```bash
python3.11 -m venv "/absolute/path/to/deblurgan-inspection"
"/absolute/path/to/deblurgan-inspection/bin/python" -m pip install --upgrade pip
"/absolute/path/to/deblurgan-inspection/bin/python" -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
"/absolute/path/to/deblurgan-inspection/bin/python" -m pip install dominate opencv-python-headless ssim visdom
```

## Notes on backend choice

- Use a CUDA-enabled wheel for the training path because the perceptual-loss implementation moves VGG19 features to GPU.
- CPU-only PyTorch is acceptable for inference or data-preparation smoke checks if you pass `--gpu_ids -1` for inference.
- If you do not want interactive plots, you can omit `visdom` and keep the wrapper in headless mode.

## Quick sanity check

After installing dependencies, run the root environment helper:

```bash
python scripts/check_deblurgan_env.py --repo-root <path-to-DeblurGAN-checkout> --cuda
```

Omit `--cuda` if you only need to inspect the import surface.

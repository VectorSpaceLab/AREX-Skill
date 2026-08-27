# ALAE setup and environment guide

## When to read

Read this before running ALAE scripts, diagnosing import failures, or choosing a Python/CUDA/TensorFlow stack for a checkout.

## Repository shape

ALAE is an un-packaged script repository: there is no `setup.py`, `setup.cfg`, or `pyproject.toml`. Most scripts import root modules such as `model`, `net`, `launcher`, `defaults`, and `checkpointer`. Native commands should therefore be run from the ALAE repository root, and subdirectory scripts need the checkout root on `PYTHONPATH`:

```bash
cd <ALAE-checkout>
export PYTHONPATH="$PYTHONPATH:$(pwd)"
```

If an IDE is used, set its working directory to the ALAE checkout root.

## Dependency groups

### Core PyTorch routes

Core training and generation routes need:

- Python with PyTorch and TorchVision.
- CUDA-visible PyTorch for `train_alae.py`, `interactive_demo.py`, `style_mixing/stylemix.py`, and `make_figures/*.py` because these scripts call `torch.cuda.set_device` and `.cuda()` directly.
- `dareblopy` for TFRecord loading during training/metrics data access.
- `dlutils` for parameter counting and download helpers.
- `yacs` for config merging.
- `numpy`, `scipy`, `Pillow`, `imageio`, `tqdm`, `matplotlib`, and `scikit-learn`.

The upstream `requirements.txt` says `torch >= 1.3` and `torchvision`, but old CUDA10-era PyTorch wheels can fail on A100-class GPUs. Prefer a CUDA wheel that supports the actual GPU architecture. During construction, `torch==1.7.1+cu110` was the oldest A100-compatible stack that also kept `dlutils` importable.

The upstream requirement `sklearn` should be installed as `scikit-learn`; the deprecated `sklearn` shim may fail in modern pip. `make_figures/make_recon_figure_multires.py` also imports `skimage`, so install `scikit-image` if that route is needed.

### Optional GUI demo

`interactive_demo.py` additionally needs `bimpy` and a display/GUI context. On headless servers, validate assets first and avoid launching the GUI unless an X/GUI session is available.

### TFRecord preparation and legacy metrics

Dataset preparation scripts use TensorFlow 1.x APIs such as `tf.Session` and `tf.python_io`. TensorFlow 2.x without compatibility changes is not a drop-in replacement for these scripts.

Metric scripts (`metrics/fid.py`, `fid_rec.py`, `ppl.py`, `lpips.py`) are legacy StyleGAN-derived workflows that need `dnnlib` and metric pickle files. The README recommends TensorFlow GPU 1.10/CUDA 9.0; a newer TF1 stack may import but still fail on CUDA/cuDNN library mismatches. Treat metric execution as optional, expensive, and environment-specific.

### Optional face alignment

`align_faces.py` needs `dlib` and a 68-landmark predictor file such as `shape_predictor_68_face_landmarks.dat`. The bundled face-alignment helper lazy-imports `dlib` so its `--help` and `--dry-run` modes work without the optional dependency.

## Safe environment check

From this generated skill root, run:

```bash
python scripts/check_alae_environment.py --repo-root <ALAE-checkout>
```

The checker imports core dependencies and safe source modules, verifies PyTorch CUDA with a tiny tensor by default, and reports optional TensorFlow/dnnlib/bimpy readiness. It never imports metric scripts, downloads checkpoints, starts training, or opens a GUI.

## Model artifact setup

Pretrained checkpoints are normally downloaded through the repository's `training_artifacts/download_all.py`, which has network side effects at top level. Prefer this generated dry-run helper first:

```bash
python scripts/download_alae_artifacts.py --dataset all
python scripts/download_alae_artifacts.py --dataset ffhq --download --yes --dest-root <ALAE-checkout>/training_artifacts
```

The helper lists Google Drive IDs and S3 fallback URLs by default. It downloads only when both `--download` and `--yes` are supplied.

## Native command template

```bash
cd <ALAE-checkout>
export PYTHONPATH="$PYTHONPATH:$(pwd)"
python train_alae.py -c ffhq
python style_mixing/stylemix.py -c ffhq
python make_figures/make_generation_figure.py -c ffhq
```

Always validate data, checkpoint, and style/sample paths with the relevant sub-skill helpers before launching long GPU scripts.

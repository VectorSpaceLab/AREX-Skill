# Installation and Asset Guide

## When to read

Read this when a user needs to set up DragGAN, decide whether CUDA/CPU/MPS is acceptable, place checkpoint files, or understand which StyleGAN-Human workflows need extra assets.

## Environment shape

DragGAN is a script-style repository rather than a packaged Python distribution. A practical runtime usually has:

- Python 3.8 or newer; Python 3.8–3.10 is safest for older StyleGAN-Human and GUI dependencies.
- PyTorch with CUDA for interactive DragGAN editing. The top-level generation script can choose CUDA, MPS, or CPU, but CPU is slow and not a validation substitute for dragging.
- `numpy`, `scipy`, `click`, `Pillow`, `requests`, `tqdm`, `ninja`, `matplotlib`, `imageio`, and `imageio-ffmpeg`.
- GUI/web dependencies: `gradio`, `PyOpenGL`, `imgui`, and `glfw`.
- StyleGAN-Human support dependencies when using that subtree: `opencv-python`, `pandas`, `moviepy`, `lpips`, `imutils`, and optional packages named by the workflow.

The repository documentation uses a Conda environment file for a CUDA-oriented StyleGAN3-style environment and a pip requirements file for additional DragGAN dependencies. On CPU or Apple Silicon, remove NVIDIA/CUDA packages from the Conda environment and set MPS fallback where appropriate, but do not claim that this verifies the interactive CUDA drag path.

## Minimum import check

Use the bundled root helper rather than hand-testing many imports:

```bash
python scripts/check_environment.py --repo-root /path/to/DragGAN
```

A successful check should import the core repo modules and report CUDA visibility when available. If a specific workflow fails later, rerun this helper plus the relevant sub-skill preflight helper.

## Checkpoints and model files

DragGAN expects pretrained StyleGAN `.pkl` files in a checkpoint directory for GUI and Gradio demos. Use the bundled asset helper:

```bash
python scripts/check_model_assets.py --checkpoint-dir /path/to/checkpoints
```

The public manifest can be listed without network access:

```bash
python scripts/download_draggan_checkpoints.py --checkpoint-dir /path/to/checkpoints
```

This helper is dry-run by default. Only add `--execute` after reviewing the URLs, disk budget, and applicable model/license terms. Keep downloads outside the generated skill directory.

Known checkpoint filenames from the repo manifest include:

- `stylegan2_lions_512_pytorch.pkl`
- `stylegan2_dogs_1024_pytorch.pkl`
- `stylegan2_horses_256_pytorch.pkl`
- `stylegan2_elephants_512_pytorch.pkl`
- `stylegan2-ffhq-512x512.pkl`
- `stylegan2-afhqcat-512x512.pkl`
- `stylegan2-car-config-f.pkl`
- `stylegan2-cat-config-f.pkl`

Additional README-mentioned assets include StyleGAN-Human and landscape checkpoints that users must obtain separately when needed. Keep model files outside the generated skill directory.

## Filename inference rule

DragGAN's renderer chooses the generator implementation from the checkpoint filename. It expects names containing one of these signals:

- `stylegan2`
- `stylegan3`
- `stylegan_human`

If a custom model file lacks those substrings, rename a copy or use a workflow that explicitly constructs the expected generator class. Otherwise the renderer may raise a model-type inference error even when the pickle is otherwise valid.

## StyleGAN-Human asset classes

StyleGAN-Human workflows are asset-gated:

| Workflow | Required assets |
| --- | --- |
| Basic generation/interpolation/style mixing | StyleGAN-Human `.pkl` checkpoint matching the desired version. |
| Background whitening | Raw images and segmentation masks with matching filenames; no model weights. |
| Alignment | OpenPose body model, PP-HumanSeg exported model, Paddle/PaddleSeg dependencies, CUDA. |
| PTI inversion | Aligned images, e4e weight, StyleGAN-Human checkpoint, configured PTI paths, CUDA. |
| Attribute editing | StyleGAN-Human checkpoint, latent-direction/statistics files for `upper_length` or `bottom_length`, CUDA, optional FFmpeg for videos. |
| InsetGAN | Body and face checkpoints, dlib landmark and CNN detector models, LPIPS, CUDA. |
| Training | SHHQ data access, dataset directory or zip, large GPU/time/storage budget. |

Use `sub-skills/stylegan-human-manipulation/scripts/check_stylegan_human_assets.py` before running the manipulation workflows.

## Docker caveat

The repo documents a Docker path for Gradio demos, but the image is large and still requires local checkpoints. Prefer the Python environment plus preflight helpers unless the user specifically asks for container execution.

## License and watermark note

The DragGAN algorithm code is CC-BY-NC, while much of the StyleGAN-derived code follows NVIDIA source-code license terms. The project also requires preserving the `AI Generated` watermark behavior in generated outputs.

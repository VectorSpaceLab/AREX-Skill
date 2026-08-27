# Cross-cutting Troubleshooting

## Missing or incompatible checkpoints

**Symptoms:** `No network pickle loaded`, a checkpoint dropdown is empty, or the renderer reports `Cannot infer model type from pkl name!`.

**Recovery:** run `scripts/check_model_assets.py --checkpoint-dir <dir>`. Confirm files end in `.pkl`, are readable, and their names contain `stylegan2`, `stylegan3`, or `stylegan_human`. Do not use an empty directory with the Gradio app: initialization enumerates existing `.pkl` files.

## CUDA is unavailable

**Symptoms:** `torch.cuda.is_available()` is false, a DragGAN UI fails while creating CUDA events, or a heavy StyleGAN-Human script raises a CUDA/device error.

**Recovery:** run `scripts/check_environment.py --repo-root <checkout>`. Install a PyTorch build compatible with the NVIDIA driver and use a GPU-capable environment for interactive editing. CPU/MPS can cover some batch generation commands but is not equivalent to drag optimization, PTI, alignment, or training.

## Custom CUDA extension failures

**Symptoms:** a StyleGAN-Human editing import tries to compile `fused` or `upfirdn2d`, reports missing `CUDA_HOME`, `cuda_runtime.h`, `cusparse.h`, or an incompatible CUDA compiler/toolkit header.

**Recovery:** treat this as an environment/toolchain problem, not a missing model file. Use a matching CUDA toolkit/compiler, a supported host compiler, and the repo’s older dependency assumptions. Clear stale `~/.cache/torch_extensions` artifacts only after confirming they are disposable. Do not claim the editing path is verified from a plain PyTorch import.

## Gradio import errors

**Symptoms:** `ModuleNotFoundError` under `gradio_client`, missing `pkg_resources`, or component API errors.

**Recovery:** use the repo-compatible Gradio 3 generation rather than the newest Gradio release. The inspected environment required `gradio==3.35.2`, `gradio-client==0.2.9`, and a setuptools version that still provides `pkg_resources`. Run the Gradio launcher in dry-run mode before starting a server.

## GUI/OpenGL/GLFW problems

**Symptoms:** the desktop GUI exits before opening a window, reports GLFW/OpenGL/display errors, or works over SSH only after a display is configured.

**Recovery:** verify `imgui`, `glfw`, `PyOpenGL`, and the system OpenGL libraries. Use the Gradio route for headless environments. The desktop route needs a display or a correctly configured virtual display; `--browse-dir` only changes model browsing and does not fix display errors.

## Wrong current directory or import shadowing

**Symptoms:** StyleGAN-Human scripts import the top-level `torch_utils`, `dnnlib`, or `legacy` package instead of the StyleGAN-Human copy, or `ModuleNotFoundError` appears for `utils`, `edit`, or `torch_utils.models`.

**Recovery:** keep root DragGAN and StyleGAN-Human execution contexts distinct. Use the bundled command builders with an explicit `--repo-root`, inspect the printed command, and ensure a StyleGAN-Human command is launched from the subtree expected by its absolute imports. Do not add both conflicting `dnnlib`/`torch_utils` roots to a global `PYTHONPATH` in arbitrary order.

## Download and network failures

**Symptoms:** checkpoint downloads stall, a URL returns an HTML error page, or a partially written `.pkl` is loaded.

**Recovery:** stop the download, check HTTP status and file size, remove only the incomplete target, and retry from a trusted network. Keep downloads outside the generated skill directory. The bundled helpers do not download models by default.

## StyleGAN-Human optional dependencies

- `alignment.py` needs OpenPose model files, PP-HumanSeg/Paddle dependencies, and the expected exported model directory.
- `run_pti.py` needs an aligned-image directory, e4e weights, a StyleGAN-Human checkpoint, and paths configured in PTI config modules.
- `edit.py` needs latent-direction/statistics assets for `upper_length` or `bottom_length`; this checkout may contain the directories without the actual files.
- `insetgan.py` needs dlib landmark/detector models, face/body checkpoints, LPIPS, and CUDA.
- `stylemixing_video.py` imports `dnnlib.tflib` at module import time, so TensorFlow is needed even for help on the unmodified source script.

Use `sub-skills/stylegan-human-manipulation/scripts/check_stylegan_human_assets.py` and do not silently downgrade an asset-gated workflow to a passing import check.

## Data and output mistakes

- Keep raw images and segmentation masks in matching filename pairs for background whitening.
- Alignment expects images with one person; the source algorithm skips or reports images with multiple/low-confidence people.
- PTI and editing paths use relative defaults such as `aligned_image/`, `pretrained_models/`, and `outputs/pti/`; make these paths explicit in a generated command plan before running.
- Video workflows require a working `ffmpeg` executable and enough disk for frames.

## License and output policy

Preserve the repo’s `AI Generated` watermark behavior. Check the DragGAN CC-BY-NC and NVIDIA-derived license terms before redistribution or commercial use.

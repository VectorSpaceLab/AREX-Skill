# Cross-Cutting Troubleshooting

## `ModuleNotFoundError: No module named 'pytorch3d'` before `main.py --help`

Cause: `main.py` imports `nerf.provider`, which imports `nerf.utils`, which imports `nerf.refine_utils`; `nerf.refine_utils` imports PyTorch3D at module import time. This can fail even for a help or coarse-training attempt.

Recovery:

1. Install a PyTorch3D build matching the active Python, torch, CUDA, and platform.
2. If PyTorch3D is only needed for refinement and the user is doing source maintenance, consider patching imports to lazy-load refine utilities, but do not claim the unpatched repo can run without PyTorch3D.
3. Re-run the environment diagnostic and a `main.py --help` check.

## `ModuleNotFoundError: No module named 'tinycudann'`

Cause: default `--backbone tcnn` imports `tinycudann` in `nerf/network_tcnn.py`.

Recovery: install the NVlabs tiny-cuda-nn torch bindings for the selected torch/CUDA stack, or use `--backbone vanilla` only if slower pure-PyTorch NeRF is acceptable. This does not remove the raymarching CUDA requirement because the source forces `opt.cuda_ray = True`.

## Raymarching build/import failure

Symptoms include missing `_raymarching`, `nvcc not found`, CUDA ABI errors, or lazy JIT failures from `raymarching/backend.py`.

Recovery:

- Verify `torch.cuda.is_available()` and a tiny CUDA allocation.
- Verify `nvcc --version` if building from source.
- Build with the same Python/torch/CUDA that will run training: `pip install ./raymarching`.
- If no toolkit is available, install a matching CUDA toolkit or use an environment image that already includes it. A GPU driver alone is not enough for compiling the extension.

## DPT weight path failures

`main.py` constructs `DPTDepthModel(path="dpt_weights/dpt_hybrid-midas-501f0c75.pt", ...)`. If that file is absent relative to the runtime working directory, the run fails before training.

Recovery: download the documented DPT hybrid weights into `dpt_weights/`, or edit/patch the source to accept a different path and record that patch in the user's run notes.

## Hugging Face or BLIP2 stalls/downloads

Stable Diffusion and BLIP2 can download large model weights. If the user has no network or token, runs may fail or hang.

Recovery:

- Ask for explicit permission before network/model downloads.
- Use `huggingface-cli login` or a token where required.
- Provide `--text "object description"` to skip BLIP2 caption generation.
- Use `--guidance clip` only if the user accepts a different guidance mode than the README's Stable Diffusion default.

## Invalid reference image alpha

A regular RGB image can trigger OpenCV conversion errors or produce a useless mask. Use the bundled alpha validator. If no alpha exists, create one with segmentation/background removal and save a PNG with transparent background.

## Long or stretched geometry

The README recommends increasing field of view and blob radius. Try:

```bash
python main.py --workspace NAME --ref_path REF.png --phi_range 135 225 --iters 2000 --fov 60 --fovy_range 50 70 --blob_radius 0.2 --text "prompt"
```

Also check that the alpha mask is centered and does not include large background regions.

## Refinement does not start

The README presents `--refine` as the refine-stage trigger, but in the inspected source the refine code is nested under the `if opt.final:` branch after training/test. If `--refine` alone only trains, run with `--final --refine` or patch the control flow intentionally.

## Mesh export fails after training

`--save_mesh` reaches code paths that require `xatlas`, `nvdiffrast`, scikit-learn, OpenCV, and GPU rasterization. Verify those packages before promising OBJ/texture export.

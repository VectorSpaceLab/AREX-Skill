# Cross-Cutting Troubleshooting

## Purpose

Use this for install/import/backend, config/data path, logging, and GUI failures that affect more than one SplaTAM workflow. Workflow-specific issues live in the nearest sub-skill troubleshooting reference.

## `diff_gaussian_rasterization` import or build failures

Symptoms:

- `ImportError: ... diff_gaussian_rasterization/_C... undefined symbol`
- `ImportError: libcudart.so.11.0: cannot open shared object file`
- `RuntimeError: The detected CUDA version ... mismatches the version that was used to compile PyTorch`
- Build errors involving `cuda_runtime.h`, `crt/host_config.h`, `fatbinary_section.h`, or `cicc`

Likely causes:

- The rasterizer was built against a different PyTorch ABI than the one now imported.
- The compiler toolkit (`nvcc --version`) does not match `torch.version.cuda` closely enough.
- CUDA toolkit headers or compiler subpackages are incomplete.
- Runtime loader paths find the wrong `libcudart.so`.

Recovery:

1. Run `python scripts/check_env.py --require-cuda --require-rasterizer` and capture the exact failing stage.
2. Confirm `python -c "import torch; print(torch.__version__, torch.version.cuda)"` and `nvcc --version`.
3. Install or switch to a coherent Torch/CUDA/toolkit pair. The README-era baseline is Torch 1.12.1 + CUDA 11.6; upstream also reports testing Torch 2.3.0 + CUDA 12.1.
4. Rebuild the pinned rasterizer after the final Torch selection:

   ```bash
   python -m pip install --no-build-isolation --force-reinstall \
     'git+https://github.com/JonathonLuiten/diff-gaussian-rasterization-w-depth.git@cb65e4b86bc3bd8ed42174b72a62e8d3a3a71110'
   ```

5. If unpinned dependencies pulled a newer Torch, repair the dependency set before rebuilding. Rebuilding against the wrong Torch just moves the failure to runtime.

Do not proceed to native reconstruction verification until this import passes.

## Torch CUDA is unavailable

Symptoms:

- `torch.cuda.is_available()` is `False`.
- CUDA tensor allocation fails while CPU imports work.
- SplaTAM crashes at the first `.cuda()` call.

Recovery:

1. Check host GPU visibility with the platform's NVIDIA tooling.
2. Confirm the installed PyTorch build is a CUDA build, not CPU-only.
3. Confirm the CUDA driver is new enough for the selected runtime.
4. Do not claim CPU fallback; selected SplaTAM workflows require CUDA.

## TorchMetrics / TorchVision import failures

Symptoms:

- Import fails while loading `torchmetrics.image.lpip`.
- Import chain fails inside `torchvision.models` or `torchvision.transforms`.

Likely causes and fixes:

- `torchmetrics`, `torchvision`, and `torch` are version-incompatible. Install a compatible trio instead of upgrading only one package.
- Modern unpinned `kornia` can upgrade Torch. Pin or constrain dependencies when preserving the README-era stack.
- LPIPS metrics can require model weights when instantiated; avoid triggering downloads during offline verification unless weights are already cached or the user approves network access.

## W&B prompts or network/auth failures

Some public benchmark configs set `use_wandb=True`. For local or CI-style runs without credentials:

- Set `use_wandb=False` in the Python config before running.
- If a run already started and stalls on W&B, stop it, edit the config, and restart rather than adding credentials implicitly.

## Dataset/config path failures

Symptoms:

- `FileNotFoundError` for `params.npz`, YAML data config, RGB/depth frame, or `transforms.json`.
- `Unknown dataset name ...`.
- Dataset length is zero or `num_frames` exceeds available frames.

Recovery:

1. Read [data-and-configs.md](data-and-configs.md) to identify the expected layout for the dataset family.
2. Confirm `config["data"]["basedir"]`, `sequence`, and `gradslam_data_cfg` are correct for the current checkout/dataset root.
3. For NeRFCapture data, run `sub-skills/capture/scripts/validate_nerfcapture_dataset.py` before SLAM.
4. For saved results, run `sub-skills/reconstruction/scripts/check_result_bundle.py` before export or visualization.

## Open3D visualization problems

Symptoms:

- Viewer window never appears.
- `GLFW`/display errors in a headless session.
- Final visualization starts but renders black or empty points.

Recovery:

- Confirm a GUI/display is available; visualization is not a headless verification gate.
- Use `viz.render_mode='centers'` to inspect Gaussian centers when color/depth rendering is suspect.
- Confirm `params.npz` includes `means3D`, colors, opacity, scale, rotations, `intrinsics`, `w2c`, and frame metadata.

## Capture wrapper system mutations

The bash wrappers for iPhone/NeRFCapture workflows inspect and may set:

```bash
net.core.rmem_max=2147483647
net.core.wmem_max=2147483647
```

They call `sudo sysctl -w` if the values differ. Ask for explicit authorization before running those wrappers. If system mutation is not authorized, run the Python scripts directly and document any DDS buffer limitation.

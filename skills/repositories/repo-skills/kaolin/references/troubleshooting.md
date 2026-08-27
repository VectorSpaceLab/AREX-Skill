# Kaolin cross-cutting troubleshooting

Use this before drilling into a sub-skill-specific troubleshooting page.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'kaolin'` | Kaolin is not installed in the active Python. | Install a matching wheel/source build and run `python scripts/check_kaolin_environment.py --json`. |
| `cannot import name '_C'`, `No module named kaolin._C`, or source checkout import fails | Import is shadowing an installed wheel, or the checkout was not built. | Run Python from outside the source checkout, install a compatible wheel, or build the checkout with required toolchain. |
| PyTorch version guard fails during source install | Setup enforces a supported PyTorch range. | Install a supported PyTorch/Kaolin pair. Use `IGNORE_TORCH_VER=1` only for deliberate expert testing. |
| CUDA workflow fails but CPU import works | CPU-only install or CUDA wheel/toolkit mismatch. | Check `torch.version.cuda`, `torch.cuda.is_available()`, `import kaolin._C`, and the owning sub-skill's backend probe. |
| Source build cannot find `nvcc` | CUDA toolkit is not installed or not on `PATH`. | Use an official prebuilt wheel for the matching PyTorch/CUDA pair, or install a CUDA toolkit and set build variables deliberately. |
| Wrong CUDA architecture or CUB conflict during build | `TORCH_CUDA_ARCH_LIST`/CUB headers not configured. | Set `TORCH_CUDA_ARCH_LIST` for the target GPUs; set `CUB_HOME` if CUB header selection conflicts. |
| USD import/export fails | Missing `pxr`/`usd-core`, wrong scene path/time sample, or overwrite policy. | Probe `pxr`, inspect scene paths/time, and pass explicit `scene_path`, `time`, and `overwrite` values. |
| nvdiffrast backend unavailable | Optional package/context missing. | Use bundled CUDA renderer (`backend="cuda"`) when acceptable or install/probe nvdiffrast separately. |
| Simplicits/Newton fails on import | Missing Warp/Newton optional package or incompatible device. | Use `physics-simulation/scripts/physics_backend_probe.py`; treat Newton as optional unless the user explicitly needs it. |
| Dash3D or notebook visualization hangs | Server/browser/Jupyter UI was launched in automation or optional frontend deps are missing. | Use visualization dry-run helpers first; launch servers/browser UIs only after explicit user approval. |
| API exists in source but not installed package | Source/wheel drift. | Refresh/install from current source or constrain the answer to APIs verified in the installed package. |

## Safe diagnostic order

```bash
python scripts/check_kaolin_environment.py --json
python sub-skills/geometry-io-representations/scripts/mesh_io_probe.py --json --tiny-surface-mesh
python sub-skills/ops-metrics-conversions/scripts/tensor_ops_smoke.py
python sub-skills/rendering-cameras-lighting/scripts/render_backend_probe.py --json
python sub-skills/physics-simulation/scripts/physics_backend_probe.py --json
python sub-skills/visualization-workflows/scripts/kaolin_dash3d_help.py --help
```

Only run CUDA, server, notebook, dataset, or long simulation checks when the user's task requires them and the environment is safe.

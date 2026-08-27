# KAIR setup and environment guidance

KAIR is a source-script repository, not an installable package. Run commands from the KAIR checkout root so imports such as `models`, `data`, and `utils` resolve from the repository tree.

## Minimal install pattern

Use an isolated Python environment. Then install the repository requirements and any missing toolchain helpers:

```bash
python -m pip install -U pip setuptools wheel
python -m pip install -r requirement.txt
python -m pip install ninja
python -m pip check
```

`requirement.txt` covers the normal image/video stack, including OpenCV, scikit-image, hdf5storage, lmdb, timm, einops, and requests. The exact PyTorch build should be chosen for the user's accelerator and driver rather than blindly pinned from construction-time evidence.

## Backend expectations by workflow

| Workflow | Minimum useful backend | Notes |
| --- | --- | --- |
| Config editing, command building, dataset layout checks | CPU-only Python is enough | Bundled helper scripts do not import KAIR or run models. |
| Image testing/training parser/help checks | CPU can check syntax and imports | Real inference/training may still need CUDA for practical speed and memory. |
| SwinIR real-world SR and large image restoration | CUDA strongly recommended | Use `--tile` to avoid OOM. |
| VRT/RVRT inference and training | CUDA-first | VRT/RVRT are memory-heavy video transformers; CPU is not a realistic verification backend. |
| RVRT custom guided deformable attention | CUDA-capable PyTorch + `nvcc` + `ninja` | Extension compilation can fail even when ordinary PyTorch CUDA works. |
| Face enhancement / GPEN path | CUDA recommended; custom op import path matters | `network_faceenhancer.py` imports `op` as a top-level module in KAIR, so source wrappers may need to add `models/` to `PYTHONPATH`. |
| MATLAB metrics/scripts | MATLAB runtime | Reference-only in this skill. |

## Portable environment check

From the KAIR root, the root helper can check the active environment:

```bash
python skills/disco/kair/scripts/kair_check_environment.py --kair-root .
```

For CUDA-required workflows:

```bash
python skills/disco/kair/scripts/kair_check_environment.py --kair-root . --require-cuda
```

For RVRT/face custom-op preflight, only run when a CUDA toolkit is installed and extension builds are allowed:

```bash
mkdir -p .cache/torch-extensions
TORCH_EXTENSIONS_DIR="$PWD/.cache/torch-extensions" \
TORCH_CUDA_ARCH_LIST="<your_compute_capability>" \
python skills/disco/kair/scripts/kair_check_environment.py --kair-root . --require-cuda --check-custom-ops
```

Replace `<your_compute_capability>` with a value such as `8.0`, `8.6`, or `9.0`. If the first custom-op import reports that `ninja` is missing, install `ninja` into the same environment and retry.

## Safe parser/help probes

These probes should not start training or full inference, but they do import parts of KAIR and may reveal missing dependencies:

```bash
python main_download_pretrained_models.py --help
python main_test_dncnn.py --help
python main_test_swinir.py --help
python main_train_psnr.py --help
python main_test_vrt.py --help
python main_test_rvrt.py --help
```

If VRT/RVRT help imports fail because of extension or CUDA issues, use the bundled command builders and references for command planning, then repair the environment before launching native workflows.

## Working-directory and path rules

- Run KAIR native scripts from the repository root unless a wrapper explicitly sets `PYTHONPATH`.
- Keep user datasets/checkpoints outside the generated skill files; pass paths at runtime.
- Avoid putting private absolute paths into option JSONs that will be shared.
- KAIR option paths can use `~`; the parser expands user paths.
- Many KAIR scripts use default roots such as `model_zoo`, `testsets`, `trainsets`, and `results` relative to the current working directory.

## Known dependency pitfalls

- OpenCV import errors usually indicate a broken `opencv-python` wheel or missing system libraries.
- `lmdb` is only needed for LMDB-backed training datasets and conversion helpers.
- `hdf5storage` is needed by MATLAB/Mat-file related data flows.
- `timm` and `einops` are required by SwinIR/VRT/RVRT families.
- `ninja` is required for PyTorch C++/CUDA extension JIT builds.
- If `torch.cuda.is_available()` is false, do not treat VRT/RVRT/face-enhancer native checks as fully verified.

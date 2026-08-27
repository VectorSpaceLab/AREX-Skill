# Safe diagnosis and stop conditions

Start with the parent [cuda-extensions skill](../SKILL.md) and run the
[read-only compatibility checker](../scripts/check_legacy_cuda_compat.py). This
reference owns diagnosis of the legacy NMS/RoIAlign path. Route model
configuration and tensor-shape questions to
[models-and-architectures](../../models-and-architectures/SKILL.md), and route
prediction, 2D-to-3D merging, and saved-result questions to
[inference-and-evaluation](../../inference-and-evaluation/SKILL.md).

## Triage table

| Symptom | Likely class | Safe next action | Stop condition |
|---|---|---|---|
| `ModuleNotFoundError: torch.utils.ffi` while importing `cuda_functions` | Modern torch/legacy FFI ABI gap | Record the exact torch version and checker output; use source contracts only | Do not install a random FFI package, patch the import, or call `build.py` |
| `_nms.so` or `_crop_and_resize.so` fails with undefined symbols, loader errors, or import-time CFFI errors | Precompiled binary portability/ABI mismatch | Treat binary as unverified; preserve the original error in the report | Do not symlink libraries, change binary names, or claim the detector works |
| `nvcc: command not found` | No CUDA toolkit compiler | Record driver/torch facts separately; stop at static build planning | Do not infer that `nvidia-smi` CUDA 13.0 supplies `nvcc`; do not compile |
| `invalid device function`, `no kernel image`, or launch failure | CUDA object architecture mismatch or stale kernel | Compare target capability to README arch table; escalate source modernization | Do not rerun on another GPU or substitute CPU and call it equivalent |
| `torch.cuda.is_available()` is false | Framework driver/runtime/device issue | Diagnose the current torch/driver installation independently | Do not use it to conclude that legacy CPU detector execution is equivalent |
| NMS receives wrong number of columns | Dimensionality/config contract error | Check `cf.dim`, model family, contiguous float tensor, and score position | Do not reshape/drop columns silently |
| NMS returns CPU indices or fails at `.cuda()` | The wrapper expects a CUDA tensor and CUDA indices | Verify that input and active device are correct; then stop if extension is unverified | Do not use `nms_cpu` as an invisible fallback |
| RoIAlign 2D shape mismatch | Wrong `N,C,H,W`, box ordering, normalization, or `box_ind` dtype/length | Compare the direct 2D contract in [custom-ops.md](custom-ops.md) | Do not use a 3D wrapper for 2D data |
| 3D RoIAlign CPU path is requested | Checked-in 3D CPU C source is still 2D-shaped | Report source inconsistency and require separate validation | Do not claim a CPU 3D fallback |
| 3D `RoIAlign` class raises constructor/argument errors | Class calls the function without `crop_zdepth` and retains a 2D docstring | Use the model's direct `ra3D` contract for static review only | Do not patch the runtime skill or claim the class is verified |
| Model import fails before data/config parsing | Custom op imports occur at module import in MRCNN/U-FRCNN and NMS imports occur in Retina models | Separate import/ABI failure from data/config failure; route model facts upward | Do not skip the failure and report a trained/tested detector |
| GPU memory is unavailable for a tiny smoke | Host resource contention | Skip the optional framework smoke and record why | Do not evict other jobs or run a model workload |

## Safe command sequence

From the repository root, this sequence is read-only with respect to repository
sources and never invokes `build.py`:

```bash
python path/to/medical-detection-toolkit/sub-skills/cuda-extensions/scripts/check_legacy_cuda_compat.py \
  --repo-root path/to/checkout

# Only if a one-element allocation is safe on the chosen device:
python path/to/medical-detection-toolkit/sub-skills/cuda-extensions/scripts/check_legacy_cuda_compat.py \
  --repo-root path/to/checkout --framework-cuda-smoke
```

The checker may query `nvidia-smi` and import torch. It must not import any
module below `cuda_functions`, execute a native extension, call `nvcc`, or
invoke a build helper. A checker result is diagnostic evidence, not a license
to continue past a blocker.

## Build planning facts

The README gives a manual two-stage flow: compile the relevant `.cu` object
with `nvcc -x cu -Xcompiler -fPIC -arch=[arch]`, then run the corresponding
`build.py`. The four build scripts use `torch.utils.ffi.create_extension`,
legacy TH/THC headers, and `.cu.o` files. On the verified host, both the
compiler and FFI module are absent. A modern A100 target also is not one of the
README's documented architecture rows. Therefore the safe result is
`LEGACY_CUDA_BLOCKED`, not a suggested command with guessed paths or flags.

If a user explicitly requests modernization, that is a new engineering task
with its own source/API design, target architecture, build isolation, and
numerical validation. It must not be hidden inside a diagnosis or treated as
an automatic repair.

## Exact detector execution policy

The following are **optional/unverified**, with no CPU substitute, until an
approved compatible environment and native numerical tests exist:

- importing MRCNN/U-FRCNN/RetinaNet/Retina U-Net with custom-op imports;
- running `exec.py --mode train`, `test`, or `train_test` through `.cuda()`;
- using the custom NMS in RPN/final detection filtering; and
- using 2D/3D legacy RoIAlign in the feature pyramid.

A pure CPU helper test, a static source assertion, or a PyTorch CUDA tensor
smoke may be reported separately, but none upgrades this classification.

## Report template

When closing a diagnosis, include:

1. `repo_root` and source commit/check-out identity if available;
2. torch version, torch CUDA label, `cuda.is_available`, device capability,
   driver-reported CUDA, and `nvcc` result;
3. `torch.utils.ffi` result;
4. the failing phase and exact model/config dimensionality;
5. whether binaries were merely present (default: yes) or separately verified;
6. one of `FRAMEWORK_CUDA_ONLY`, `LEGACY_CUDA_UNVERIFIED`,
   `LEGACY_CUDA_BLOCKED`, or `CPU_UTILITY_ONLY`; and
7. the next safe route, with an explicit statement that no CPU substitution was
   made.

Link this report back to
[compatibility.md](compatibility.md) and the parent skill so a downstream
researcher can distinguish a framework smoke from an exact detector result.

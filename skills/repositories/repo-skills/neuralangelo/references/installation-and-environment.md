# Neuralangelo Installation and Environment Guide

Use this reference when the task is to prepare, inspect, or repair the runtime before running data conversion, training, or mesh extraction. It is not a full package installer; it records the dependency constraints that matter operationally and gives safe verification commands.

## Runtime Model

Neuralangelo is a source-tree workflow rather than a packaged command-line distribution. The project root provides training and extraction entry points and Python packages such as `imaginaire`, `projects.nerf`, and `projects.neuralangelo`. To execute the implementation, a future agent needs:

1. A target Neuralangelo source tree or equivalent installed source package.
2. A Python environment whose `sys.path` can import that source tree.
3. CUDA-capable PyTorch and a working `tinycudann`/tiny-cuda-nn install for real model work.
4. Additional image, mesh, config, and experiment-tracking packages depending on the requested phase.

The bundled helper `scripts/check_neuralangelo_environment.py` accepts `--project-root` to make these imports explicit instead of depending on hidden shell state.

## Proven Compatible Baseline

The verified drafting baseline used these public versions and capabilities:

- Python 3.9 for inspection.
- PyTorch 2.6.0 with CUDA enabled.
- TorchVision 0.21.0.
- tiny-cuda-nn / `tinycudann` 1.7.
- NumPy 1.26.4, PyYAML, addict, OpenCV headless, trimesh, PyMCubes, W&B.
- NVIDIA A100 GPUs with compute capability 8.0.

The repository's environment file describes a Python 3.8-era stack. On one modern host, Python 3.8 plus source builds of tiny-cuda-nn failed through CUDA/header/ABI problems, while a Python 3.9 environment with a prebuilt `tinycudann` package verified successfully. Treat Python 3.8 as source evidence, not as an invariant if a newer CUDA/tiny-cuda-nn stack is required.

## Minimum Phase-Specific Needs

| Phase | CUDA required? | Needs Neuralangelo source imports? | Notes |
| --- | --- | --- | --- |
| Bundled command planning | No | No | Uses this skill's standalone scripts only. |
| `transforms.json` validation | No | No | Use data-preparation validator before expensive runs. |
| Config summary from YAML files | No | No for static YAML; yes only if using project config loader | The bundled summary parser can inspect YAML paths safely. |
| CLI help/import checks | Usually no CUDA allocation, but CUDA packages must import | Yes | Use root environment checker or entry-point wrapper with `--help`. |
| Training | Yes | Yes | Requires PyTorch CUDA and `tinycudann`; CPU substitute is not realistic. |
| Mesh extraction | Yes for practical extraction | Yes | Low-resolution planning can be static, but extraction evaluates the model. |
| COLMAP reconstruction | GPU optional but recommended | No for raw COLMAP, yes for project conversion helpers | Dataset/tool availability controls this phase. |

## Safe Verification Commands

From the generated skill directory:

```bash
python scripts/check_neuralangelo_environment.py --project-root <neuralangelo-root> --require-cuda --json
```

For entry-point help checks through the bundled wrapper:

```bash
python scripts/run_neuralangelo_entrypoint.py --project-root <neuralangelo-root> --entrypoint train -- --help
python scripts/run_neuralangelo_entrypoint.py --project-root <neuralangelo-root> --entrypoint extract-mesh -- --help
python scripts/run_neuralangelo_entrypoint.py --project-root <neuralangelo-root> --entrypoint generate-config -- --help
```

For package consistency:

```bash
python -m pip check
python - <<'PY'
import torch, tinycudann
print('torch', torch.__version__, 'cuda', torch.version.cuda, torch.cuda.is_available())
print('tinycudann import ok')
PY
```

## Installing: Practical Strategy

1. Start with an isolated Conda or micromamba environment. Avoid mutating a shared system Python.
2. Install a CUDA-enabled PyTorch/TorchVision pair compatible with the host driver.
3. Prefer a prebuilt `tinycudann` package when available for the selected Python/CUDA combination. Use source builds only when the CUDA toolkit headers, compiler, and GPU architecture flags are known to match.
4. Pin NumPy below 2 if older visualization/conversion packages or binary wheels complain about ABI compatibility.
5. Install image/geometry utilities only to the level needed for the requested phase. For pure planning and validation, the bundled scripts use the standard library where possible.
6. Add the target Neuralangelo source tree to `PYTHONPATH`, install it in editable form if packaging metadata exists in a future revision, or run the root checker with `--project-root`.

## tiny-cuda-nn Failure Patterns

- **`ModuleNotFoundError: tinycudann`**: install tiny-cuda-nn/`tinycudann` for the active Python, then rerun the root checker.
- **CUDA header errors during source build**: verify the CUDA toolkit development headers, not just runtime libraries. Source builds may need `CUDA_HOME`, `TORCH_CUDA_ARCH_LIST`, a compatible compiler, and `ninja`.
- **Unsupported GPU architecture**: set architecture flags for the actual GPU capability, or choose a binary package built for the host CUDA stack.
- **Source build succeeds but import fails**: check PyTorch/CUDA ABI compatibility and whether the extension was compiled for the same Python environment.

## When to Stop Environment Work

Stop and report an explicit blocker when:

- The host has no CUDA device but the user asks for real training or extraction.
- PyTorch CUDA works but `tinycudann` cannot be installed after trying an appropriate binary route and one bounded source-build repair pass.
- The target Neuralangelo source tree is absent and the requested action requires executing project code.
- Required data/checkpoints are missing for an end-to-end native run.

Do not convert a CPU-only planning success into a claim that Neuralangelo training or extraction is verified.

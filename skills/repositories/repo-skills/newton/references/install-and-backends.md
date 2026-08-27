# Installation, extras, and backend checks

Read this before diagnosing Newton import errors, optional dependency failures, or CPU/CUDA differences.

## Minimum install

Newton supports Python 3.10+ and requires `warp-lang`.

```bash
pip install newton
python - <<'PY'
import newton, warp as wp
print(newton.__version__)
wp.init()
print([str(d) for d in wp.get_devices()])
PY
```

Use a virtual environment. On systems where `warp-lang` is resolved from NVIDIA's package index, add the documented NVIDIA extra index if ordinary pip cannot find the required Warp wheel.

## Optional extras

Install the smallest extra that matches the workflow:

| Extra | Use when |
| --- | --- |
| `newton[sim]` | MuJoCo/MuJoCo Warp solver workflows and MJCF/MuJoCo integration |
| `newton[importers]` | USD, mesh processing, robot URI resolution, Newton USD schemas, and import-heavy examples |
| `newton[remesh]` | Open3D/pyfqmr remeshing utilities |
| `newton[onnx]` | ONNX/Warp-NN neural actuators and policy examples |
| `newton[examples]` | Built-in example browser, visualization dependencies, importers, sim, and ONNX example support |
| `newton[rtx]` | OVRTX real-time ray-tracing viewer |
| `newton[torch-cu12]` or `newton[torch-cu13]` | Torch checkpoint or training/policy workflows that explicitly require PyTorch |
| `newton[notebook]` | Jupyter notebook and web visualization workflows |
| `newton[dev]` | Development/test workflow for the repository, not ordinary package usage |
| `newton[docs]` | Building Newton documentation |

Avoid installing `dev`, Torch, RTX, or notebook extras unless the task requires them.

## Platform and GPU requirements

- Python: 3.10+; Python 3.11+ is generally safer for compiled optional wheels.
- OS: Linux x86-64/aarch64, Windows x86-64, or macOS CPU-only.
- CUDA: Newton inherits Warp CUDA support; NVIDIA GPUs should have a compatible driver and compute capability. Warp wheels include CUDA runtime pieces, so a local CUDA Toolkit is usually not required.
- macOS: CPU-only for Newton GPU acceleration claims.
- Optional extras can have narrower Python/platform wheel support than the base package.

## Diagnostic scripts

From the root of this generated skill directory:

```bash
python scripts/check_newton_env.py --show-optional
python scripts/newton_smoke.py --device cpu --steps 2
python scripts/list_newton_examples.py --limit 20
```

Use `--require-cuda` only when the task truly requires CUDA. A CPU smoke proves base API viability, not CUDA performance, RTX rendering, or Torch policy support.

## Source checkout development install

When contributing to Newton itself, use the repository's documented `uv` workflow if available:

```bash
uv sync --extra dev
uv run -m newton.examples --list
uv run --extra dev -m newton.tests -k test_api
```

For a pip-based editable install, use the development-maintenance reference and keep optional extras narrow.

## Backend classification for this skill

The generated skill was verified with:

- Base editable Newton package import.
- `warp-lang` import and CPU allocation.
- CUDA allocation through Warp on a visible NVIDIA GPU.
- A tiny public `SolverXPBD` CPU simulation smoke.

Optional native gates for MuJoCo/importers/RTX/Torch/notebook were not installed in the minimum construction environment. Treat their guidance as install-and-troubleshooting knowledge until the current user environment verifies the relevant extras.

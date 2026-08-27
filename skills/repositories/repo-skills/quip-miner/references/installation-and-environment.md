# Installation and Environment

## Package Facts

- Distribution name: `quip-protocol`.
- Console command: `quip-miner`.
- Python requirement: `>=3.10`.
- Public Python modules include `quip_cli`, `shared`, `substrate`, `CPU`, `GPU`, `QPU`, and `dwave_topologies`.
- Base dependencies include D-Wave Ocean, NumPy, aiohttp, Click, BLAKE3, `substrate-interface`, `scalecodec`, `dilithium-py`, and TOML support for Python 3.10.

## Install Extras

Use the smallest extra set that matches the workflow:

| Need | Install extra | Notes |
| --- | --- | --- |
| CPU/operator/config/QPU package surface | base install | Base includes D-Wave Ocean but not CUDA/Metal packages. |
| NVIDIA CUDA mining | `cuda` | Installs `cupy-cuda12x` and `nvidia-ml-py`; still requires an NVIDIA driver and visible device. |
| Apple Silicon Metal mining | `metal` | Installs PyObjC Metal packages; live runtime requires macOS Apple Silicon. |
| Test/contributor workflow | `dev` | Installs `pytest` and `pytest-asyncio`. |
| Networking performance extras | `fast` | Optional `pyzmq` and `uvloop` where supported. |
| Broad visual/torch stack | `full` | Large; do not choose it unless the task really needs those packages. |

From a checkout:

```bash
python -m pip install -e .
python -m pip install -e '.[cuda,dev]'
```

If using a published package or wheel, install the same extras from that distribution instead of relying on a local checkout.

## Safe Smoke Checks

```bash
python -c "from importlib.metadata import version; import quip_cli; print(version('quip-protocol'))"
quip-miner --help
python scripts/quip_backend_probe.py --json
python -m pip check
```

CUDA-specific smoke:

```bash
python - <<'PY'
import cupy as cp
print(cp.__version__)
print(cp.cuda.runtime.getDeviceCount())
cp.zeros(1)
PY
```

This proves CuPy can see and allocate on a CUDA device. It does not prove a live validator or mining run.

## Backend Availability Rules

- **CPU:** available when the base package imports and command routing works.
- **CUDA:** requires `cupy-cuda12x`, compatible NVIDIA driver/runtime, and at least one visible CUDA device.
- **Metal:** requires macOS + Apple Silicon + Metal/PyObjC packages. On Linux or non-Apple hardware, treat Metal as unavailable; there is no CPU fallback for live Metal execution.
- **Modal:** requires the optional `modal` package plus Modal authentication. The package can import with Modal unavailable; live jobs still require cloud auth.
- **D-Wave QPU:** package imports are not live sampling evidence. Live sampling requires `DWAVE_API_KEY`, network access, solver access, and cost approval.
- **Gate-model QPUs:** token/profile support is provider-specific. Treat them as optional unless the user supplies credentials and asks for a live run.

## Environment Privacy

Do not put local virtualenv, conda prefix, workstation paths, or temporary inspection-environment names into user-facing instructions. Generated commands should use `python`, `quip-miner`, paths supplied by the user, or paths inside this skill tree.

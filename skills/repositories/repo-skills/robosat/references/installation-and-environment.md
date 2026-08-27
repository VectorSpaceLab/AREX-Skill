# Installation and environment

RoboSat is legacy Python software. Treat installation as part of the task, not a formality, especially when using compiled geospatial dependencies or torch.

## Recommended installation routes

### Docker-style route

RoboSat originally documented CPU and GPU Docker images. Prefer this route when a user wants to reproduce the historical environment, isolate old dependencies, or train on GPU:

```bash
docker run -it --rm -v "$PWD:/data" --ipc=host --network=host mapbox/robosat:latest-cpu --help
```

For GPU training, use a host/container combination that exposes NVIDIA devices and a torch CUDA build compatible with the actual GPU. The legacy GPU image used an older CUDA/torch family, so modern GPUs may need a rebuilt image rather than a blind wheel install.

### Source or local environment route

When installing from source or a checkout, use an isolated environment pointed at the RoboSat source checkout or release checkout, not the skill tree itself. The project was exercised with Python 3.6-era dependencies. A practical CPU install sequence is:

```bash
python -m pip install -r requirements.txt
python -m pip install https://download.pytorch.org/whl/cpu/torch-1.1.0-cp36-cp36m-linux_x86_64.whl
python -m pip install https://download.pytorch.org/whl/cpu/torchvision-0.3.0-cp36-cp36m-linux_x86_64.whl
python -m pip install -e <robosat-checkout> --no-deps
```

Use the exact Python tag that matches the torch wheels. If using Conda, install native libraries such as `libspatialindex` in the same environment before checking the CLI.

## Minimal runtime check

From the environment where RoboSat is installed:

```bash
python -c "import robosat; print('robosat import ok')"
rs --help
python -m robosat.tools --help
python scripts/check_robosat_env.py --check-cli
```

If `rs` is not on `PATH`, `python -m robosat.tools --help` exercises the same subcommand registry.

## CPU and CUDA policy

RoboSat commands read `model.common.cuda` from the model TOML:

- `cuda = false`: use CPU. This is the safest environment-inspection and small-smoke path.
- `cuda = true`: `train`, `predict`, and `serve` require `torch.cuda.is_available()` to be true and will exit or assert otherwise.

This skill generation verified CPU import, CLI help, and a CPU U-Net forward smoke. It did not verify CUDA. Do not promise GPU success unless the target environment has a compatible CUDA torch build, driver, GPU architecture support, and a tiny CUDA smoke has passed.

## Dependency notes

| Surface | Notes |
| --- | --- |
| `torch` / `torchvision` | The historical CPU wheel pair is `torch==1.1.0`, `torchvision==0.3.0` for CPython 3.6. GPU wheels must match Python, CUDA, driver, and GPU architecture. |
| `rtree` | Needs the `libspatialindex_c` shared library. If CLI import fails with `Could not find libspatialindex_c`, install `libspatialindex` through the OS package manager or Conda. |
| `pyproj` / PROJ data | Post-processing imports create an ESRI:54009 equal-area transformer. If `rs --help` fails with `Invalid projection: esri:54009`, use a pyproj/PROJ-data combination that includes ESRI authorities; pyproj 2.6.x is a compatible 2.x line under `setup.py`'s `pyproj~=2.1` requirement. |
| `rasterio`, `shapely`, `osmium`, `opencv` | Prefer wheels or Conda packages in a Python 3.6-era environment. Source builds may require GDAL/GEOS/PROJ/OpenCV system libraries. |
| `flask`, `requests` | Needed for `rs serve` and downloads; serving also needs a Mapbox token for the demo map page. |
| `pillow` | The historical Dockerfile replaced Pillow with `pillow-simd` for speed. It is optional for correctness. |

## Offline-safe model smoke

Run the bundled U-Net smoke from the model sub-skill to avoid pretrained ResNet downloads:

```bash
python sub-skills/model-lifecycle/scripts/unet_cpu_smoke.py
```

It constructs `UNet(pretrained=False)` and runs a small CPU forward. Do not use `UNet()` with the default `pretrained=True` for an offline smoke, because it can request pretrained torchvision weights.

## Network and credentials

- `rs download` fetches imagery from a URL template with `{z}`, `{x}`, and `{y}` placeholders. Keep access tokens outside scripts and logs.
- `rs serve` needs `MAPBOX_ACCESS_TOKEN` for the demo map page and a tile URL template for imagery fetches.
- Do not use network-backed commands as smoke tests unless the user has provided the endpoint, token policy, and runtime budget.

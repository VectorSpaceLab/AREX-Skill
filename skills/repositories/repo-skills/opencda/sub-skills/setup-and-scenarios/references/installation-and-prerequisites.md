# Installation and prerequisites

This guidance targets the inspected OpenCDA 0.1.3 source. The supplied
repository documents Python 3.7+ and recommends Ubuntu 16.04/18.04/20.04,
roughly 3 GB GPU for smooth CARLA rendering (8 GB recommended), and about
100 GB disk for CARLA/Unreal assets. The inspected compatible environment used
Python 3.8; use a clean environment and resolve pins for the actual Python
minor version rather than blindly forcing the older environment file.

## Dependency layers

| Layer | Needed for | Evidence/verification |
|---|---|---|
| OpenCDA Python package | CLI/config and module imports | `python -m pip install -r requirements.txt` or the documented conda environment; `python -m pip check` |
| Scientific/visual stack | core managers and plotting/sensors | NumPy, SciPy, matplotlib, networkx, OpenCV, Open3D, Shapely, OmegaConf and related requirements |
| CARLA Python API | any actual CARLA scenario | install the egg/API matching the server; `python -c "import carla; print(carla.__file__)"` |
| CARLA server and maps | any simulation | start the matching server; connect on `world.client_port` (default 2000), load requested town/custom map |
| PyTorch + YOLOv5 | `--apply_ml` perception paths | install versions compatible with the GPU/CUDA and scenario; `python -c "import torch"` plus the model import used by the selected module |
| SUMO + `traci` | `*_cosim` scenarios | install SUMO, set `SUMO_HOME` where required, install `traci`, provide matching network/route files |
| ScenarioRunner/OpenSCENARIO | `openscenario_carla` | install and verify the external ScenarioRunner/OpenSCENARIO integration; not supported by the supplied Docker note |

Inspection evidence for this production verified OpenCDA imports, CARLA 0.9.12
client import, OmegaConf, the scientific stack, and core manager imports after
compatible pins; `pip check` passed. It did **not** verify a CARLA server,
SUMO, ScenarioRunner, PyTorch, or YOLOv5 runtime. Treat those as external gates.

## Local setup

From the checkout root, the upstream documentation gives this general flow:

```bash
conda env create -f environment.yml
# Use the selected environment's Python explicitly:
python setup.py develop
# Or, in a prepared compatible environment:
python -m pip install -r requirements.txt
python -m pip check
```

Do not mutate the Python running the agent or a user-owned environment; use an
isolated prefix and its explicit Python executable.

The checked-in `requirements.txt` includes pinned scientific packages and
OmegaConf but does not itself provide CARLA, PyTorch/YOLOv5, SUMO, or
ScenarioRunner. `environment.yml` specifies Python 3.7.10; the inspected
Python 3.8 environment required compatible pins, so record the resolved
versions when using another Python version.

## CARLA API installation

Install the CARLA Python API from the official release package or a
compatible source build, matching the server release and Python ABI, then
verify it independently:

```bash
python -c "import carla; print(getattr(carla, '__file__', 'loaded'))"
```

The source release includes a legacy helper that expects `CARLA_HOME`, a
Python 3.7 Linux egg under `CARLA_HOME/PythonAPI/carla/dist/`, and performs
local cache copying plus editable installation. That helper is intentionally
not part of this self-contained skill because it mutates the checkout and
assumes shell activation. Prefer a reviewed, explicit installation command for
the official client artifact. A client import is necessary but not sufficient:
the CARLA server binary must also be started separately and use the same
release. OpenCDA selects different blueprint names for 0.9.11 and 0.9.12, so
pass the matching `-v` value.

CARLA 0.9.11 and 0.9.12 are the documented supported versions for this source.
Additional maps are needed for Town06 scenario testing according to the
installation guide. Customized highway assets/maps may require a CARLA source
build; a precompiled package is otherwise acceptable. Map availability is
server-side and cannot be established by `import carla` alone.

## External server gate

Before a real run, confirm all of the following explicitly:

1. the server release matches `-v`;
2. the server is listening on the YAML `world.client_port` (default 2000);
3. the requested Town05/Town06 or custom map is installed;
4. synchronous mode and `fixed_delta_seconds` are accepted;
5. the host has the required rendering/display/GPU resources, or a supported
   headless configuration;
6. the selected scenario's CARLA Traffic Manager or SUMO path is available.

Do not silently downgrade to async mode. `ScenarioManager` applies
synchronous mode and fixed timestep and exits when `sync_mode` is false in this
release. Shut down or restore the world settings after an interrupted run.

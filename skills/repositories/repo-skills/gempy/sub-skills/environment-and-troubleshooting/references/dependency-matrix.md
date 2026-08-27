# GemPy dependency matrix

Use this matrix to install only the capability being exercised. Version ranges
below are the public requirements represented by the generated GemPy release;
the three GemPy packages should be kept on a compatible release line.

| Capability | Install | Public imports/probes | Expected result | If absent |
| --- | --- | --- | --- | --- |
| Core model construction and NumPy computation | `python -m pip install gempy` | `import gempy, gempy_engine, numpy` | GemPy imports and the engine is available | Reinstall core; an absent engine is a required-core failure |
| 2-D plotting and tabular input | `python -m pip install "gempy[base]"` | `import pandas`; `import matplotlib.pyplot` | CSV/table helpers and Matplotlib are usable | Install the base extra or the missing package; core import may still work |
| GemPy viewer | base extra or `python -m pip install gempy_viewer` | `import gempy_viewer` | Viewer APIs import | Install a compatible `gempy_viewer`; compare GemPy package versions |
| 3-D viewer rendering | viewer plus a PyVista installation | `import pyvista` | Renderer can be configured | Install PyVista and a supported rendering stack; use off-screen mode headlessly |
| URL-backed example/input retrieval | `python -m pip install "gempy[opt]"` | `import pooch` | URL inputs can be retrieved and hash-checked | Use local files or install Pooch; network access is still a runtime requirement |
| SciPy/skimage optional workflows | `python -m pip install "gempy[opt]"` | `import scipy, skimage` | Optional numerical/image helpers import | Install the optional extra or route to a workflow that does not need them |
| GSTools features | `python -m pip install "gempy[opt]"` | `import gstools` | GSTools-backed operation can start | Install GSTools; do not confuse this with a core import failure |
| GemPy plugins | `python -m pip install "gempy[opt]"` | `import gempy_plugins` | Plugin APIs are discoverable | Install `gempy_plugins` compatible with the GemPy line |
| Subsurface file/topography/borehole integration | install the Subsurface package required by the selected integration | `import subsurface` | Subsurface objects can be passed to GemPy | Install the package for that integration or use arrays/local tables |
| PyTorch backend, gradients, nugget optimization | install a matching PyTorch build | `import torch`; `torch.cuda.is_available()` when relevant | `AvailableBackends.PYTORCH` can be selected | Use `AvailableBackends.numpy` or install the correct CPU/CUDA/ROCm Torch build |
| KeOps acceleration/documentation workflows | install PyKeOps when the selected operation requires it | `import pykeops` | KeOps import succeeds | Omit KeOps-dependent work or install it; it is not required for core NumPy use |

## What is required at package import

GemPy's top-level API imports `gempy_engine` and its engine-facing data/API
classes. Therefore a successful `import numpy` alone does not prove a usable
GemPy install. Pandas, Pooch, Subsurface, Torch, and other modules are guarded
by lazy `require_*` helpers or are used only in particular workflows. A missing
optional module should be diagnosed at the call site and not “fixed” by
changing the core backend.

`gempy_viewer` is a companion package, not a substitute for `gempy_engine`.
The base requirements place the viewer and pandas together. The optional group
also includes `gstools`, `gempy_plugins`, `pooch`, `scipy`, and
`scikit-image`. The development/docs dependency sets additionally mention
PyVista, Subsurface, Torch, and PyKeOps; use those only for the corresponding
capability.

## Version and provenance probes

Run these without importing a model or downloading data:

```bash
python -c "import sys; print(sys.version)"
python -c "import importlib.metadata as m; print(m.version('gempy')); print(m.version('gempy-engine'))"
python -c "import gempy, gempy_engine; print(gempy.__version__)"
python -m pip check
```

`importlib.metadata` may report a package as missing even when a checkout is
being shadowed on `sys.path`; use a normal installed package environment for a
publication or recovery claim. Conversely, metadata can exist while an import
fails because a companion package is absent. Record both metadata and import
results.

## Backend facts

The public compute path accepts `GemPyEngineConfig` and branches on
`AvailableBackends.numpy` or `AvailableBackends.PYTORCH`. The default backend is
provided by the engine configuration, so inspect it rather than hard-coding a
value in automation. `GEMPY_USE_GPU=True` requests GPU use through the config;
`GEMPY_GPU_FALLBACK=True` permits the compute path to retry with CPU after a GPU
runtime failure. These variables are case-sensitive in the current code.

For reproducibility record:

1. Python version and the three GemPy package versions.
2. NumPy/PyTorch versions and, for Torch, the reported CUDA availability.
3. Backend enum, `use_gpu`, dtype, and `compute_grads`.
4. Presence of viewer, Matplotlib, PyVista, pandas, and any optional module
   used by the workflow.
5. Whether rendering was interactive or off-screen.

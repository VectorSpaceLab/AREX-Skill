---
name: environment-and-troubleshooting
description: "Install GemPy reproducibly, inspect core and optional
  dependencies, select a safe compute backend, and diagnose import, validation,
  viewer, headless, and version-drift failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: EUPL 1.2
---

# Environment and troubleshooting

Use this route when GemPy cannot be installed, imported, computed, plotted, or
validated, or when a working model behaves differently after an upgrade. It
covers the package boundary and the first diagnostic only. After the first
signal, send modeling/data, grid, or persistence problems to the owning route
in the [root GemPy skill](../../SKILL.md).

## Install a known capability set

Use a fresh Python environment with Python **3.10 or newer**. The published
source advertises Python 3.10--3.12; newer interpreters are not automatically
proven compatible. Use `python -m pip` so pip belongs to the selected Python:

```bash
python -m pip install --upgrade pip
python -m pip install gempy                    # core NumPy-oriented install
python -m pip install "gempy[base]"             # viewer, pandas, and base use
python -m pip install "gempy[opt]"              # base plus optional data/plugins
```

The core install brings `gempy_engine` and NumPy. The `base` extra adds the
companion `gempy_viewer` package and pandas; viewer workflows also need
Matplotlib and, for 3-D rendering, PyVista as described by the viewer package.
The `opt` extra adds GSTools, `gempy_plugins`, Pooch, SciPy, and scikit-image.
Install PyTorch separately using its official selector when a PyTorch backend,
gradients, or nugget optimization is actually required. Do not install all
extras merely to make a core NumPy model run.

Prefer one release line for `gempy`, `gempy_engine`, and `gempy_viewer`.
After installation, run the bundled [environment checker](scripts/check_environment.py)
from any directory:

```bash
python path/to/check_environment.py
python path/to/check_environment.py --backend numpy
python path/to/check_environment.py --require gempy_viewer --require pyvista
python path/to/check_environment.py --strict-optional --json
```

The checker never installs packages or accesses the network. It reports Python
compatibility, distribution metadata, public imports, backend availability,
Matplotlib's active backend, and whether a headless viewer needs off-screen
configuration. Missing optional modules are warnings with a package-specific
recovery command; required core failures return a non-zero status.

## First import and provenance check

A minimal core probe is:

```bash
python -c "import gempy, gempy_engine; print(gempy.__version__)"
python -m pip check
python -m pip show gempy gempy-engine gempy-viewer
```

If `gempy` fails while `gempy_engine` is absent, repair the core install rather
than adding viewer packages. If only `gempy_viewer`, pandas, PyVista, or another
optional import fails, core NumPy modeling can remain usable; install the
smallest extra for the operation that failed. Do not treat `pip check` failures
in unrelated packages as GemPy API evidence, but record them when diagnosing a
contaminated environment.

Before comparing a saved model or result, read the [dependency matrix](references/dependency-matrix.md)
and refresh information in [repo provenance](../../references/repo-provenance.md).
Compare the three GemPy package versions, Python version, backend, dtype, GPU
choice, and optional-module set. Re-run the checker after any upgrade.

## Choose the compute backend deliberately

For the most portable path, construct `GemPyEngineConfig` with
`gp.data.AvailableBackends.numpy` and `use_gpu=False`. The source also exposes
`AvailableBackends.PYTORCH`; use it only after `torch` imports successfully and
its device is usable. `GemPyEngineConfig` reads `GEMPY_USE_GPU` and treats the
exact value `True` as enabled. A GPU request can be made recoverable with
`GEMPY_GPU_FALLBACK=True`; this changes an unavailable GPU request to CPU after
the engine raises its runtime error. Validate the selected backend before a
long computation and keep dtype consistent across a run.

A backend failure is not a data failure. First run:

```bash
python path/to/check_environment.py --backend numpy
python path/to/check_environment.py --backend pytorch
```

If the second command fails because Torch or its accelerator is unavailable,
use the NumPy configuration for ordinary modeling or install the matching
Torch build. Route model construction, interpolation options, and grid-shape
errors to the modeling/grid route after recording this backend result.

## Validation and viewer triage

`compute_model` validates by default. `GeoModel.validate()` raises
`gempy.ModelValidationError` with `field`, `reason`, `message`, and `context`.
The first diagnostic is normally more useful than the later engine traceback:

- `empty_model`: no surface points and no orientations.
- `underdetermined_input`: at most one surface point and no orientation.
- `empty_fault_group` or `empty_non_fault_group`: a structural group has no
  elements.
- `basement_relation_on_non_last_group`: a basement relation is not on the
  final structural group.

Fix the input or structural groups, then compute again. `skip_validation=True`
is an explicit escape hatch for a known, intentionally deferred condition; it
is not a repair and should not be the default. Detailed symptoms and recovery
are in [troubleshooting](references/troubleshooting.md).

If core import and NumPy computation work but plotting fails, check viewer,
Matplotlib, and PyVista independently. A viewer import failure does not imply
that the core model is unusable. In a display-less process, set
`MPLBACKEND=Agg` before importing Matplotlib for file-based 2-D output and use
the viewer/PyVista off-screen option supported by the installed viewer for 3-D.
Do not call interactive `show()` as a headless smoke test. For a direct PyVista
file/render smoke test, configure the public off-screen switch before creating
plots:

```python
import pyvista
pyvista.OFF_SCREEN = True
```

A missing display, OpenGL/EGL problem, or PyVista import error is a
visualization issue; route model/data errors separately.

## Handoff boundary

Always preserve the exact command, package versions, backend, exception type,
validation `reason`/`field`, and whether the process is headless. Then use the
[root route map](../../SKILL.md) for workflow-specific modeling/data/grid/
persistence help. This route owns environment and first-diagnostic facts, not
maintainer documentation builds, deployment scripts, private tests, or a full
modeling tutorial.

# GemPy troubleshooting playbook

Use the smallest reproducer and capture the Python version, `gempy`,
`gempy_engine`, and (when used) `gempy_viewer` versions. Run
`scripts/check_environment.py --json` before changing packages. Do not mix
repair commands with a model-data diagnosis: first establish whether the
failure is core import, optional feature, backend, validation, viewer, or
workflow-specific.

## Decision sequence

1. **Python gate** — GemPy asserts Python >=3.10 at top-level import. If this
   fails, use a supported Python interpreter and recreate the environment.
2. **Core metadata/import** — check `gempy`, `gempy_engine`, and NumPy. A
   missing engine is a required dependency failure; do not start by installing
   PyVista or Torch.
3. **Dependency consistency** — run `python -m pip check` and compare the
   GemPy companion versions. Repair a conflicting environment in a fresh
   environment when possible.
4. **Optional feature** — identify the first missing lazy dependency and install
   only the relevant extra/package, or use a core-compatible alternative.
5. **Backend** — explicitly probe NumPy or PyTorch and GPU availability before
   interpreting an engine traceback as bad data.
6. **Validation** — inspect `ModelValidationError.field`, `.reason`,
   `.message`, and `.context`; fix model semantics before bypassing checks.
7. **Viewer/headless** — prove core compute separately from 2-D/3-D rendering.
8. **Drift** — record versions, environment variables, backend, dtype, input
   hashes, and source provenance before claiming reproducibility.

## Install and import failures

| Symptom | Likely cause | Recovery and confirmation |
| --- | --- | --- |
| `ModuleNotFoundError: gempy_engine` while importing `gempy` | Core install is incomplete or companion package is not on the same interpreter's path | Run `python -m pip install --upgrade gempy`; then `python -c "import gempy, gempy_engine"`. If the error persists, inspect `python -m pip show gempy gempy-engine` and create a clean environment. |
| `AssertionError` mentioning Python 3.10 | Interpreter is older than the package requirement | Use Python 3.10+ and reinstall. The source metadata advertises 3.10, 3.11, and 3.12; verify newer versions rather than assuming support. |
| `import gempy` works but `import gempy_viewer` fails | Viewer is not part of the core install or its companion version is incompatible | Install `python -m pip install "gempy[base]"` or the matching `gempy_viewer`; rerun the checker. Core NumPy workflows may remain usable. |
| `pip check` reports conflicts | Shared environment contains incompatible requirements | Treat this as an environment signal, not a GemPy model diagnosis. Record the output, then repair in a fresh environment or align the conflicting package versions. |
| Metadata exists but import fails | Broken wheel, shadowed module, or missing transitive dependency | Compare metadata and import results with the checker; do not copy installation locations into reports. Reinstall the affected distribution in a clean environment. |
| `ImportError` appears only after an upgrade | GemPy, engine, viewer, or NumPy release lines drifted apart | Pin a tested compatible set, reinstall together, and rerun import plus a tiny core smoke test. Check [provenance](../../../references/repo-provenance.md) before comparing results. |

## Optional dependencies

GemPy uses lazy `require_*` helpers that raise a feature-specific
`ImportError`. The missing module is actionable:

| Missing module or symptom | Feature that is blocked | Recovery |
| --- | --- | --- |
| `pandas` | CSV/table reading and table conversion | Install `python -m pip install "gempy[base]"` or pandas, then retry the table operation. |
| `matplotlib` | 2-D plots and some grid helpers | Install `python -m pip install "gempy[base]"`; in headless jobs set `MPLBACKEND=Agg` before importing Matplotlib. |
| `gempy_viewer` | GemPy viewer calls | Install the base extra or a compatible viewer package. Keep core compute as a separate check. |
| `pyvista` | 3-D rendering | Install PyVista and its supported rendering dependencies; configure off-screen rendering for CI/server jobs. |
| `pooch` | URL-backed input retrieval | Install `python -m pip install "gempy[opt]"`, or pass local input files. URL retrieval also requires network access and a valid known hash. |
| `scipy` or `skimage` | Optional numerical/image workflows | Install the optional extra or route to a workflow that does not need those modules. |
| `gstools` | GSTools-backed operations | Install the optional extra; this is not required for ordinary NumPy modeling. |
| `gempy_plugins` | Plugin workflows | Install the optional extra and verify plugin compatibility with the GemPy release line. |
| `subsurface` | Subsurface topography/borehole adapters | Install the Subsurface distribution required by the selected adapter, or use arrays/local tables. |
| `torch` | PyTorch backend, gradients, and nugget optimization | Install a matching PyTorch build; otherwise use the NumPy backend. |
| `pykeops` | KeOps-dependent advanced/documentation workflows | Install PyKeOps only when that workflow requires it. |

The checker prints a concrete suggested command for missing modules but never
runs it. If an optional feature is not needed, leave it absent and document the
chosen core-only path.

## Backend and configuration failures

### NumPy versus PyTorch

The compute API accepts `GemPyEngineConfig` with `backend`, `use_gpu`, `dtype`,
and `compute_grads`. The supported GemPy-side cases inspected here are
`AvailableBackends.numpy` and `AvailableBackends.PYTORCH`. Start with:

```python
import gempy as gp

engine_config = gp.data.GemPyEngineConfig(
    backend=gp.data.AvailableBackends.numpy,
    use_gpu=False,
)
solutions = gp.compute_model(model, engine_config=engine_config)
```

For a PyTorch attempt, first prove `import torch` and, if GPU is requested,
`torch.cuda.is_available()`. A CPU-only Torch installation is not evidence that
the requested accelerator works. If GPU startup raises a runtime error, either
set `use_gpu=False` or set `GEMPY_GPU_FALLBACK=True` when accepting an automatic
CPU retry is appropriate. Record the actual backend and device in the result.

If an unsupported backend enum reaches `compute_model`, it raises a backend
`ValueError`; use the public enum rather than a string guessed from an older
GemPy version. A backend mismatch must be fixed before changing points,
orientations, or grids.

### Dotenv and effective settings

GemPy's configuration loader can load dotenv values discovered from the package
configuration context, a user-level dotenv location, or the normal dotenv
search. This can make `GEMPY_USE_GPU`, `GEMPY_GPU_FALLBACK`, or other engine
settings differ between shells. For a reproducible run, set intended values in
the process environment, record only the relevant variable names and values,
and avoid relying on an unknown dotenv file. Use `GEMPY_USE_GPU=True` only when
GPU use is intended; the current comparison is exact and case-sensitive.

## Model validation failures

`compute_model` calls `model.validate()` unless `skip_validation=True`. The
first violation is a `ModelValidationError`, not an indication that the engine
is broken. Inspect the structured attributes:

```python
try:
    model.validate()
except gp.ModelValidationError as exc:
    print(exc.field, exc.reason, exc.message, exc.context)
```

| `reason` | Meaning | Recovery |
| --- | --- | --- |
| `empty_model` | Both surface-point and orientation tables are empty | Add input data, then verify table lengths before compute. |
| `underdetermined_input` | At most one surface point and no orientations | Add more surface points or at least one orientation for the intended model. |
| `empty_fault_group` | A fault structural group has no elements | Add the intended structural elements or remove the empty fault group. |
| `empty_non_fault_group` | A non-fault structural group has no elements | Populate or remove the group, preserving the intended structural order. |
| `basement_relation_on_non_last_group` | A group marked basement is not last | Move the basement relation to the final group or correct the relation. |

Validation precedence matters: an entirely empty model reports `empty_model`
before group-specific rules. Use `skip_validation=True` only to isolate an
already-understood downstream issue or to load/inspect an intentionally partial
model; it does not make that model semantically valid. After this first check,
route malformed input, structural groups, interpolation options, and grid shape
to the owning modeling/data/grid sub-skill in the root map.

## API and data boundary failures

- A `require_pandas()` error during CSV import means the tabular dependency is
  absent; it is not a malformed CSV diagnosis until pandas imports.
- URL input paths invoke Pooch and known-hash retrieval. Test with local files
  first when separating network/hash problems from table schema problems.
- Subsurface adapters require a real Subsurface object, not a NumPy array with a
  similar shape. Use the array-based topography API when the data is already in
  memory.
- `compute_model_at` changes the model's active custom grid before computing and
  explicitly warns about side effects. If the next result uses an unexpected
  grid, inspect/reset the active grid and route the grid issue to the grid
  sub-skill.
- `save_model`/`load_model` use the `.gempy` extension and the persistence route
  owns file corruption, serialization, and round-trip failures. Preserve the
  first environment diagnostic here, then hand off rather than treating a
  serialization error as an install error.

## Viewer and headless failures

### Core succeeds, viewer fails

Run the core probe without importing viewer code, then probe each layer:

```bash
python -c "import gempy, gempy_engine; print('core ok')"
python -c "import gempy_viewer; print('viewer import ok')"
python -c "import matplotlib; print(matplotlib.get_backend())"
python -c "import pyvista; print('pyvista import ok')"
```

If only the viewer layer fails, retain the core result and repair that layer.
Do not “fix” a viewer error by switching the model's interpolation backend.

### Headless process

For file-based 2-D output, set the environment before the first Matplotlib
import:

```bash
MPLBACKEND=Agg python your_repro.py
```

For 3-D, configure the installed viewer/PyVista for off-screen rendering rather
than invoking interactive windows. A missing `DISPLAY`, X/Wayland connection,
OpenGL/EGL library, or renderer is a host/viewer issue. Avoid claiming that a
headless import proves a rendered image; validate an output file or a safe
viewer smoke test separately. Do not include GUI setup or maintainer docs-build
scripts in a runtime GemPy workflow.

## Provenance drift

When a formerly working workflow changes, compare:

- source commit/tag recorded in [repo provenance](../../../references/repo-provenance.md);
- Python and package versions from `importlib.metadata`;
- NumPy/PyTorch versions and Torch device availability;
- backend enum, `use_gpu`, dtype, and gradient setting;
- optional modules actually imported;
- model input file hashes, coordinate columns, and interpolation/grid settings;
- interactive versus headless rendering and relevant environment variables.

Do not infer reproducibility from a matching top-level `gempy.__version__`
alone. A companion engine or viewer change can alter behavior. If provenance
is stale, refresh the GemPy skill before treating a new API or error message as
established behavior.

# ANTsPy Troubleshooting

Use this reference for cross-cutting failures before diving into a specific workflow sub-skill.

## Install and Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'ants'` | `antspyx` is not installed in the active Python environment. | Install with `pip install antspyx` or `conda install conda-forge::antspyx`, then run `python -c "import ants"`. |
| `ModuleNotFoundError: No module named 'antspyx'` | The distribution name is not the import name. | Import with `import ants`; use `antspyx` only for package installation and metadata. |
| Import fails with missing compiled library or `cannot import name 'lib'` | A source tree without built native extensions is shadowing the installed wheel, or the wheel/native library is incompatible. | Run from a neutral working directory and rerun `python -c "import ants"`. If it still fails, reinstall a compatible wheel or use conda-forge. |
| Pip attempts a source build unexpectedly | No compatible wheel exists for the current Python/platform, or platform compatibility checks rejected the wheel. | Prefer conda-forge, use a supported Python version, or follow a deliberate source-build path with CMake/ITK/ANTs prerequisites. |
| Windows import/runtime failure | Missing compatible Microsoft Visual C++ Redistributable or wheel/platform mismatch. | Install the supported VC++ Redistributable and prefer published wheels/conda packages. |
| macOS pip compiles from source when a wheel should exist | macOS version compatibility checks can reject available wheels. | Try the documented `SYSTEM_VERSION_COMPAT=0` environment setting only for installation, then verify import. |

Run [../scripts/antspy_environment_check.py](../scripts/antspy_environment_check.py) after fixing import problems.

## Binary Wheel Versus Source Build

Normal users should prefer prebuilt `antspyx` packages. Source builds involve CMake, nanobind, ITK/ANTs native code, compilers, and platform-specific library paths. The repository's ANTs/ITK configuration scripts are build evidence, not runtime helpers for this skill.

If a user truly needs a source build:

1. Confirm the Python version is supported by package metadata.
2. Install normal runtime dependencies first: NumPy, pandas, PyYAML, statsmodels, matplotlib, Pillow, webcolors, requests, and scikit-learn.
3. Ensure a compiler/CMake toolchain can build native ANTs/ITK wrappers.
4. Run a clean import and tiny image smoke test before debugging higher-level workflows.

## Physical-Space and Data Validation

- Shape equality is not enough. Check `dimension`, `shape`, `origin`, `spacing`, and `direction` before mixing images.
- Use `ants.image_physical_space_consistency(a, b)` before arithmetic, overlays, masks, labels, transform application, matrix extraction, or overlap metrics.
- Use `datatype=True` when pixel type and component count must match.
- Do not repair metadata with `copy_image_info` when the image was actually resampled, cropped, padded, reoriented, or transformed. Use the owning image-ops or registration workflow.

## API Misuse Patterns

- `ants.from_numpy(...)` expects a NumPy array, not a Python list.
- `img.numpy()` returns a copy; edits do not affect the image. Use `img.view()` only when shared-memory mutation is intentional.
- Label images should be integer-like before label statistics, geometry, overlap, or label-safe transform application.
- Registration points use physical coordinates in DataFrames; they are not voxel indices.
- Use label-safe interpolation (`nearestNeighbor` or `genericLabel`) for labels and masks.

## Optional Dependencies

- Plotting requires Matplotlib and may need a non-interactive backend such as `Agg` in CI or headless environments.
- nibabel and SimpleITK interop require those packages to be installed separately when the conversion path is used.
- ANTsPy's `deeplearn` module contains helper utilities, not neural-network framework training code.

## Runtime and Cost Triage

- Start with tiny synthetic or packaged fixture images when reproducing failures.
- Use `Translation`, `Rigid`, `QuickRigid`, or `AffineFast` before expensive nonlinear transforms when debugging registration setup.
- Treat full SyN, template building, motion correction, joint label fusion, KellyKapowski, and large 3-D N4/bias-correction workflows as potentially expensive.
- Run [../scripts/run_antspy_smoke_suite.py](../scripts/run_antspy_smoke_suite.py) to separate package/runtime issues from data-specific failures.

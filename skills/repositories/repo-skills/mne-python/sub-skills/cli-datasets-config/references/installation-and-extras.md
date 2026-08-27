# Installation and optional dependency choices

Use this reference to choose the smallest MNE-Python installation that supports the requested workflow, then verify it with import, CLI, and `sys_info` checks. Do not install broad extras merely because they exist.

Source evidence: `README.rst`, `pyproject.toml`, `doc/install/index.rst`, `doc/install/manual_install.rst`, `doc/install/check_installation.rst`, `doc/install/advanced.rst`, environment preparation and installed smoke evidence.

## Baseline package requirements

The project metadata requires Python `>=3.11`. Core runtime dependencies include NumPy, SciPy, Matplotlib, Pooch, tqdm, Jinja2, decorator, lazy-loader, and packaging. The console script is named `mne`.

Fast verification after any install:

```bash
python -c "import mne; mne.sys_info(check_version=False)"
mne --version
mne sys_info --no-check-version --ascii
```

Expected result: MNE imports, CLI version prints, and `sys_info` lists core dependencies plus unavailable optional packages instead of crashing.

## User installation choices

| Need | pip choice | conda choice | Notes |
| --- | --- | --- | --- |
| Core MNE-Python with minimal dependencies and 2D plotting | `pip install mne` | `conda create --channel=conda-forge --strict-channel-priority --name=mne mne-base` | Good for CLI help, config, datasets, FIF inspection, many core APIs, and non-GUI workflows. |
| Full user environment | `pip install "mne[full]"` | `conda create --channel=conda-forge --strict-channel-priority --name=mne mne` | Adds broad numerical, visualization, file-format, notebook, and ecosystem dependencies. Use when the task needs 3D/Qt/report-rich workflows or many vendor readers. |
| Full without installing a Qt binding | `pip install "mne[full-no-qt]"` | choose packages explicitly with conda | Useful when the platform already manages Qt or the task must avoid GUI bindings. |
| Full with a specific Qt binding | `pip install "mne[full-pyside6]"` or `pip install "mne[full-pyqt6]"` | conda-forge full install ships a Qt choice | Choose only when visualization/browser workflows need that binding. |
| HDF5 and MATLAB-like I/O support | `pip install "mne[hdf5]"` | `conda create --override-channels --channel=conda-forge --name=mne mne-base h5io h5py pymatreader` | Needed for functions that require HDF5-style I/O, including several file readers and `SourceMorph.save`. |
| Existing core install that now needs HDF5 support | `pip install h5io pymatreader` | install `h5io`, `h5py`, and `pymatreader` into the active env | Re-run `mne sys_info --no-check-version` after installing. |
| Contributor/development checkout | `pip install -e ".[test_extra,doc]"` | use the repository's documented dev environment tooling | Route lint/test/changelog/doc-build policy to `repo-development`; do not apply maintainer workflows to ordinary user analysis. |

## Optional dependency families

`mne.sys_info()` groups optional packages into practical families:

- Numerical: scikit-learn, threadpoolctl, numba, nibabel, nilearn, dipy, openmeeg, python-picard, cupy, pandas, h5io, h5py.
- Visualization: pyvista, pyvistaqt, vtk, qtpy, ipympl, pyqtgraph, mne-qt-browser, ipywidgets, trame packages.
- Ecosystem and file-format support: mne-bids, mne-nirs, mne-features, mne-connectivity, mne-icalabel, mne-bids-pipeline, autoreject, neo, eeglabio, edfio, curryreader, mffpy, pybv, pymef, antio, defusedxml.
- Developer-only: pytest, pytest plugins, pre-commit, ruff, sphinx, numpydoc, notebook execution tools, packaging infrastructure.

Choose extras from the task:

- FIF, NumPy synthetic data, configuration, dataset path checks, and command help usually need only the core package.
- HDF5/MATLAB-related file readers need `mne[hdf5]` or equivalent packages.
- 3D visualization, coregistration GUI, browser GUI, and rich reports may need Qt/PyVista/VTK/browser packages and a working display or headless rendering setup.
- Source modeling may need anatomical datasets plus external tools such as FreeSurfer or OpenMEEG, depending on the workflow.
- Decoding needs scikit-learn for estimator workflows.
- CUDA acceleration needs a compatible NVIDIA driver plus CuPy and explicit MNE CUDA configuration; it is optional for most workflows.

## Install decision checklist

1. Identify the exact task and owning sub-skill.
2. Decide whether the task needs only CLI/config/dataset probes, core analysis, HDF5 readers, GUI/3D/report output, source modeling/external binaries, decoding, CUDA, or development tooling.
3. Install the smallest environment that satisfies those needs.
4. Run `python -c "import mne; mne.sys_info(check_version=False)"` and `mne --version`.
5. For optional features, confirm their package availability in `sys_info` before calling APIs that require them.
6. If the task is a repository edit or native test plan, switch to `repo-development` for project-specific policy before running maintainer commands.

## Headless and notebook notes

- For headless servers, prefer non-interactive plotting (`show=False`) and `mne report --no-browser`; route plotting-backend decisions to `visualization-reporting`.
- Notebook and 3D visualization workflows often need a Qt backend, notebook backend, or PyVista/VTK setup. Confirm with `sys_info` before promising interactivity.
- Remote/offline environments should use `mne sys_info --no-check-version` and `download=False` dataset checks.

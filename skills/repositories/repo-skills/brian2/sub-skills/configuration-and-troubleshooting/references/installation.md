# Brian2 installation and environment baseline

This reference is for Brian2 2.9.0. The distribution is named `Brian2`, the
Python import root is `brian2`, and the package declares Python `>=3.12`.
Prefer a dedicated environment per project and one package-manager strategy.

## Verify identity before repairing anything

From a neutral working directory, use the bundled checker first:

```bash
python scripts/check_brian2_env.py --json
python -m pip show Brian2
```

The expected distribution version is `2.9.0`. A package metadata version and an
import version are separate observations: metadata can identify an installed
wheel even when importing `brian2` fails. The checker also compares each
versioned base dependency against the declared constraint.

A version of `unknown`, or an import message saying that Brian's version cannot
be determined, usually means that Python is resolving a source-like checkout
without its generated version metadata or without the build-time
`setuptools_scm` support. A source-like import can also be incomplete (for
example, a generated Cython extension is absent). Do not fix this by adding
arbitrary directories to `PYTHONPATH` or by mixing the checkout with another
installation. Run Python from a neutral directory, confirm `python -m pip show
Brian2`, and reinstall the intended released package in the active environment:

```bash
python -m pip install --upgrade --force-reinstall "Brian2==2.9.0"
```

If a known 2.9.0 checkout is intentionally required, an editable install is a
separate development setup and must build Brian's generated Cython extension.
A shallow checkout without release tags can make `setuptools-scm` resolve the
version as `unknown`; after confirming that the checkout really represents
2.9.0, supply the version only for that install command:

```bash
SETUPTOOLS_SCM_PRETEND_VERSION=2.9.0 python -m pip install -e .
```

Do not use that override to label an arbitrary branch as 2.9.0, and do not
claim a wheel installation from an editable source import. If the editable
import reports that `DynamicArray` or another generated Cython extension is
absent, install the released wheel/Conda package or complete the supported
editable build in its own environment. After any repair, start a fresh
interpreter and rerun the checker.

## Required baseline

Brian2 2.9.0 declares these runtime dependencies. The `README` may describe a
broader historical minimum for NumPy; use the 2.9.0 `pyproject.toml`/package
metadata constraint shown here when resolving this release:

| Package | Requirement or role |
|---|---|
| Python | `>=3.12` |
| NumPy | `>=2.2.0` |
| Cython | `>=0.29.21`; needed for the compiled Cython runtime |
| SymPy | `>=1.2` |
| PyParsing | `>=3`, but not `3.2.4` |
| Jinja2 | `>=2.7` |
| setuptools | `>=61` |
| packaging | required by package tooling/runtime checks |
| py-cpuinfo | only declared on Windows |

For Windows, `py-cpuinfo` is the only platform-specific base dependency. The
checker reports it as required only on Windows and reports the other packages
as required on every platform.

Brian's import-time dependency check probes NumPy, SymPy, PyParsing, and
Jinja2. Cython is additionally exercised when the compiled Cython target or
source-built extensions are used; the package metadata still declares it as a
runtime dependency. If `brian2` import or the requested target reports a
missing required package, repair the dependency set rather than suppressing
the error. Check the active interpreter explicitly:

```bash
python -c "import sys; print(sys.version)"
python -m pip check
```

Do not use `pip` from a different interpreter. Prefer `python -m pip` (or the
matching `conda` executable) so the installation and import use the same
environment. An incompatible Python version cannot be repaired by upgrading
Brian2; create an environment with Python 3.12 or newer.

## pip installation

In a fresh virtual environment or other isolated Python environment:

```bash
python -m pip install "Brian2==2.9.0"
```

For an exact package repair, use the same command with `--force-reinstall` only
after recording the current failure and confirming that replacement is allowed.
Do not mix editable checkout imports with a released wheel. `pip check` should
be clean, and this minimal check should succeed:

```bash
python -c "import brian2; print(brian2.__version__)"
```

The package's test extra is separate from runtime requirements:

```bash
python -m pip install "Brian2[test]==2.9.0"
```

It provides `pytest`, `pytest-xdist`, `pytest-cov`, and `pytest-timeout`; it does
not install GSL, Matplotlib, SciPy, Pandas, Jupyter, or `brian2tools`.

## Conda installation

Use a new environment and the community `conda-forge` channel. Pin the
package when the 2.9.0 operating contract is required:

```bash
conda create -n brian2-2.9 -c conda-forge python=3.12 "brian2=2.9.0"
conda activate brian2-2.9
```

If the channel does not provide that exact build for the selected platform,
use the pinned PyPI install in a fresh environment rather than silently
accepting another Brian release.

If the project requires the test tools, install them in that same environment
rather than relying on a different Python:

```bash
conda install -c conda-forge pytest pytest-xdist pytest-cov pytest-timeout
```

The Conda package can provide a compiler toolchain on Linux and macOS, but
still verify the compiler name before selecting a compiled target. Avoid
combining a Conda Brian2 package with unrelated pip versions of NumPy, Cython,
or SymPy unless the environment's package state has been intentionally checked.

## C++ compiler prerequisite

The NumPy target does not need a C compiler. Cython-generated C++ code and
C++ standalone workflows do. Cython itself is a Python dependency; it is not a
C++ compiler.

- **Linux/macOS:** verify a C++ compiler name with `g++ --version` (or an
  approved `c++`/`clang++` tool). Install the compiler through the operating
  system or Conda package manager if it is absent. Do not infer a working
  toolchain merely from a Python package import.
- **Windows:** install the Microsoft Visual C++ Build Tools with C++ build
  tools, a current MSVC toolset, and a Windows SDK. Brian's documentation notes
  that `setuptools >=34.4.0` is needed for this path; Brian2 2.9.0's declared
  baseline is newer (`>=61`). Open a shell where the MSVC environment is
  available, or configure the supported MSVC preference when required.
- **Unix compiler selection:** Brian's C++ preference accepts the default
  compiler or `unix`/`msvc` selection. To select a particular Unix compiler
  binary, use the `CXX` environment variable. Detailed target and build choices
  belong to the code-generation route.

A compiler executable being present is only a prerequisite observation. A real
Cython or C++ build can still fail because of incompatible compiler flags,
headers, SDKs, linker libraries, permissions, or ABI mismatch. Do not run a
native build as part of a read-only diagnosis. The NumPy target is the
no-compiler fallback; it does not validate Cython or C++ standalone support.

## Optional capability boundaries

Install only what the workflow needs:

| Capability | Package/system requirement | Boundary |
|---|---|---|
| GSL state updaters | Native GSL headers and libraries, plus Brian's GSL integration | Not proved by `import gsl`; route target/codegen details elsewhere |
| SciPy | `scipy` | Needed by selected NumPy spatial/multicompartment operations; not a core import requirement |
| Matplotlib | `matplotlib` | Plotting and the convenient `from brian2 import *` pylab namespace; not required for core import |
| Pandas | `pandas` | Pandas state import/export formats; not required for core simulation |
| IPython/Jupyter | `ipython`, `notebook`/Jupyter packages | Interactive shell/notebook only; notebook output has its own limitations |
| brian2tools | separate `brian2tools` package | Visualization/analysis helpers, not part of Brian2 |
| pytest | `pytest>=8` | Required by `brian2.test()` and repository tests |

The install documentation provides these examples when appropriate:

```bash
# pip
python -m pip install scipy matplotlib pandas ipython notebook brian2tools pytest

# conda-forge where packages are available
conda install -c conda-forge scipy matplotlib pandas ipython notebook pytest
# brian2tools is a separate package/channel choice; verify its packaging first.
```

Do not install optional packages merely to make the checker green. Record
missing optional capabilities and select a supported fallback. For example,
use the NumPy target for a core smoke when Cython/compiler setup is unavailable,
and use a non-GSL state updater when native GSL is not prepared. A fallback is
not evidence that the optional workflow works.

## Test-suite guidance

After installation, a small package-level test is useful if `pytest` is
available:

```python
import brian2
brian2.test(codegen_targets="numpy", test_codegen_independent=True)
```

`brian2.test()` raises an import error when pytest is absent. The test harness
resets preferences to defaults by default and restores the previous values on
completion. It can test `numpy` and, when Cython is importable, `cython`; GSL is
excluded unless `test_GSL=True` and the native development dependency is
available. Use a narrow target or selected pytest node for diagnosis, not a
full suite or long/standalone run by default.

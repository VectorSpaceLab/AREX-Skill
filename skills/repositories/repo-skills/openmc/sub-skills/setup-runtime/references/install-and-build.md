# Install and build OpenMC

Use this reference to establish the smallest runtime that matches the requested
operation. Commands below are templates: replace `/path/to/openmc-source` and
`/path/to/openmc-build` with the user's actual paths, and run them from a
trusted, dedicated environment.

## Choose the installation shape

| Need | Minimum route | What it proves |
|---|---|---|
| Python model construction or XML generation | Install the Python package and its dependencies | `import openmc` works; no native transport implied |
| Command-line simulation or plotting | Python package plus a CMake-built/installable `openmc` executable | XML inputs can be handed to the native runtime |
| `Model.init_lib`, `openmc.lib`, C-API workflows, or library-mode execution | Python package plus a CMake-built shared `libopenmc` discoverable by the package | The ctypes library can load and initialize |
| Native unit tests | CPU CMake build with tests enabled, then `ctest` | C++ test targets were configured and built; data-dependent tests remain conditional |

The package metadata requires Python 3.12 or newer and declares the base
runtime dependencies (NumPy, h5py, SciPy, IPython, Matplotlib, pandas, lxml,
uncertainties, and endf). The `test` extra adds pytest and test-support
packages. `depletion-mpi` adds mpi4py; `docs`, `ci`, and `vtk` are purpose-
specific extras.

## Python package installation

For a released/package-manager installation, use the package manager selected
by the user (for example, a Conda environment from conda-forge). For a source
checkout, install into the active environment with one of:

```sh
python -m pip install .
python -m pip install -e .[test]
```

Use `python -m pip`, not a possibly unrelated `pip`, so the package and its
interpreter are paired. Verify the package gate before attempting native work:

```sh
python -c 'import openmc; print(openmc.__version__)'
python -m pip check
```

An editable install is convenient for development but does not build the C++
executable or guarantee that `openmc.lib` can load. The source install guide
also notes that native `make install` and Python-package installation are
separate concerns; install the Python package explicitly when needed.

## CPU CMake build

The native build requires a C/C++ compiler, CMake 3.16 or newer, and HDF5 with
C and high-level components. OpenMP is enabled by default; MPI, DAGMC,
libMesh, profiling, coverage, and strict floating-point behavior are explicit
options. A conservative CPU build is:

```sh
cmake -S /path/to/openmc-source -B /path/to/openmc-build \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DOPENMC_USE_OPENMP=ON \
  -DOPENMC_USE_MPI=OFF \
  -DOPENMC_BUILD_TESTS=ON
cmake --build /path/to/openmc-build --parallel
```

The default build type is `RelWithDebInfo` when none is supplied. CMake places
the executable under the build `bin/` directory and the shared library under
its `lib/` directory; the build also copies the shared library into the Python
package's `openmc/lib/` directory for a source-tree development workflow. Do
not infer that copy has happened until the file and a real `import openmc.lib`
check both succeed.

For a local installation rather than using build-tree paths:

```sh
cmake -S /path/to/openmc-source -B /path/to/openmc-build \
  -DCMAKE_INSTALL_PREFIX="$HOME/.local" \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DOPENMC_USE_OPENMP=ON \
  -DOPENMC_USE_MPI=OFF
cmake --build /path/to/openmc-build --parallel
cmake --install /path/to/openmc-build
```

If CMake cannot find HDF5, point it at the matching installation, for example:

```sh
HDF5_ROOT=/path/to/hdf5 cmake -S /path/to/openmc-source \
  -B /path/to/openmc-build -DOPENMC_USE_OPENMP=ON
```

The HDF5 compiler/toolchain must be compatible with the compiler used for
OpenMC. A parallel HDF5 installation requires MPI support; configure with
`-DHDF5_PREFER_PARALLEL=ON -DOPENMC_USE_MPI=ON` and provide a working MPI
implementation rather than mixing serial OpenMC with parallel HDF5.

## Feature flags and their evidence boundary

- `OPENMC_USE_OPENMP=ON|OFF`: shared-memory threading; the compiler must support
  OpenMP 3.1 or newer. Default is `ON`.
- `OPENMC_USE_MPI=ON`: distributed-memory support; CMake must find MPI and the
  run must be launched through a compatible `mpiexec`/`mpirun`. Default is
  `OFF`, and availability is not assumed.
- `OPENMC_ENABLE_STRICT_FP=ON`: disables selected floating-point optimizations
  and keeps assertions active in `RelWithDebInfo`; use for reproducible test
  references, not as a general performance default.
- `OPENMC_BUILD_TESTS=ON`: builds C++ tests for CTest; default is `ON` in the
  current build configuration.
- `OPENMC_USE_DAGMC=ON`, `OPENMC_USE_LIBMESH=ON`, and `OPENMC_USE_UWUW=ON`:
  optional integrations with additional dependencies. UWUW requires DAGMC
  support. Do not describe them as installed without a successful CMake
  configure and feature probe.
- `OPENMC_ENABLE_PROFILE` and `OPENMC_ENABLE_COVERAGE`: instrumentation modes;
  use only when the corresponding profiling/coverage workflow is intended.

If a build uses git submodules, a configure failure about missing vendored
libraries means the source checkout is incomplete or its submodules were not
made available. Repair the trusted checkout separately; never hide that failure
by copying arbitrary third-party files into the build.

## Data is a separate prerequisite

Transport needs a cross-section index, normally `cross_sections.xml`, and the
HDF5 files named by that index. Set the environment variable for the process or
shell that will run OpenMC:

```sh
export OPENMC_CROSS_SECTIONS=/path/to/data/cross_sections.xml
```

The Python configuration object can also set and synchronize the variable:

```python
import openmc
openmc.config['cross_sections'] = '/path/to/data/cross_sections.xml'
```

Setting the Python configuration path resolves it by default and warns if the
path does not exist. It does not download data or repair paths. Validate the
index and all referenced files before running a transport case; see
[troubleshooting.md](troubleshooting.md) and the bundled
[diagnostic script](../scripts/check_openmc_environment.py). The helper parses
XML and checks local `path` references (including a declared `<directory>`
base); it does not prove HDF5 schema compatibility or scientific coverage.

The repository's test data may additionally require `OPENMC_ENDF_DATA` and an
`njoy` executable. These are test/data-processing prerequisites, not a reason
to claim that a normal Python import or XML export is broken. Do not bundle or
invoke a downloader: data acquisition is an explicit user-controlled step.

## Readiness checks after build

Run the least expensive checks in this order, preserving failures as separate
findings. Run the helper from this sub-skill directory, or replace its path
with the location where the generated skill was installed:

```sh
python -c 'import openmc; print(openmc.__version__)'
python scripts/check_openmc_environment.py
python scripts/check_openmc_environment.py --executable openmc
python scripts/check_openmc_environment.py --library PATH_TO_LIBOPENMC
python scripts/check_openmc_environment.py --cross-sections PATH_TO_CROSS_SECTIONS_XML
```

The first helper invocation always checks the Python package and reports the
executable, native-library, and data gates as skipped or unavailable unless
requested. `--executable` accepts either a name resolved on `PATH` or an
explicit executable path and invokes only `--version`. `--library` requests a
specific shared library load. `--cross-sections` parses the XML index and
checks every local `path` reference relative to the index, unless the XML
contains a `<directory>` base. Each requested failure produces a nonzero exit
status; an unrequested missing optional gate does not.

A successful package check plus a missing executable/shared library means the
Python layer is usable but the native build/install gate is incomplete. A
native executable with a missing, malformed, or incomplete cross-section index
is likewise not transport-ready. `openmc.lib` may remain unavailable until the
shared library has been built and is discoverable by the same Python
installation.

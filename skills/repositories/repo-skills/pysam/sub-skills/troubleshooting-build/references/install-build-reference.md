# Install and build reference

## Supported package facts

- Package name: `pysam`.
- Python requirement: `>=3.8`.
- Verified version family: `pysam 0.24.0`.
- Bundled upstream versions in this source release: `htslib 1.23.1`, `samtools 1.23.1`, and `bcftools 1.23.1`.
- Core compiled modules include `pysam.libchtslib`, `pysam.libcalignmentfile`, `pysam.libcalignedsegment`, `pysam.libcbcf`, `pysam.libctabix`, and `pysam.libcfaidx`.

## Recommended install paths

### Bioconda

Use Bioconda when users want the most reliable installation, especially on platforms where compiler flags or non-Python libraries are hard to align:

```bash
conda config --add channels bioconda
conda config --add channels conda-forge
conda config --set channel_priority strict
conda install pysam
```

Why this route helps:

- Conda resolves non-Python dependencies.
- Bioconda packages use preconfigured build options.
- It avoids many macOS compiler and library-path issues.

### PyPI wheels and builtin htslib

The typical PyPI command is:

```bash
python -m pip install pysam
```

When a compatible wheel is available, pip installs it without compiling local C code. When no wheel is available, or when the user forces source compilation with `--no-binary`, the build compiles the `htslib` source bundled with pysam.

Builtin `htslib` is the default PyPI source-build model. It avoids depending on a system `htslib` installation, but still needs a C compiler, Python development headers, and htslib build dependencies.

### Source repository builds

Repository checkouts require Cython before building because the checkout builds Cython extensions from `.pyx` sources:

```bash
python -m pip install 'Cython>=3,<4'
python setup.py install
```

`pyproject.toml` declares `setuptools>=59.0` and `Cython>=3,<4` for the build backend. A PyPI source distribution may include generated C files, but do not assume a repository checkout can build without Cython.

## Builtin htslib configuration

For builtin `htslib` builds, pysam runs htslib configuration during compilation. It tries advanced features first and can fall back to conservative defaults if optional libraries such as `libcurl` or `libcrypto` are unavailable.

Use `HTSLIB_CONFIGURE_OPTIONS` to pass explicit configure options, for example:

```bash
export HTSLIB_CONFIGURE_OPTIONS=--enable-plugins
python -m pip install --no-binary pysam pysam
```

Important behavior:

- A normal wheel install ignores build-time configure options because no local build occurs.
- Use `--no-binary pysam` when the user needs build-time options such as plugin support or profiling.
- Missing optional htslib dependencies can cause a fallback rather than a hard failure; inspect early configure output to distinguish fallback from compiler failure.

## External htslib linking

pysam can link against an externally installed `htslib` to avoid duplicate libraries:

```bash
export HTSLIB_LIBRARY_DIR=/path/to/lib
export HTSLIB_INCLUDE_DIR=/path/to/include
python -m pip install --no-binary pysam pysam
```

Use external linking only when the external `htslib` version is compatible with the pysam release. Version mismatches can cause compile failures, import failures, or subtle runtime errors.

Runtime dynamic linking must also find `libhts` after installation. On ELF-style platforms this often means setting the dynamic loader path, for example:

```bash
export LD_LIBRARY_PATH=/path/to/lib:$LD_LIBRARY_PATH
python -c 'import pysam; print(pysam.__version__)'
```

On macOS, the equivalent diagnosis may involve install names and `DYLD_LIBRARY_PATH`, but prefer conda packages or wheels before asking users to hand-tune dynamic linker settings.

## Profiling builds

Pysam no longer builds Cython code with Python profiling enabled by default. To enable profiling in a source build:

```bash
export PYSAM_PROFILE=1
python -m pip install --no-binary pysam pysam
```

Use this only for diagnostics or profiling tasks. It changes build behavior and requires a local source build.

## Platform and version caveats

- Compilation depends on OS, Python version, compiler, and C library availability.
- `Python.h` failures usually mean the Python development headers for the active interpreter are missing.
- Compiler errors after the first fatal error can be misleading; read the earliest compiler or configure failure first.
- htslib optional features may require additional system libraries.
- Repository builds require Cython; use the version range from `pyproject.toml` unless the user has a release-specific reason to deviate.
- For typing and signatures, prefer `.pyi` files and docstrings because many compiled extension classes do not expose reliable `inspect.signature` data.

## Quick verification commands

After installation, verify import and dependency health:

```bash
python -c 'import pysam; import pysam.libchtslib; import pysam.libcalignmentfile; import pysam.libcbcf; print(pysam.__version__)'
python -m pip check
```

For deeper build configuration diagnostics without leaking paths by default:

```bash
python sub-skills/troubleshooting-build/scripts/inspect_build_config.py
```

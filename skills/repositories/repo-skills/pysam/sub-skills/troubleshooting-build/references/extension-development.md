# Cython Extension Development with pysam

## When To Read

Read this when a user wants to compile Cython code against pysam internals, migrate legacy extension imports, inspect include/link helper functions, or diagnose type-stub and direct-extension behavior.

## Public Helper Functions

Modern pysam exposes helper functions for extension builds:

```python
import pysam

include_dirs = pysam.get_include()
library_args = pysam.get_libraries()
defines = pysam.get_defines()
```

Use these values in a `setuptools.Extension` or `pyximport` build configuration instead of hard-coding package internals. Treat the returned paths and flags as machine-specific build inputs; do not publish them in reusable docs or generated code.

## Minimal `pyximport` Pattern

A small extension build typically follows this shape:

```python
# pyxbld-style helper
from distutils.extension import Extension
import pysam


def make_ext(modname, pyxfilename):
    return Extension(
        name=modname,
        sources=[pyxfilename],
        include_dirs=pysam.get_include(),
        extra_link_args=pysam.get_libraries(),
        define_macros=pysam.get_defines(),
    )
```

In the `.pyx` file, import Cython declarations from `pysam.lib*` modules:

```cython
from pysam.libcalignmentfile cimport AlignmentFile
from pysam.libcalignedsegment cimport AlignedSegment
```

Use public Python APIs when speed is not critical. Direct Cython internals are more sensitive to pysam and htslib version changes.

## Legacy Module Name Migration

Older examples may use direct extension names without the `lib` prefix, such as:

```cython
cimport pysam.csamtools
```

Modern pysam extension modules use the `lib` prefix. Migrate direct imports to the matching `pysam.lib*` module, for example:

```cython
cimport pysam.libcsamtools
from pysam.libcalignmentfile cimport AlignmentFile
```

If the user sees `ImportError: cannot import name csamtools`, check for old direct imports and update them. Ordinary Python code should usually import from `pysam`, `pysam.samtools`, or `pysam.bcftools` instead of direct extension modules.

## Repository Builds vs Installed Packages

- Repository checkouts require Cython because `.pyx` files need to be translated during builds.
- PyPI wheels do not need a local compiler or Cython.
- PyPI source distributions can include generated C files, but repository checkouts should follow the build-system Cython range.
- Use an installed `pysam` package for compiling an external extension; importing from an unbuilt source checkout can shadow compiled modules and fail.

## Type Stubs and Signatures

Many compiled extension classes do not expose reliable `inspect.signature()` data. Prefer:

- `pysam/*.pyi` type stubs for parameter names and return shapes.
- Class/function docstrings for constructor summaries.
- Small runtime smoke tests for behavior that type stubs cannot prove.

Useful stub areas:

- `libcalignmentfile.pyi` for `AlignmentFile`, `AlignmentHeader`, `fetch`, `pileup`, `count`, and `IndexedReads`.
- `libcalignedsegment.pyi` for `AlignedSegment`, flags, tags, CIGAR, pileup records, and quality helpers.
- `libcbcf.pyi` for `VariantFile`, `VariantHeader`, `VariantRecord`, and sample/INFO/FORMAT mappings.
- `libctabix.pyi` and `libcfaidx.pyi` for tabix, FASTA, and FASTQ helpers.

## Build Script Checklist

Before compiling extension code against pysam:

1. Verify `python -c 'import pysam; print(pysam.__version__)'` uses the intended installed package.
2. Confirm Cython is installed when building `.pyx` files.
3. Use `pysam.get_include()`, `get_libraries()`, and `get_defines()` in the extension build.
4. Use `pysam.lib*` Cython imports, not legacy direct names.
5. Compile in a clean build directory when changing htslib, Python, Cython, or compiler versions.
6. If runtime import fails after compilation, inspect dynamic linker paths and htslib compatibility before changing Python code.

## Diagnostic Helper

Run the bundled helper for a redacted build-configuration summary:

```bash
python sub-skills/troubleshooting-build/scripts/inspect_build_config.py
```

Use `--show-paths` only for private diagnostics when the user needs exact include/library paths. Keep those paths out of public skill content and shared reports.

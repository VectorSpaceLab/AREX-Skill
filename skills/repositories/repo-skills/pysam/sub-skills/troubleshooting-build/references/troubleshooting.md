# Install, Import, and Build Troubleshooting

## When To Read

Read this when `pysam` cannot be installed, imported, linked, or used from extension code. For data-level errors after import succeeds, route to the relevant workflow sub-skill.

## Fast Triage

Run these public checks first:

```bash
python -c 'import pysam; import pysam.libchtslib; import pysam.libcalignmentfile; import pysam.libcbcf; print(pysam.__version__)'
python -m pip check
python sub-skills/troubleshooting-build/scripts/inspect_build_config.py
```

If import fails in a source checkout, retry from a neutral directory or a properly installed environment. An unbuilt local checkout can shadow installed compiled extension modules.

## Install Fails While Compiling

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Python.h: No such file or directory` | Python development headers for the active interpreter are missing. | Install Python dev headers for that interpreter, use Bioconda, or use a wheel-compatible Python version. |
| Early htslib configure errors about `libcurl`, `libcrypto`, or plugins | Optional htslib dependencies are missing. | Decide whether optional features are required. If not, conservative fallback may be acceptable; otherwise install the missing libraries and rebuild. |
| `Cython` missing or `.pyx` translation errors from a repository checkout | Repository builds require Cython. | Install `Cython>=3,<4` or use PyPI wheels/Bioconda. |
| Long compiler errors after an early fatal error | Cascading C errors after the real root cause. | Read the first compiler/configure error, not the final undefined names. |
| Build options appear ignored | A wheel was installed instead of building from source. | Use `python -m pip install --no-binary pysam pysam` when build-time options are required. |

Prefer Bioconda when users do not specifically need a custom source build.

## Import Errors After Installation

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` for `pysam.lib...` modules | Package was imported from an unbuilt checkout, partial install, or incompatible wheel. | Verify `python -c 'import pysam; print(pysam.__file__)'` privately, reinstall in a clean environment, and avoid running from a checkout that shadows compiled modules. |
| Dynamic linker error for `libhts` | External htslib build cannot be found at runtime. | Set the platform dynamic loader path for the private environment or rebuild with builtin htslib/compatible Bioconda package. |
| Crashes or undefined symbols after external htslib linking | htslib headers and runtime library do not match pysam's expected version. | Rebuild with a compatible htslib or use builtin/conda packaging. |
| `ImportError: cannot import name csamtools` | Old direct extension name. | Migrate to `pysam.libcsamtools` or use public `pysam.samtools` wrappers. |

## External htslib Problems

External linking requires both build-time and runtime paths:

```bash
export HTSLIB_LIBRARY_DIR=/path/to/lib
export HTSLIB_INCLUDE_DIR=/path/to/include
python -m pip install --no-binary pysam pysam
```

Then the runtime loader must find the same compatible `libhts`. If this is fragile, prefer Bioconda or builtin htslib. Do not mix headers from one htslib version with a runtime library from another.

## Command Wrapper Confusion Is Not an Install Failure

If `pysam.samtools.sort()` raises `pysam.SamtoolsError`, the package imported successfully; route to `../command-wrappers/SKILL.md`. Common command-wrapper fixes include `catch_stdout=False`, `save_stdout`, `usage()`, and `get_messages()`.

## Data Errors Are Not Build Errors

- Missing BAM/CRAM indexes, coordinate shifts, and pileup proxy lifetime errors belong in `../alignment-io/SKILL.md`.
- VCF header/INFO/FORMAT/sample mismatches belong in `../variant-io/SKILL.md`.
- Missing `.tbi`, stale tabix indexes, BGZF-vs-gzip mistakes, and FASTA `.fai` issues belong in `../tabix-fasta/SKILL.md`.

## Deprecated and Renamed Surfaces

- Use `FastaFile` instead of legacy `Fastafile` in new code.
- Use `TabixFile` instead of legacy `Tabixfile` in new code.
- Use `pysam.lib*` extension-module names for direct Cython imports.
- Prefer top-level public APIs and `pysam.samtools`/`pysam.bcftools` wrappers for ordinary Python code.

## Type Checking and Signatures

C-extension classes can make `inspect.signature()` raise `ValueError`. Use `.pyi` stubs, docstrings, and small runtime examples instead. If a type checker disagrees with runtime behavior, inspect the installed version's stubs and avoid assuming a newer or older pysam signature.

## When To Stop and Escalate

Stop and ask for user/environment action when:

- The required compiler, Python headers, or system libraries cannot be installed in the current environment.
- The user explicitly requires an external htslib version that is incompatible with this pysam release.
- The failure involves private library paths, module systems, clusters, or security policies that the user must configure.
- The task requires publishing exact local include/library paths; keep those in private diagnostics, not public skill content.

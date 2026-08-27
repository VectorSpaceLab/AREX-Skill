# Runtime troubleshooting

Use the failure class first. Do not treat every failure as geometry or as a
missing Python dependency.

## Triage matrix

| Observation | Likely gate | First checks | Recovery |
|---|---|---|---|
| `import openmc` fails | Python package/dependency | `python -c 'import openmc'`; `python -m pip check`; interpreter/venv identity | Install the package into the active interpreter and repair the reported dependency; do not start a native build until the base import works |
| Python import works, but `openmc` is not found | Executable/install gate | `command -v openmc`; `openmc --version`; inspect the CMake build `bin/` directory | Build the C++ target, add its install `bin/` directory to the intended `PATH`, or pass `openmc_exec` explicitly |
| Python import works, but `import openmc.lib` fails with a missing `libopenmc.so`/`.dylib` | Native shared-library gate | locate the built shared library; check that the Python package's `openmc/lib/` location contains the platform library; retry import in the same interpreter | Complete the CMake shared-library build and package/install arrangement; a base package import can remain valid while this gate is absent |
| `openmc --version` works but a run reports no `cross_sections.xml` | Data configuration gate | `printf '%s\n' "$OPENMC_CROSS_SECTIONS"`; check settings/material data reference; run the diagnostic helper | Set a real index path for the run, or use the Python config mapping; do not blame geometry until data is configured |
| The index exists but a run cannot open an HDF5 file | Data integrity/path gate | parse the XML and inspect every referenced path; resolve relative paths relative to the index's directory; check permissions and HDF5 file existence | Correct the library layout or index paths and rerun the diagnostic; an existing XML index is insufficient if its HDF5 targets are absent |
| CMake cannot find compiler, HDF5, OpenMP, or MPI | Native configure gate | reread the configure output; check `cmake --system-information` only if needed; verify compiler/HDF5 wrapper and optional dependency paths | Install/provide the missing required dependency; set `HDF5_ROOT` or `CMAKE_PREFIX_PATH`; turn off an optional feature that is not required. Do not turn off required HDF5 to force a partial build |
| CMake detects parallel HDF5 while MPI is off | MPI/HDF5 consistency | inspect the HDF5 variant and `OPENMC_USE_MPI` | Enable MPI with a compatible MPI toolchain, or point CMake to a serial HDF5 installation. Do not mix parallel HDF5 with an MPI-off build |
| CMake reports missing submodules/vendored libraries | Source completeness gate | verify that the trusted checkout's submodules are present | Initialize/update the checkout's declared submodules or use available system packages; do not copy untrusted libraries into `vendor/` |
| `RuntimeError: OpenMC aborted unexpectedly` or a segmentation fault | Native runtime/model/data | retain native output; rerun a tiny case with a Debug CMake build; use geometry-debug for suspected overlap/lost-particle issues | Reduce to a minimal case, check all XML/data paths, and inspect the debug location/output. Escalate with the complete command and native log if unresolved |
| Lost-particle warning or maximum lost particles | Geometry coverage/boundary condition | check that every region, including void, is covered by a cell and that outer surfaces have appropriate boundaries; use `--geometry-debug` with fewer particles | Repair the model geometry/boundaries, then rerun a bounded diagnostic. This route only identifies the runtime symptom; detailed geometry repair belongs to the model/geometry route |
| `Failed to open HDF5 file with mode 'w': summary.h5` | Open HDF5 handle/output collision | close `StatePoint`/summary readers; check that another run is not writing the same directory | Use `with openmc.StatePoint(...) as sp:` or call `close()` before the next run; isolate concurrent runs in separate output directories |
| MPI launch fails, hangs, or oversubscribes | MPI runtime/scheduler | check `mpiexec --version`, native MPI build status, allocation, process binding, and thread count | Use the scheduler's launcher and an allocated process count; start with one process and one/two threads; keep MPI optional/unverified until an actual run succeeds |
| Full tests fail without data or `njoy` | Test prerequisite gate | check `OPENMC_CROSS_SECTIONS`, `OPENMC_ENDF_DATA`, `njoy`, executable, and strict-FP build | Run data-free API/XML tests first; acquire/configure prerequisites through an explicit user-approved process, then rerun only the needed tests |

## Cross-section index validation

Use the bundled [diagnostic script](../scripts/check_openmc_environment.py) for
a non-mutating diagnostic. Run it from this sub-skill directory:

```sh
python scripts/check_openmc_environment.py --cross-sections PATH_TO_CROSS_SECTIONS_XML
python scripts/check_openmc_environment.py --executable openmc \
  --cross-sections PATH_TO_CROSS_SECTIONS_XML --json
```

The helper reports the selected index, XML parse failures, and missing or
non-file paths referenced by `path` attributes. Relative references are
interpreted relative to the directory containing `cross_sections.xml`, unless
the index declares a `<directory>` element, in which case that directory is the
base. This catches the common case where the index exists but its HDF5 files
were moved. The helper does not download data, build anything, change
environment variables, or run a model. It is a path/structure diagnostic, not
a complete validation of nuclide coverage, HDF5 schema compatibility, or
scientific suitability.

The runtime may also obtain the cross-section setting from a materials/settings
XML reference or from `OPENMC_CROSS_SECTIONS`. Keep one deliberate source of
truth for a run and print it in the handoff. A path that exists but is unreadable,
malformed, or points to missing library files remains a failed data gate.

## Executable and native-library gates

A command-line gate is requested explicitly with `--executable openmc` (or an
explicit executable path). The helper resolves a PATH name without a shell and
runs only `--version`; it never passes XML, Python, or other model input to the
program. A nonzero version probe is a failed executable gate.

The native-library report combines package-local `libopenmc` candidates with a
real `import openmc.lib` attempt. A missing package-local file or a loader
error is reported without raising out of the helper. Request `--library PATH`
when a specific shared object must be loaded; that explicit check contributes
to the helper's exit status. An unavailable unrequested native library is a
reported limitation, not a failed Python package check.

## Native library versus package failures

The Python package and C++ runtime are built and loaded independently:

- `import openmc` exercises the Python API and its Python dependencies.
- `openmc --version` exercises the executable and dynamic dependencies.
- `import openmc.lib` loads the packaged/shared `libopenmc` through ctypes.

If only the first succeeds, say **Python API ready; native executable and/or
shared library not ready**. Rebuild/reinstall the native targets and retry with
the same Python interpreter. Do not install a random shared object from another
OpenMC version into the package directory.

## Debug and recovery discipline

1. Save the exact command, current working directory, environment variables
   relevant to the run, native version, and first error line. Record package,
   executable, native-library, and data-index gates separately.
2. Reproduce in a fresh output directory so stale XML, statepoint, summary, and
   restart files cannot mask the failure.
3. Separate the smallest successful gate from the first failed gate: package,
   executable, library, data index, referenced files, XML parse, then transport.
4. For native crashes, configure a new Debug build rather than overwriting a
   working build:

   ```sh
   cmake -S /path/to/openmc-source -B /path/to/openmc-debug \
     -DCMAKE_BUILD_TYPE=Debug \
     -DOPENMC_USE_OPENMP=ON \
     -DOPENMC_USE_MPI=OFF
   cmake --build /path/to/openmc-debug --parallel
   ```

5. For reproducibility/test mismatches, use
   `-DOPENMC_ENABLE_STRICT_FP=ON`, fix the thread count (often
   `OMP_NUM_THREADS=2` for the project test guidance), and avoid comparing
   outputs from different data libraries or optional builds.
6. Never solve a missing-data error by silently substituting an unknown library,
   and never solve an optional-feature failure by claiming the feature is
   available without a successful native probe.

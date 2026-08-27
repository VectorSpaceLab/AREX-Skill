# Source Evidence Map

This runtime reference records the repository evidence distilled into the SimpleITK skill. It is not a request to reopen the original checkout during normal use.

## Included Evidence

| Evidence source | Why it matters | Skill use |
| --- | --- | --- |
| `pyproject.toml`, `CMakeLists.txt`, `Version.cmake`, `CMake/` | Python packaging, CMake options, version, language wrapping, elastix build option | install/build guidance and build metadata helper |
| `Wrapping/Python/SimpleITK/` | Python package shim, extra overloads, NumPy bridge, pixel type names | image-core API and NumPy guidance |
| `Code/Common/` | `Image`, transforms, `ProcessObject`, pixel IDs, spatial object implementation | image-core and registration facts |
| `Code/IO/` | image readers/writers, ImageIO utilities, series readers, viewers | IO/DICOM/transform IO guidance |
| `Code/BasicFilters/yaml/` | generated filter definitions and parameter defaults for hundreds of filters | filter patterns and representative API coverage |
| `Code/Registration/` | `ImageRegistrationMethod` metrics, optimizers, and framework implementation | registration workflows and troubleshooting |
| `Code/ElastixTransformixWrappers/` | optional elastix/transformix wrapper source | build-dependent optional feature guidance |
| `docs/source/` | public install, concepts, IO, registration, build, and setup docs | agent-facing references and troubleshooting |
| `Examples/` | runnable patterns for IO, DICOM, filters, segmentation, registration, elastix, and language wrappers | recipe distillation and safe bundled smoke scripts |
| `Wrapping/Python/tests/` and `Testing/Unit/` | behavioral edge cases for image indexing, NumPy conversion, IO, transforms, filters, and optional wrappers | verification candidates and failure-mode coverage |
| `skills/simpleitk/` | existing repo-local skill content for image core, IO, and filtering | adapted into the DisCo runtime tree after path and API corrections |

## Excluded or De-Prioritized Evidence

| Path or pattern | Reason |
| --- | --- |
| `.git/`, build directories, caches, generated binaries, virtual environments | generated or machine-local artifacts |
| `skills/tests/` | review/test artifact area, not runtime skill content |
| Release/download statistics and publishing utilities | release-heavy workflows outside selected skill scope |
| Full CI workflow orchestration | useful as maintainer context but not a runtime user workflow |
| Large ExternalData payloads and data downloads | not needed for bundled deterministic smoke scripts |
| Full multi-language wrapper internals for R/Java/Lua/Ruby/Tcl/C# | mentioned in build/wrapping triage; detailed runtime guidance focuses on Python and source-build decisions |

## Bundled Source-Artifact Replacements

| Source artifact | Runtime replacement | Owner |
| --- | --- | --- |
| `Examples/HelloWorld/HelloWorld.py` and `Examples/SimpleGaussian/SimpleGaussian.py` | `sub-skills/filtering-segmentation/scripts/filter_segmentation_smoke.py` and filtering references | `filtering-segmentation` |
| `Examples/SimpleIO/SimpleIO.py` | `sub-skills/io-and-data/scripts/io_roundtrip_smoke.py` and IO references | `io-and-data` |
| `Examples/ImageRegistrationMethod1/ImageRegistrationMethod1.py` | `sub-skills/registration-transforms/scripts/registration_smoke.py` and registration references | `registration-transforms` |
| DICOM examples | `sub-skills/io-and-data/references/dicom-series.md` | `io-and-data` |
| Elastix examples | `sub-skills/registration-transforms/references/elastix-transformix.md` | `registration-transforms` |
| CMake/SuperBuild/build docs | `sub-skills/builds-and-wrapping/references/*.md` and `scripts/check_build_metadata.py` | `builds-and-wrapping` |

## Verification Notes

The generated scripts use tiny synthetic images or read-only metadata inspection. They avoid network access, credentials, destructive writes, source checkout dependencies, and long native builds.

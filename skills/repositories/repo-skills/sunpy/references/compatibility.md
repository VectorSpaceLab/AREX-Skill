# Compatibility and capability matrix

This skill was generated from a development checkout whose package metadata
requires Python `>=3.12`. The provenance file contains the exact source commit;
check it before relying on version-sensitive behavior.

## Capability gates

| Capability | Import/API gate | Additional condition | Safe claim |
|---|---|---|---|
| Base time/coordinates/solar physics | `import sunpy`, `sunpy.time`, `sunpy.coordinates`, `sunpy.sun`, `sunpy.physics` | Astropy, NumPy, PyERFA | CPU-local workflows are available after import and tiny-object smoke |
| Map/WCS and plotting | `import sunpy.map` | `sunpy[map]`, Matplotlib; `reproject` for reprojection | Map creation and local WCS plotting; validate the target projection and dependency |
| Remote Fido clients | `import sunpy.net` and registered clients | `sunpy[net]`, network/provider availability; JSOC may need a notify email | Query construction is local; search/fetch require explicit network approval |
| TimeSeries | `import sunpy.timeseries` | `sunpy[timeseries]` and source-specific reader | Generic local DataFrame workflow; validate source parser, units, and file format |
| ASDF | `import asdf`; SunPy ASDF entry points | `sunpy[asdf]` | Local ASDF round trips when the extra and schema versions agree |
| JPEG2000 | `import glymur` plus codec probe | `sunpy[jpeg2000]` and an available native codec | Do not infer codec usability from a Glymur import alone |
| SPICE | `import spiceypy` | `sunpy[spice]` and mission kernels | Kernel-dependent geometry only after kernels are identified and loaded |
| S3 | `import fsspec` S3 support | `sunpy[s3]`, credentials, network, bucket permissions | Optional remote filesystem access; never put credentials in examples |
| OpenCV/scikit-image | import the relevant package | selected optional extra and compatible binary | Optional image operations; verify the exact operation on the target platform |

## Dependency and version troubleshooting

1. Confirm the interpreter with `python -c "import sys; print(sys.executable)"`.
2. Confirm metadata with `python -m pip show sunpy` or an equivalent package
   manager query; then import `sunpy` and print `__version__`.
3. Run `python -m pip check` before diagnosing a SunPy API error.
4. Install or remove only the extra that owns the missing import. Avoid
   combining unrelated major dependency upgrades while debugging.
5. Re-run the smallest local smoke for the affected route. Do not use a remote
   example as an installation check.

Astropy, NumPy, pandas, Matplotlib, SciPy, reproject, and native codec releases
can change numerical behavior or available methods. Preserve units and compare
semantic outputs (frame, shape, metadata, time range, and values within a
scientifically justified tolerance), not only object repr strings.

## Remote and platform limits

Provider schemas, network endpoints, certificates, proxies, rate limits,
credentials, remote file availability, and user cache state are not guaranteed
by a package import. macOS GUI backends and interactive notebook behavior need
separate checks. SunPy's selected workflows have no required accelerator
backend; CUDA availability is irrelevant unless an external dependency asks
for it.

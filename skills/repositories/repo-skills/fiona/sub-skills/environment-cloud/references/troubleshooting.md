# Environment and cloud troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `gdal-config` missing or GDAL API version error | Source build cannot discover compatible headers/libraries | Use a wheel or compatible package-manager build, set `GDAL_CONFIG`/`GDAL_VERSION` from the actual GDAL installation, and verify the version meets the package minimum. |
| Compiled extension `ImportError` or undefined symbol | Fiona was built against a different GDAL ABI than the runtime being loaded | Do not mix unrelated binary stacks. Reinstall Fiona and GDAL in one compatible environment, then import from a neutral directory and run `pip check`. |
| Driver is absent | Wheel/runtime omitted the optional GDAL driver | Inspect `supported_drivers`, choose an available format, or install a package-manager/source build that documents the needed driver. Do not claim the format is supported merely because GDAL supports it in general. |
| CRS operation cannot find database/data | `PROJ_DATA`, `PROJ_LIB`, or GDAL data is missing or mismatched | Run the bundled diagnostic, repair the package-managed data path, and verify one EPSG construction and transform. Never bake a local data path into a shared skill. |
| `boto3` import/session failure | `[s3]` extra is absent or credentials/profile are invalid | Install only `[s3]` if the task requires it; for private resources request approved credentials/profile. Use `DummySession` for offline/core work. |
| Remote URI hangs or downloads unexpectedly | Network/VSI access is implicit in the path | Stop the command, classify network and data permissions, and use a local fixture or approved bounded download. |
| `Env` settings leak into later work | GDAL options were set globally rather than scoped | Put options in `with fiona.Env(...)`; exit and re-enter the context, then rerun a clean probe. |
| Opener complains about missing methods | File-like or fsspec contract is incomplete | Implement/verify read, seek, tell, close or the required filesystem methods before passing `opener`. |

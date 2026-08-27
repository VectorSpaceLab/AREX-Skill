# Package-wide troubleshooting

## Import and install failures

- **`ModuleNotFoundError` for `sunpy.map`, `sunpy.net`, or `sunpy.timeseries`:**
  install the owning `map`, `net`, or `timeseries` extra in the interpreter that
  will run the code. Confirm with `python -m pip check` and an isolated import.
- **`ImportError` after an upgrade:** print `sunpy.__version__`, the dependent
  package versions, and `sunpy.__file__`; check for a mixed system/virtualenv
  interpreter. Recreate a private environment rather than repairing a user-owned
  environment blindly.
- **`PermissionError` during installation:** do not use `sudo`. Create or
  activate a writable virtual environment and install there.
- **Binary/native package failure:** identify the exact optional extra and
  platform. Avoid broad upgrades; use a supported wheel or a clean environment.
  A successful import does not prove JPEG2000, OpenCV, or SciPy runtime behavior.
- **Unexpected development version:** an editable checkout or development
  build is being imported. Check provenance and use a release distribution when
  a released API is required.

## Configuration and reproducibility

- Run `sunpy.print_config()` to locate the active configuration directory and
  set `SUNPY_CONFIGDIR` before import when isolating configuration.
- Use `sunpy.system_info()` and `sunpy.__version__` in a bug report. Include
  the Python executable, platform, install method, optional extras, and a small
  standalone reproducer.
- Set logging in the caller through `sunpy.log`; avoid modifying package source
  or relying on implicit global logging configuration.
- Keep sample-data/cache locations explicit. Accessing a lazy sample constant or
  calling `download_all()` may download data; never use those as an import test.

## Data and format failures

- Check the file exists, is readable, and has bytes consistent with its suffix
  before selecting a reader. A renamed file is not a converted file.
- For a 2-D solar image, inspect FITS HDUs and WCS keys before calling
  `sunpy.map.Map`. Missing `CTYPE`, units, reference pixel, observer, or time
  metadata can make a map scientifically ambiguous; repair a copied header and
  document each change.
- Install `asdf`, `jpeg2000`, or `timeseries` only when the requested format
  needs it. Validate the reader on a tiny local fixture before using a mission
  file.
- A CDF/NetCDF series can contain unfamiliar unit strings. Register a deliberate
  Astropy unit mapping or preserve the warning and resolve it before analysis;
  do not silently treat an unknown physical unit as dimensionless.
- If `TimeSeries` raises `NoMatchError` for a dict/list, use a pandas DataFrame
  with a time-like index and `GenericTimeSeries`, or pass a supported local file
  with an explicit `source=`.

## API and workflow misuse

- Use quantities for coordinates, scales, durations, wavelengths, and physical
  values. Bare numbers often create ambiguous frames or incompatible units.
- For observer-dependent transforms, provide `observer` and `obstime`; do not
  infer an observer from a missing header. For a 2-D HPC coordinate, state the
  line-of-sight/on-disk/off-limb assumption before interpreting a 3-D location.
- Keep NumPy image data in `(y, x)` order and treat `CRPIX` versus zero-indexed
  reference-pixel conventions deliberately. Validate `map.data.shape`, `map.wcs`,
  `map.coordinate_frame`, `map.scale`, and `map.observer_coordinate` after each
  operation.
- `Fido.search` and `Fido.fetch` are separate network operations. Inspect query
  results, provider errors, estimated size, credentials, destination, and retry
  results before fetching. Do not increase concurrency as a first response to a
  provider failure.
- Use `MPLBACKEND=Agg` for headless plotting, close figures, and save to a
  controlled path. `peek`, `quicklook`, and interactive examples may open a
  browser/window and are not unattended smoke tests.

## Escalation record

When a problem persists, record: exact code and input shape/file kind, package
and dependency versions, `sunpy.system_info()`, configuration changes, the
smallest failing operation, full exception type/message, and whether the issue
reproduces in a clean private environment. Separate a package defect from
provider availability, malformed data, local permissions, and missing optional
extras before reporting it.

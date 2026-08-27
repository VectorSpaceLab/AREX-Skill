# Shared troubleshooting

Read this for failures that cross the route boundaries. Keep the route-specific
troubleshooting file as the first stop for detailed API or data errors.

## Install and import

- **`ModuleNotFoundError: pycirclize`**: install the distribution into the
  Python interpreter that will execute the script, then run
  `python -c "import pycirclize; print(pycirclize.__version__)"`. Do not infer
  the import name from a failed `pip` in another environment.
- **Missing `Bio`, `numpy`, `pandas`, or Matplotlib imports**: install the base
  `pycirclize` package; these are runtime dependencies, not optional plotting
  extras.
- **Tooltip import/widget errors**: static plotting does not need `ipympl`.
  Install `pycirclize[tooltip]` only for a live Jupyter widget kernel and keep
  `tooltip=False` for batch export.

## Rendering and output

- **Blank or missing output**: register primitives before `plotfig()` or
  `savefig()`, use a supported extension, choose `Agg` in headless jobs, and
  assert that the parent directory exists and the output is non-empty.
- **Legend or custom axes disappear**: call `fig = circos.plotfig()` and add
  Matplotlib objects to `circos.ax`/`fig` before `fig.savefig(...)`. The
  convenience `Circos.savefig()` is for a completed self-contained export.
- **Repeated renders look stale**: build a fresh object for independent output
  or inspect the figure lifecycle; `savefig()` clears/closes figures when the
  package configuration enables that behavior.

## Coordinates and schemas

- **`ValueError` for degree range, sector space, or tuple range**: check
  `-360 <= start < end <= 360`, a span no larger than 360 degrees, one space per
  sector when `endspace=True` (one fewer otherwise), and strictly increasing
  tuple endpoints.
- **Coordinate/range errors in a Track or feature plot**: keep x values in the
  sector's declared coordinate range and make sequence IDs match the sector
  names. Use `ignore_range_error` only after validating the data yourself.
- **Unexpected single-column table or labels**: pass the correct delimiter and
  preserve the DataFrame index/columns. A wrong CSV/TSV delimiter can look like
  a valid but unusable parser input.

## Data sources and safety

Network-backed example/data helpers can download and cache files. Use them only
when the caller has explicitly approved network/cache behavior; otherwise use a
local path or an in-memory fixture. A missing example file is not evidence that
core plotting is broken.

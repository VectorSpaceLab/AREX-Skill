# Dashboard troubleshooting

Use the validator and the branch-specific observations before changing code.
Prefer a bounded local fixture or a small in-memory table over a remote retry.

| Symptom | Likely cause | Safe response |
|---|---|---|
| CSV cannot be opened | missing local file, wrong working directory, or a deployment filename/path mismatch | Check the explicit input path, resolve bundled resources from app root in new code, and report the path; do not silently fall back to a remote URL. |
| Required-column error | remote schema drift or wrong frequency/scale selected | Stop before normalization, print the missing names and observed header, and pin/review the source contract. |
| Metric selector is empty | all columns are metadata, or the selected source changed names | List observed columns, compare with the dictionary, and require an explicit metric mapping. |
| A selected month/week has no rows | absent period, unsorted set-derived default, or date-format mismatch | Show sorted available periods and choose a known fallback only with a warning; never fill with zero. |
| Dictionary lookup crashes | metric is new, misspelled, or dictionary has duplicates | Validate `Name`, use a safe lookup, and show the metric name without a description. |
| All metric values are null | source has no observations for the period or conversion failed | Keep valid geometries in a no-data set, inspect raw samples and percent conversion, and do not render an empty success state. |
| Map shows blank/gray regions | valid geometry has no value, or an outer merge introduced null geometry | Distinguish geometry-only from data-only rows, count each class, and exclude null geometries from PyDeck. |
| Join overlap is zero | FIPS/CBSA/postal strings were parsed as numbers, whitespace/case differs, or boundary vintage changed | Normalize before joining, preserve leading zeroes, inspect sample keys from both sides, and report unmatched keys. |
| Historical county period has null geometry | data row has no matching boundary key, or an outer merge retained a data-only row | Keep it in diagnostics/raw data, not the GeoJsonLayer; for a boundary-only county with a null metric, use the gray no-data layer. |
| ZIP boundary import fails | archive is unavailable, missing shapefile sidecars, path suffix replacement is wrong, or extraction is unsafe | Validate archive members and expected `.shp/.shx/.dbf/.prj`, extract to a temporary owned directory, cap size, clean up, and never use blind `extractall` on untrusted input. |
| GDAL/PROJ/GEOS import fails | Python and system packages are incompatible or a wheel is unavailable | Use the platform's declared system package mechanism and a supported Python environment; run a small import probe, not a full remote/native workflow. |
| `setup.sh` changes a developer machine | it writes `~/.streamlit/config.toml` and uses `$PORT` | Do not run it on a shared/persistent host. Use platform settings or explicit Streamlit flags and a platform-provided port. |
| Procfile starts with an empty port | `PORT` was not injected | Fail with a clear configuration message or use the hosting platform's standard port injection; do not write a broken user config. |
| page works locally but not in Cloud | relative TSV/dictionary path or page discovery differs from launch directory | Launch from the app root, use `Path(__file__).resolve()` in new code, and add a local fixture smoke test. |
| OS split map fails | tile URL/catalog row missing, invalid numeric text input, or provider access/reuse restriction | Validate catalog headers and coordinates, preserve attribution, and tell the user that the tile provider may be unavailable or restricted. |
| Streamlit process is slow or unstable | unbounded remote fetch, repeated archive extraction, or no caching boundary | Cache deterministic reads with an explicit invalidation strategy and keep network/archive work bounded; do not add a background downloader. |

## Remote schema drift

The housing link groups are remote and can change headers, types, periods,
metric names, or geography vintages without changing the dashboard code. Before
processing a new response:

1. capture the response header and a small sample locally;
2. validate required columns and a known period with the bundled helper;
3. inspect identifier string preservation and percent-like values;
4. compare normalized key overlap against the selected boundary;
5. stop and surface the diff when a strict assumption fails.

Do not “fix” a schema mismatch by dropping unknown columns or guessing a join
key. A new metric can be displayed only after its label/description and numeric
semantics are reviewed.

## Clean deployment checklist

- Install Python dependencies and OS dependencies through the deployment
  platform's supported, declarative channels.
- Avoid the repository `setup.sh` on shared hosts because it mutates the user
  Streamlit configuration directory. If the Procfile is retained, replace the
  mutation with platform configuration or an explicit command that uses the
  injected port.
- Ensure the launch directory contains the app entry point and that page and
  fixture filenames preserve case, spaces, emoji, and underscores exactly.
- Resolve bundled catalogs from the app root and treat remote data/tiles as
  optional failures with readable UI messages.
- Use an owned temporary directory for archive extraction and an explicit
  writable output directory for generated artifacts; never write into an
  installed package directory by default.
- Smoke-test `Home.py` import/page discovery, the local TSV and data-dictionary
  parsers, one synthetic join, and the validator. Avoid a full remote download,
  credentialed service, or large boundary extraction as a deployment probe.

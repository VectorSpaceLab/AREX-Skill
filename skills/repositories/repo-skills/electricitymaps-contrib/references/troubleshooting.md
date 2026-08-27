# Repo-Level Troubleshooting

## When to read

Read this for install/import/CLI failures that cut across parser, capacity, and
configuration workflows. For workflow-specific failures, use the nearest
sub-skill troubleshooting file.

## Symptoms and recoveries

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'electricitymap.contrib.types'` | The `libs/types` workspace package is not installed or importable. | Prefer `uv sync --extra parsers --group dev`. With pip, install `libs/types` editable before the root package. |
| `ModuleNotFoundError: No module named 'parsers'` while calling `CONFIG_MODEL...parsers.get_function(...)` | The config model lazily imports live parser functions through top-level `parsers.*`; plain package installs may not expose the checkout's `electricitymap/contrib` source root. | Run repo commands through uv from the checkout, or run `python scripts/check_environment.py --repo-root <checkout>` / sub-skill helpers with `--repo-root`. For ad hoc shell work, add `<checkout>/electricitymap/contrib` to `PYTHONPATH`. |
| `No module named bs4`, `lxml`, `pandas`, `openpyxl`, `xlrd`, `odf`, `cv2`, `pytesseract`, `pydataxm`, or `demjson3` | Parser optional dependencies are missing. | Install with `uv sync --extra parsers --group dev` or pip-install `.[parsers]`. Do not treat a base-package import as enough for parser work. |
| `pytest`, `requests_mock`, `syrupy`, `testfixtures`, `click`, or `ruff` missing | Dev dependency group not installed. | Add `--group dev` with uv or install the explicit dev packages in [installation and checks](installation-and-checks.md). |
| `test-parser` or `capacity_update` command not found | The project is not installed in the active environment or uv is not being used from the checkout. | Use `uv run test-parser --help` / `uv run capacity_update --help`, or install the package editable in the environment. |
| `npx` or `prettier` error after `capacity_update` | Capacity CLI finished Python-side work and then tried to format `config/zones` with `npx --yes prettier@2`. Node/npm, network, or cache may be unavailable. | Inspect the config diff first. If the content is correct, install/use Node/npm and run the prettier command, or format through project tooling once available. |
| API token error from `get_token(...)` | A live parser or capacity parser requires credentials. | Set only the needed variable, such as `ENTSOE_TOKEN`, `EIA_KEY`, `ESIOS_TOKEN`, `OPENELECTRICITY_TOKEN`, `EMBER_CAPACITY_KEY`, `FINGRID_TOKEN`, `RESEAUX_ENERGIES_TOKEN`, `EMAPS_NORDPOOL_USERNAME`/`EMAPS_NORDPOOL_PASSWORD`, `ERCOT_API_*`, `NED_TOKEN`, `JAO_AUCTION_API_KEY`, `MAILGUN_TOKEN`, `TR_USERNAME`/`TR_PASSWORD`, or Webshare proxy credentials. Use mocked tests when credentials are absent. |
| Live parser returns HTTP 403/429/timeouts | Upstream source blocks traffic, rate-limits, changes API, or needs a proxy/token. | Reproduce with the smallest parser smoke command and a `target_datetime`; then check parser-specific token/proxy code and existing mocked tests. Do not hide network failures as parser output failures. |
| Full pytest suite is slow or noisy | The repo contains many parser fixtures and snapshot tests. | Use the focused commands in [installation and checks](installation-and-checks.md) and the relevant sub-skill's native candidate notes before broadening scope. |
| YAML/JSON diff is unexpectedly large | Capacity/config scripts can rewrite ordering/formatting or bulk-update many files. | Stop before committing. Compare the intended zone/source scope, use dry-run/helper modes where available, and avoid all-zone capacity/name updates unless explicitly requested. |

## General debugging sequence

1. Run the root environment check with `--repo-root`.
2. Use the relevant sub-skill helper in list/describe/dry-run mode.
3. If live execution is necessary, confirm the exact zone/source, target date,
   token variables, and expected file mutations before running it.
4. Run the focused native tests for the changed workflow.
5. Only then broaden to `uv run check` or the full test suite.

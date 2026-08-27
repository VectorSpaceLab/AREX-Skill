# Parser Troubleshooting

## Import and registry failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No module named 'parsers'` from `get_function()` | Lazy config-model imports expect the checkout's `electricitymap/contrib` source root. | Use `scripts/test_parser.py --repo-root <checkout>` or root `scripts/check_environment.py --repo-root <checkout>`. In an ad hoc shell, add `<checkout>/electricitymap/contrib` to `PYTHONPATH`. |
| Parser exists but `--describe ZONE TYPE` says no parser registered | The zone/exchange YAML lacks the matching `parsers:` field, the data type is wrong, or an exchange key direction/name differs. | Inspect the zone/exchange config and `ParserDataType` value. For exchange tasks use the `A->B` key and exchange-side data type. |
| `Invalid parser key: ...` during registry import | Config YAML uses a parser key not present in `ParserDataType` or the parser model. | Correct the YAML key or update types/model/tests together; run `tests/config/test_config_model.py` and `tests/test_parser_interface.py`. |
| `ImportError` for `bs4`, `lxml`, `pandas`, `openpyxl`, `pytesseract`, `cv2`, etc. | Parser extra dependencies are missing. | Install `uv sync --extra parsers --group dev`; for pip use `.[parsers]` plus explicit dev deps. |

## Execution and output failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Error: parser returned nothing` | The parser returned `None`, `[]`, `False`, or source data did not match expected payload. | Reproduce with a target date, inspect the raw mocked/live response, and either raise a clear source exception or return a truthy event list. |
| `Parser output lacks datetime key` | Returned event dicts do not match the expected model. | Use event-list helpers and verify every event has `datetime`. Add a test asserting the exact output. |
| `Datetimes must be timezone aware` | Parser returned naive datetime objects. | Convert source-local time to a timezone-aware `datetime`, often with `zoneinfo.ZoneInfo(...)`, then normalize or preserve as appropriate. |
| Historical target returns latest data | Parser ignored `target_datetime`. | If historical data is unsupported, raise a clear exception for target dates. If supported, translate target date to source timezone and source query parameters. |
| Consumption/exchange validation warning | Output violates quality checks such as exchange direction or consumption shape. | Inspect `validate_consumption` or `validate_exchange` expectations and compare sign conventions/source keys. |
| Snapshot test fails after source parser change | Intended output changed or parser emitted nondeterministic fields. | Review fixture and event fields. Update snapshots only when source behavior and event schema changes are intentional. |

## Token, proxy, and live-source issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Missing `ENTSOE_TOKEN`, `EIA_KEY`, `ESIOS_TOKEN`, `OPENELECTRICITY_TOKEN`, or similar | Live source requires an API key. | Use mocked tests when possible. For live smoke, set only the needed env var and do not commit secrets. |
| Nordpool auth error | `EMAPS_NORDPOOL_USERNAME`/`EMAPS_NORDPOOL_PASSWORD` missing or token expired. | Re-run with credentials or keep work to mocked tests. |
| ERCOT/NED/JAO/Mailgun/TR-specific credential error | Source-specific token/user/pass missing. | Read the parser's token names from the error or API reference and set a fake value only in tests. |
| Source blocks traffic or returns 403/429 | Rate limiting, geo blocking, source outage, or proxy requirement. | Check parser decorators such as `use_proxy`; only use Webshare credentials when explicitly approved. Add a fixture-based regression test for parsing logic. |
| OCR/image parser fails despite Python deps | `pytesseract` package is installed but system Tesseract binary/data may be absent. | Avoid making OCR paths required for generic verification. If the task is OCR-specific, verify the system binary and traineddata separately. |

## Choosing the next check

- Signature or mapping changed: run `tests/test_parser_interface.py`.
- One parser changed: run that parser's focused test module.
- Config parser mapping changed: also run `tests/config/test_config_model.py`.
- Live source behavior changed: create/update a mock fixture and test before
  relying on live `test-parser` output.

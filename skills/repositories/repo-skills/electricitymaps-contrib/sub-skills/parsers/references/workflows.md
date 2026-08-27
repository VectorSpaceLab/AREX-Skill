# Parser Workflows

## When to read

Read this for concrete steps to add, wire, test, or debug live parser functions.

## Add or update a zone-side parser

1. **Choose the parser type and source.** Production parsers are the primary
   source of generation data; other supported zone-side types include
   consumption, price, generation/consumption forecasts, production-per-mode
   forecasts, LMP, grid alerts, and intraday contract statistics.
2. **Inspect the existing registry.**

   ```bash
   python sub-skills/parsers/scripts/test_parser.py --repo-root <checkout> --describe FR production
   python sub-skills/parsers/scripts/test_parser.py --repo-root <checkout> --list --data-type production
   ```

3. **Implement the function with the expected arguments.** Use a reusable
   `requests.Session`, support `target_datetime` when the source offers
   historical data, and raise a clear exception for unsupported historical
   ranges.
4. **Return event-list output.** Prefer `ProductionBreakdownList`,
   `TotalConsumptionList`, `PriceList`, and related event-list helpers, then
   return `.to_list()` when the current parser convention expects plain dicts.
5. **Wire the config mapping.** Add or update the `parsers:` entry in the zone
   YAML using the `MODULE.fetch_function` form. Keep broad config validation in
   the configuration sub-skill.
6. **Add tests and fixtures.** Mock HTTP through `requests-mock` or a mounted
   adapter. Tests should set fake token environment variables rather than
   requiring real credentials.
7. **Run focused checks.**

   ```bash
   uv run pytest electricitymap/contrib/parsers/tests/test_<PARSER>.py -q
   uv run pytest tests/test_parser_interface.py -q
   ```

8. **Smoke live only when appropriate.** Live smoke calls can hit public APIs
   and need tokens/network. Use a target date when debugging historical paths.

   ```bash
   python sub-skills/parsers/scripts/test_parser.py --repo-root <checkout> --execute FR production
   python sub-skills/parsers/scripts/test_parser.py --repo-root <checkout> --execute GE production \
     --target-datetime "2022-04-10T15:00:00+00:00"
   ```

## Add or update an exchange parser

- Use an exchange key containing `->`, for example `NO-NO3->SE`.
- The function takes `zone_key1, zone_key2, session, target_datetime, logger`.
- Exchange config files use sorted uppercase zone-key filenames with `_` as the
  filename separator; route filename validation to the configuration sub-skill.
- Use `ExchangeList` or the appropriate forecast/transfer-capacity list helper.
- Smoke with the exchange data type explicitly:

  ```bash
  python sub-skills/parsers/scripts/test_parser.py --repo-root <checkout> \
    --describe "NO-NO3->SE" exchange
  uv run test-parser "NO-NO3->SE" exchange
  ```

## Debug a failing parser

1. Reproduce with `--describe` first. This separates registry/import problems
   from live parser/network problems.
2. If describe succeeds, run the parser against a mocked native test before
   live execution. Search the parser tests for the parser module and source
   fixture pattern.
3. If live execution fails, classify the failure:
   - Missing token or credentials: see parser troubleshooting.
   - HTTP/network/source change: inspect request URL/parameters and source
     response; keep the failure distinct from output validation.
   - Output validation: compare event dicts to the API reference requirements.
   - Date/time: verify target date parsing, source timezone conversion, and
     timezone-aware returned datetimes.
4. Keep the diff small and add a focused regression test with a fixture that
   captures the source behavior.

## Native verification candidates

These native tests are good final verification candidates after a parser-related
skill or code change is integrated:

| Candidate | Why it matters | Safety |
| --- | --- | --- |
| `tests/test_parser_interface.py` | Loads parser functions from config and verifies expected argument names/return annotations. | CPU, safe-runnable, requires parser extras/dev deps. |
| `electricitymap/contrib/parsers/tests/test_ENTSOE.py` | Exercises token env, XML mocks, production/consumption/price/exchange/forecast behavior, aggregation, and snapshots. | CPU, mocked HTTP, moderate runtime. |
| `electricitymap/contrib/parsers/tests/test_FR.py` | Exercises token handling and a country parser with mocked JSON/HTTP. | CPU, mocked HTTP. |
| `electricitymap/contrib/parsers/tests/test_EIA.py`, `test_ESIOS.py`, `test_OPENNEM.py`, `test_US_ERCOT.py` | Cover API-key paths, tabular/JSON formats, source-specific edge cases, and mocked live flows. | CPU, mocked HTTP; set fake env vars in tests. |

Do not use live parser execution as the only verification signal when a mocked
native test can anchor the behavior.

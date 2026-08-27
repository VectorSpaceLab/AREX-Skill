---
name: parsers
description: "Use when adding, debugging, inspecting, or smoke-testing
  Electricity Maps live parsers and parser registry mappings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Parsers

Use this sub-skill for live Electricity Maps parser work: production,
consumption, price, exchange, forecast, grid-alert, locational marginal price,
and intraday-statistics parser functions.

Do not use this route for installed capacity updates or `productionCapacity`
execution; those belong to [capacity](../capacity/SKILL.md). Use
[configuration](../configuration/SKILL.md) for broad zone/exchange YAML model
validation beyond parser mapping fields.

## First decisions

1. Identify whether the task is zone-side or exchange-side. Exchange-side data
   types use two zone keys and exchange identifiers such as `NO-NO3->SE`.
2. Identify the parser data type. If the user omits it, production is the usual
   default for a zone and exchange is the usual default for an exchange key.
3. Check whether a config mapping already exists before editing parser code:

   ```bash
   python scripts/test_parser.py --repo-root <checkout> --describe FR production
   python scripts/test_parser.py --repo-root <checkout> --list
   ```

4. Only use live execution after confirming network/API-token expectations:

   ```bash
   python scripts/test_parser.py --repo-root <checkout> --execute FR production \
     --target-datetime "2024-01-01T00:00:00+00:00"
   ```

## Read these references

- [api-reference.md](references/api-reference.md) for parser signatures,
  `ParserDataType` groups, registry mappings, output model expectations, mode
  enums, and decorator/token helpers.
- [workflows.md](references/workflows.md) for adding a parser, debugging an
  existing parser, wiring config, writing mocks/tests, and selecting focused
  native checks.
- [troubleshooting.md](references/troubleshooting.md) for parser-specific
  import, token, date/time, output-shape, validation, and source/network
  failures.
- `scripts/test_parser.py` is an adapted safe wrapper for registry inspection
  and optional live parser execution. Run `--help` first when unsure.

## Parser workflow checklist

- Use source/config evidence before writing code: parser file, config mapping,
  existing tests/mocks, and the parser interface contract.
- New zone parser functions should follow the zone-side signature:
  `zone_key, session, target_datetime, logger`.
- New exchange functions should follow the exchange-side signature:
  `zone_key1, zone_key2, session, target_datetime, logger`.
- Return a truthy dict or list of dicts with timezone-aware native
  `datetime.datetime` values. Missing production modes should be omitted or
  `None`, not silently set to zero unless the source explicitly reports zero.
- Use `ProductionBreakdownList`, `TotalConsumptionList`, `ExchangeList`,
  `PriceList`, and related event-list helpers when possible so output fields
  stay consistent.
- Add or update a focused pytest file with mocked HTTP/file fixtures; do not
  make native verification depend on live API availability.
- Run `tests/test_parser_interface.py` after changing signatures, config
  parser mappings, `ParserDataType`, or parser registry behavior.

## Validation shortcuts

```bash
uv run pytest tests/test_parser_interface.py -q
uv run pytest electricitymap/contrib/parsers/tests/test_<PARSER>.py -q
uv run test-parser FR production
uv run test-parser "NO-NO3->SE" exchange
```

If the command fails before reaching parser code, first run the root
`scripts/check_environment.py --repo-root <checkout>` diagnostic and then read
[repo troubleshooting](../../references/troubleshooting.md).

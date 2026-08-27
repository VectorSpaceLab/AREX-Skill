---
name: configuration
description: "Use when maintaining Electricity Maps zone, exchange, data-center,
  emission-factor, geo, and config-model validation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Configuration

Use this sub-skill for static repository configuration: `config/zones`,
`config/exchanges`, `config/defaults.yaml`, data-center JSON, co2eq/emission
factor metadata, geography consistency, and filename/model validation.

Use [parsers](../parsers/SKILL.md) for live parser code and parser output
contracts. Use [capacity](../capacity/SKILL.md) when the task specifically
updates installed capacity values or capacity parsers.

## First decisions

1. Identify the config surface: zone YAML, exchange YAML, data centers,
   co2eq/emission factors, aggregate zone creation, or geometry consistency.
2. Run safe validators before and after edits:

   ```bash
   python scripts/validate_config_filenames.py --repo-root <checkout>
   uv run pytest tests/config/test_config_model.py tests/test_zones_json.py tests/test_exchanges_json.py -q
   ```

3. Use the aggregate helper in dry-run mode before writing a parent zone file:

   ```bash
   python scripts/create_aggregated_zone_config.py --repo-root <checkout> US America/New_York
   ```

4. If a task also changes parser mappings or capacity values, route to the
   owning sub-skill and then return here for model/filename/geo validation.

## Read these references

- [config-models.md](references/config-models.md) for zone/exchange/data-center
  model fields, parser mapping locations, co2eq source rules, and geometry
  consistency.
- [workflows.md](references/workflows.md) for editing zone/exchange configs,
  creating aggregate zones, handling dangerous maintainer scripts, and choosing
  focused tests.
- [troubleshooting.md](references/troubleshooting.md) for pydantic validation,
  filename ordering, subzone/geo mismatch, data-center, and emission-factor
  failures.
- `scripts/validate_config_filenames.py` checks uppercase zone filenames and
  uppercase/sorted exchange filenames.
- `scripts/create_aggregated_zone_config.py` previews aggregate zone YAML from
  subzones and requires `--write` before mutating files.

## Configuration checklist

- Zone filenames must be uppercase. Exchange filenames must be uppercase and
  sorted by zone key using `_` as the filename separator.
- Exchange config keys load as `A->B` even though filenames use `A_B.yaml`.
- Parser mapping fields must use `ParserDataType` names and `MODULE.function`
  strings; live parser mapping behavior is validated through the parser route.
- `subZoneNames` must point to existing zone config files and should align with
  geography and exchange-neighbor expectations.
- Data-center JSON is validated by pydantic models; do not add duplicate or
  malformed data-center entries by hand.
- Emission factor sources referenced in co2eq defaults/overrides must either be
  known global references or appear in the corresponding zone's `sources` map.
- Bulk zone removal/name-update scripts are destructive and not safe defaults;
  plan them explicitly with diffs and focused tests.

## Focused checks

```bash
uv run pytest tests/config/test_config_model.py tests/config/test_config_zones.py -q
uv run pytest tests/test_zones_json.py tests/test_exchanges_json.py -q
uv run pytest tests/config/test_data_center_model.py tests/config/test_emission_factors.py \
  tests/test_co2eq_parameters.py -q
```

For parser mapping edits also run `tests/test_parser_interface.py`; for capacity
edits also run the capacity tests named by the capacity sub-skill.

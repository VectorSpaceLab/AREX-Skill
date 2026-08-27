# Configuration Workflows

## When to read

Read this for static zone/exchange/data-center/co2eq edits, aggregate zone
creation, safe use of maintainer utilities, and focused validation.

## Edit a zone config

1. Identify the ownership of the field:
   - `parsers:` mapping for live data usually needs the parser sub-skill.
   - `capacity:` values usually need the capacity sub-skill.
   - Static metadata, hierarchy, sources, timezone, names, currency, and geo
     consistency stay here.
2. Keep the YAML key uppercase and equal to the filename stem.
3. If adding `subZoneNames`, ensure every subzone has a zone config and check
   neighbor/geometry consistency.
4. If adding source labels for emission factors or capacity, ensure the `sources`
   map contains referenced non-global source names.
5. Run model and zone/geo tests.

```bash
python sub-skills/configuration/scripts/validate_config_filenames.py --repo-root <checkout>
uv run pytest tests/config/test_config_model.py tests/test_zones_json.py -q
```

## Edit an exchange config

1. Name the file with sorted uppercase zone keys joined by `_`, for example
   `DK-DK1_SE-SE4.yaml`.
2. Remember that loaded exchange keys use `->`, such as `DK-DK1->SE-SE4`.
3. Parser mappings must use exchange-side parser data-type fields.
4. Run filename and exchange consistency checks.

```bash
python sub-skills/configuration/scripts/validate_config_filenames.py --repo-root <checkout>
uv run pytest tests/test_exchanges_json.py tests/config/test_config_model.py -q
```

## Create an aggregate zone config

Use the bundled helper in dry-run mode first. It previews a parent zone YAML by
collecting subzone files whose stems start with `<PARENT>-`, summing current
capacity values for a target date, and aggregating contributors.

```bash
python sub-skills/configuration/scripts/create_aggregated_zone_config.py \
  --repo-root <checkout> US America/New_York
```

To write the file after reviewing output:

```bash
python sub-skills/configuration/scripts/create_aggregated_zone_config.py \
  --repo-root <checkout> US America/New_York --target-datetime 2025-01-01 --write
```

Cautions:

- The helper writes a generated YAML view and does not preserve comments.
- For timeline-preserving parent-zone capacity updates, use the capacity
  sub-skill's aggregate update workflow instead.
- If subzones mix capacity value shapes or have missing data for a date, stop
  and normalize before writing.

## Data centers and emission factors

Data-center edits should be validated with:

```bash
uv run pytest tests/config/test_data_center_model.py -q
```

Co2eq/emission-factor edits should be validated with:

```bash
uv run pytest tests/config/test_emission_factors.py tests/test_co2eq_parameters.py -q
```

When a test complains about a missing source, either add the source to the
zone's `sources` map or confirm that it belongs to the global source allowlist
used by the model tests.

## Dangerous maintainer utilities

The source repo has useful but destructive scripts. They are not bundled as
safe default execution helpers:

| Utility behavior | Safe handling |
| --- | --- |
| Remove a zone, delete exchange files, and move parser files to archived | Ask for explicit approval, dry-run with grep/listing first, and run config/parser tests after every deletion. |
| Add country/zone names from a JSON source to many YAML files | Review generated diff carefully; use only when the user asks for bulk name synchronization. |
| Bulk capacity updates from all EMBER years | Use capacity sub-skill; narrow to one zone or documented batch before mutation. |
| Legacy ENTSO-E CSV/API capacity script | Prefer generic capacity parser workflow unless the user explicitly needs CSV import. |

## Focused validation matrix

| Change | Minimum checks |
| --- | --- |
| Zone YAML metadata/hierarchy | filename validator, `tests/config/test_config_model.py`, `tests/test_zones_json.py` |
| Exchange YAML | filename validator, `tests/test_exchanges_json.py`, config model test |
| Parser mapping in YAML | parser interface test plus config model test |
| Capacity values in YAML | capacity tests plus config model test |
| Data centers | data-center model test |
| Emission factors/co2eq | emission-factor and co2eq tests |
| Broad config reformat | focused tests above, then `uv run check` if the user wants full confidence |

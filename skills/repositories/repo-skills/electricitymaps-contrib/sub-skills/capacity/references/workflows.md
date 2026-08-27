# Capacity Workflows

## When to read

Read this for installed-capacity updates, capacity parser development, source
group updates, and review/validation steps.

## Update one zone

1. Inspect registry support.

   ```bash
   python sub-skills/capacity/scripts/capacity_update.py --repo-root <checkout> \
     --zone DK-DK1 --target-datetime 2023-01-01
   ```

2. Confirm the capacity source, token/network availability, and whether the
   parent aggregate zone should be updated.
3. Execute with an explicit gate:

   ```bash
   python sub-skills/capacity/scripts/capacity_update.py --repo-root <checkout> \
     --zone DK-DK1 --target-datetime 2023-01-01 --update-aggregate --execute
   ```

4. Inspect the YAML diff in `config/zones`. Check for unrealistic trend breaks,
   missing sources, zero values that should be omitted, and unexpected mode
   additions/removals.
5. Format only after the diff is understood. The project CLI runs `npx --yes
   prettier@2 --write config/zones --cache`; the bundled wrapper skips that by
   default unless `--run-prettier` is supplied.
6. Run focused tests:

   ```bash
   uv run pytest tests/test_capacity.py tests/test_update_capacity_configuration.py -q
   ```

## Update a source group

Source groups update every zone configured for a given `productionCapacity`
parser source. Registry examples include EIA, EMBER, ENTSOE, IRENA, ONS,
OPENNEM, and REE.

```bash
python sub-skills/capacity/scripts/capacity_update.py --repo-root <checkout> --list-sources
python sub-skills/capacity/scripts/capacity_update.py --repo-root <checkout> \
  --source ENTSOE --target-datetime 2023-01-01 --execute
```

Use source-group updates cautiously. The repository docs recommend smaller PRs
by zone or source subset because capacity data has inconsistent reporting
standards and reviewers need to inspect trend breaks.

## Add or repair a capacity parser

A capacity parser should expose:

```python
def fetch_production_capacity(zone_key, target_datetime, session) -> dict[str, Any] | None:
    ...
```

Some source modules also expose a group function:

```python
def fetch_production_capacity_for_all_zones(target_datetime, session) -> dict[str, dict]:
    ...
```

Implementation checklist:

1. Verify the source is authoritative and stable enough for ongoing updates.
2. Map source technology labels to repo capacity modes from
   [data-formats.md](data-formats.md).
3. Return per-mode dicts with `datetime`, `source`, and `value` fields; omit or
   zero-filter unavailable modes according to existing update helper behavior.
4. Add a `productionCapacity: SOURCE.fetch_production_capacity` mapping to the
   relevant zone config.
5. Add a mocked test under the capacity parser tests for source-specific
   parsing and token behavior.
6. Run capacity parser and config helper tests.

## Legacy and bulk scripts

The source repo contains additional maintainer scripts. They are intentionally
not the default runtime helpers in this generated skill:

| Source behavior | Why not default |
| --- | --- |
| EMBER all-years update | It can replace entire `capacity` sections and make many API calls. Use only when explicitly requested and after narrowing zone scope. |
| Legacy ENTSO-E CSV/API capacity script | It has separate `xmltodict` dependency, older formatting assumptions, token/network side effects, and overlaps with the generic capacity parser workflow. |
| Bulk zone-name or zone-removal scripts | They mutate many files or delete configs/exchanges; route to configuration troubleshooting and require explicit user approval. |

## Native verification candidates

| Candidate | Why it matters | Safety |
| --- | --- | --- |
| `tests/test_capacity.py` | Validates scalar/dict/list capacity lookup by date and source. | CPU, safe-runnable. |
| `tests/test_update_capacity_configuration.py` | Validates merge, deduplication, and aggregate update helper behavior. | CPU, safe-runnable. |
| `electricitymap/contrib/capacity_parsers/tests/test_ONS.py` | Tests date filtering on tabular capacity data. | CPU, safe-runnable with pandas. |
| `electricitymap/contrib/capacity_parsers/tests/test_OPENELECTRICITY.py` | Tests token env, mocked HTTP, and capacity parsing. | CPU, mocked HTTP. |

Do not treat a successful live API call as sufficient if these helper semantics
or timeline rules are untested.

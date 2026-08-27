---
name: capacity
description: "Use when updating installed capacity data, adding capacity
  parsers, or diagnosing Electricity Maps capacity configuration timelines."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Capacity

Use this sub-skill for installed-capacity workflows: capacity parsers,
`capacity_update`, zone capacity config timelines, capacity source groups, and
aggregate parent-zone capacity updates.

Do not use this route for live production/consumption/price/exchange parser
smoke tests; use [parsers](../parsers/SKILL.md). Use
[configuration](../configuration/SKILL.md) for zone/exchange config validation
that is not specifically about installed capacity.

## First decisions

1. Decide whether the user wants a **single zone** update, a **source group**
   update, or a **capacity parser implementation**.
2. Inspect available capacity parser ownership before mutating files:

   ```bash
   python scripts/capacity_update.py --repo-root <checkout> --list-sources
   python scripts/capacity_update.py --repo-root <checkout> --zone DK-DK1 \
     --target-datetime 2023-01-01
   ```

3. Execute only after confirming network/API-token requirements and expected
   YAML mutations:

   ```bash
   python scripts/capacity_update.py --repo-root <checkout> --zone DK-DK1 \
     --target-datetime 2023-01-01 --update-aggregate --execute
   ```

4. Review the config diff and run focused native tests before formatting or
   broadening to full-suite checks.

## Read these references

- [workflows.md](references/workflows.md) for update commands, source groups,
  adding capacity parsers, review expectations, and selected tests.
- [data-formats.md](references/data-formats.md) for scalar/dict/list capacity
  semantics, mode names, date/source/value fields, and aggregate rules.
- [troubleshooting.md](references/troubleshooting.md) for no-parser errors,
  token/network issues, aggregate failures, prettier errors, and bulk update
  hazards.
- `scripts/capacity_update.py` is a safe wrapper/command generator. It lists
  registry mappings by default and requires `--execute` before live mutation.

## Capacity workflow checklist

- Prefer small updates: the repository docs discourage updating all capacities
  at once because review becomes risky.
- `--zone` and `--source` are mutually exclusive. `--source` groups all zones
  configured for one capacity parser source such as EIA, EMBER, ENTSOE, IRENA,
  ONS, OPENNEM, or REE.
- `target_datetime` is required. Use an ISO date such as `2023-01-01` unless a
  source requires more precision.
- `--update-aggregate` updates the parent zone when subzone capacity changes;
  it can fail if subzones do not share compatible capacity list structures.
- Live source updates can require tokens such as `ENTSOE_TOKEN`, `EIA_KEY`,
  `EMBER_CAPACITY_KEY`, `OPENELECTRICITY_TOKEN`, or `FINGRID_TOKEN`.
- After mutation, inspect `config/zones` diffs for trend breaks and source
  consistency before running prettier/formatting.

## Focused checks

```bash
uv run pytest tests/test_capacity.py tests/test_update_capacity_configuration.py -q
uv run pytest electricitymap/contrib/capacity_parsers/tests/test_ONS.py \
  electricitymap/contrib/capacity_parsers/tests/test_OPENELECTRICITY.py -q
```

If a capacity update also changes parser mappings or broader zone YAML fields,
run the configuration sub-skill's model/filename checks as well.

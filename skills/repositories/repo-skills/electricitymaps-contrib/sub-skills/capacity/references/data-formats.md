# Capacity Data Formats

## When to read

Read this before editing `capacity:` YAML blocks, implementing capacity parsers,
or diagnosing aggregate capacity failures.

## Capacity modes

Capacity modes combine production modes and storage modes:

- Production: `biomass`, `coal`, `gas`, `geothermal`, `hydro`, `nuclear`,
  `oil`, `solar`, `wind`, `unknown`.
- Storage capacity keys: `battery storage`, `hydro storage`.

The config model aliases Python field names such as `battery_storage` and
`hydro_storage` to YAML keys with spaces.

## Accepted value shapes

The repository still supports several generations of capacity config shapes.
When writing new data, prefer the list-of-dated-points form.

### Legacy scalar

```yaml
capacity:
  wind: 5233
```

Scalar values are old-style installed MW values with no source/date. Helpers can
read them, but new updates usually convert or replace them.

### Single dated dict

```yaml
capacity:
  wind:
    datetime: "2023-01-01"
    source: "ENTSOE"
    value: 5233
```

This is supported for reading but is being superseded by lists.

### Timeline list

```yaml
capacity:
  wind:
    - datetime: "2022-01-01"
      source: "ENTSOE"
      value: 5100
    - datetime: "2023-01-01"
      source: "ENTSOE"
      value: 5233
```

`get_capacity_data(capacity_config, dt)` returns the most recent value whose
`datetime` is at or before `dt`, or the earliest value when `dt` predates all
entries. `get_capacity_data_with_source(...)` preserves source labels.

## Update helper semantics

`generate_zone_capacity_config(existing, data)` applies these rules:

- Existing scalar modes become a one-item list when updated with positive data.
- Existing list modes append the new point only when it changes the timeline.
- If the new point has the same `datetime` as an existing point, that date is
  updated; if it duplicates the previous value, the redundant point can be
  removed.
- If the new point has the same value as the next later point and is earlier in
  time, the later redundant point can be removed.
- New modes are added only when the incoming value is positive.
- Invalid mixed types raise or block aggregate updates rather than guessing.

These rules are covered by native tests in `tests/test_update_capacity_configuration.py`.

## Aggregate parent-zone rules

Aggregate updates sum subzone capacity values into the parent zone. The generic
update helper expects every selected subzone to provide compatible list-shaped
capacity entries for each mode.

Common aggregate blockers:

- Parent zone is missing from zone config.
- Subzones use mixed scalar/list/dict shapes for the same mode.
- Not all subzones have capacity entries for the same datetime.
- A subzone capacity value is `None` or omitted and the aggregate cannot be
  computed truthfully.

When an aggregate update fails, do not patch the parent value by guesswork.
First normalize subzone capacity shapes or choose a target date and document why
that date is valid.

## Source labels and review

Each new capacity point should carry a source string. The capacity README names
major sources including EIA, EMBER, ENTSO-E, IRENA, ONS, OPENNEM, and REE. When
a value changes sharply from the previous point, include the source and reason
in the PR/task summary so reviewers can validate the trend.

Do not update all capacity data at once unless the user explicitly requests a
bulk refresh and accepts the review risk.

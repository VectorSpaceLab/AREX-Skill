---
name: data-and-configuration
description: "Validate and explain NuPIC legacy CSV streams, FileRecordStream
  metadata, model parameter files, aggregation blocks, and configuration
  overrides."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data and Configuration

Use this sub-skill when the request is about NuPIC legacy input data, `FileRecordStream`, CSV field metadata, model parameter YAML/JSON, aggregation settings, or configuration property overrides. This skill prepares and validates configuration artifacts; it does not run OPF models, Network API graphs, or swarms.

## Start here

- Read [references/data-formats.md](references/data-formats.md) when a user asks why a NuPIC CSV fails, what the three header rows mean, how `FileRecordStream` interprets fields, or what timestamp/type/flag values are accepted.
- Read [references/model-params-and-config.md](references/model-params-and-config.md) when building or reviewing model params for a predicted field, mapping encoders to CSV columns, adding aggregation, or applying `NTA_CONF_PROP_*` overrides.
- Read [references/troubleshooting.md](references/troubleshooting.md) when diagnosing missing header rows, invalid field types or flags, timestamp parse errors, row width mismatches, encoder/field mismatches, swarm `file://` source issues, or config override surprises.
- Run [scripts/validate_nupic_csv.py](scripts/validate_nupic_csv.py) for a deterministic, stdlib-first CSV check that does not import `nupic`; it validates headers, field types, special flags, row widths, timestamp/value parsing, and optional predicted-field/model-param consistency.

## Common request routing

| User intent | Use this sub-skill for | Route elsewhere for |
|---|---|---|
| "Validate this input file" or "why does OPF reject my CSV?" | Three-row CSV header, field types, flags, timestamp formats, row widths, `FileRecordStream` expectations. | Python 2.7/package import failures: [root troubleshooting](../../references/troubleshooting.md). |
| "Build model params for a predicted field" | `model`, `version`, `aggregationInfo`, `modelParams.sensorParams.encoders`, `spParams`, `tmParams`, `clParams`, predicted-field checks. | Actually creating/running `ModelFactory` and reading inference outputs: [../opf-prediction/](../opf-prediction/). |
| "Use this CSV in a Network API sensor" | CSV metadata and `FileRecordStream` shape. | Region/link construction with `RecordSensor` or `FileRecordStream`: [../network-api/](../network-api/). |
| "Make or lint a swarm search definition" | CSV fields and shared model-param concepts; ensure stream sources use `file://`. | Search definition JSON, hypersearch actions, generated experiments: [../swarming/](../swarming/). |

## Minimal validation command

```bash
python sub-skills/data-and-configuration/scripts/validate_nupic_csv.py data.csv \
  --predicted-field consumption
```

With a model params file:

```bash
python sub-skills/data-and-configuration/scripts/validate_nupic_csv.py data.csv \
  --model-params model_params.json \
  --predicted-field consumption
```

If the params file is YAML, the script attempts to import `yaml` only for that file. If PyYAML is missing, use a JSON export or install PyYAML in the active Python environment. The validator itself does not require NuPIC, `nupic.bindings`, NumPy, Cap'n Proto, or Python 2.7.

## NuPIC legacy runtime reality

The actual NuPIC legacy package workflows are Python 2.7-era workflows and commonly require `nupic.bindings`, NumPy 1.12.x, `pycapnp`/Cap'n Proto, and compatible C++ runtime libraries. Keep those install/import issues out of data-format debugging unless the failure is clearly an import failure; use [root troubleshooting](../../references/troubleshooting.md) for package/runtime problems.

## Evidence provenance

This sub-skill distills behavior from NuPIC legacy data docs, quick-start model parameter examples, `nupic.data` source, configuration support source, OPF description API source, and data unit tests. Runtime instructions are bundled here so future agents do not need the original repository checkout.

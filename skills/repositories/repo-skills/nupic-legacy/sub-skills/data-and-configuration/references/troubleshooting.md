# Data and Configuration Troubleshooting

Evidence provenance: distilled from NuPIC legacy quick-start data/model-param docs, `nupic.data.FileRecordStream`, `FieldMetaInfo`, timestamp utilities, aggregation source, configuration support, OPF description API, and data unit tests.

Start with the bundled validator whenever the symptom involves a CSV file:

```bash
python sub-skills/data-and-configuration/scripts/validate_nupic_csv.py data.csv
```

Add model-param checks when the symptom mentions encoders, predicted fields, or missing predictions:

```bash
python sub-skills/data-and-configuration/scripts/validate_nupic_csv.py data.csv \
  --model-params model_params.json \
  --predicted-field consumption
```

For Python 2.7 import failures, `nupic.bindings`, NumPy, `pycapnp`, Cap'n Proto, or compiled library problems, stop using this local troubleshooting page and use [root troubleshooting](../../../references/troubleshooting.md).

## Failure matrix

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Invalid file format: different number of fields in the header rows` | Header rows 1-3 have different widths, often because the third flag row is missing or is a blank line without comma placeholders. | Add a third row with one cell per column, for example `T,` or `,,`. Re-run the validator. |
| First data row is reported as invalid special flags | The file has only two header rows; NuPIC is treating the first data row as the flag row. | Insert a third flag row before data. Use blanks for ordinary fields. |
| `field type ... not a valid FieldMetaType` | Type row contains a typo such as `integer`, `double`, `date`, or `timestamp`. | Use legacy types: `string`, `datetime`, `int`, `float`, `bool`, `list`, or source-level `sdr` if the consumer supports it. |
| `not a valid special flag` | Flag row contains an unknown marker, combined markers such as `RT`, lowercase letters, or an accidental data value. | Use blank, `R`, `S`, `T`, or `C` for public workflows. Preserve source-level `L` only for known learning-control streams. |
| Timestamp parse error | The timestamp string does not match the accepted legacy patterns, has AM/PM, timezone offsets, or unexpected separators. | Convert timestamps to one accepted pattern such as `YYYY-MM-DD HH:MM:SS` or `YYYY-MM-DDTHH:MM:SSZ`. See [data-formats.md](data-formats.md). |
| Row width mismatch | A data row has too many/few cells, usually from an unescaped comma, a trailing comma mismatch, or manual editing. | Open as CSV, not plain text; quote fields containing commas; make every row match the header width. |
| Reset column behaves oddly | Docs show a bool reset example, while source comments/tests expect reset as integer 0/1 in many paths. | Prefer `int` with `R` and values `0`/`1` for portable legacy behavior. |
| Sequence errors or unexpected resets | `S` sequence id changes or reused old ids cause reset/broken-sequence behavior; `R` marks explicit new sequences. | Sort rows by sequence/time, do not return to an old sequence id after leaving it, and make reset rows explicit. |
| Aggregation says no time field was found | Non-null `aggregationInfo` needs a timestamp field. | Ensure exactly one `datetime` column has the `T` flag, and the aggregation field names match CSV row 1. |
| Encoder references a missing field | `modelParams.sensorParams.encoders.<encoder>.fieldname` does not match any CSV header. | Update the CSV header or the encoder `fieldname`. Encoder dictionary keys do not need to match field names; the `fieldname` value does. |
| Changed predicted field but model gives no predictions or `KeyError` | CSV header, encoder `fieldname`, optional `modelParams.predictedField`, OPF `enableInference`, or swarm `inferenceArgs.predictedField` are inconsistent. | Pick one canonical field name and update every location. Then run the validator with `--predicted-field`. Use [../../opf-prediction/](../../opf-prediction/) for inference-output handling. |
| Swarm or OPF experiment cannot find stream source | Stream source lacks the `file://` scheme or resolves relative to a different location than expected. | Use `file:///absolute/path/to/data.csv` in search definitions or experiment controls. Use [../../swarming/](../../swarming/) for search-definition structure. |
| `NTA_CONF_PROP_*` override appears ignored | Environment variable name does not exactly replace dots with underscores, or the process was started before the env var was exported. | For `nupic.cluster.database.host`, export `NTA_CONF_PROP_nupic_cluster_database_host=value` before running NuPIC. Restart the process. |
| Config bool/int/float cast fails | Override value is a string that cannot be cast by `Configuration.getBool`, `getInt`, or `getFloat`. | Use numeric strings where required; booleans should be `0` or `1`. |

## Missing third header row

Bad two-row file:

```csv
timestamp,consumption
datetime,float
2010-07-02 00:00:00,5.4
```

NuPIC treats the data row as the special-flag row. Because `2010-07-02 00:00:00` and `5.4` are not valid flags, the error may look like an invalid flag instead of an obvious missing-header message.

Fixed file:

```csv
timestamp,consumption
datetime,float
T,
2010-07-02 00:00:00,5.4
```

## Invalid type or flag

Valid type row values:

```text
string datetime int float bool list sdr
```

Valid public special row values:

```text
<blank> R S T C
```

Use uppercase flags. Do not write explanatory words such as `timestamp` or `reset` in the flag row.

## Timestamp gotchas

Accepted examples:

```text
2010-07-02 00:00:00
2010-07-02 00:00
2010-07-02
07/02/2010 00:00
2010-07-02T00:00:00Z
2010-07-02T00:00:00.000000Z
```

Common invalid examples:

```text
2010-07-02 12:00 AM      # AM/PM unsupported
2010-07-02T00:00:00+00:00 # offset form unsupported
2010/07/02 00:00:00      # slash order unsupported except m/d/Y hour:minute
```

## Model params field-name triage

When a user says "the CSV validates but OPF gives no predictions":

1. Inspect CSV row 1 and pick the exact predicted field, for example `consumption`.
2. In `modelParams.sensorParams.encoders`, check every active encoder's `fieldname`. At least one relevant encoder should consume `consumption` for a consumption prediction workflow.
3. Check optional `modelParams.predictedField` if present.
4. Check the run code's `model.enableInference({'predictedField': 'consumption'})` in [../../opf-prediction/](../../opf-prediction/).
5. If using swarming, check `inferenceArgs.predictedField` in the search definition and the stream source path in [../../swarming/](../../swarming/).

Remember: encoder names such as `timestamp_timeOfDay` are allowed to differ from CSV names. Compare `fieldname`, not just the encoder dictionary key.

## Aggregation triage

For non-null `aggregationInfo`:

- Confirm a `T` timestamp column exists and parses.
- Confirm every `aggregationInfo.fields` name appears in CSV row 1.
- Use aggregation functions supported by legacy source: `first`, `last`, `sum`, `mean`, `max`, `min`, `mode`, or `wmean:<weightField>`.
- Avoid mixing calendar `years`/`months` with fixed-duration periods such as `hours` and `minutes` in the same block.

If aggregation is not needed, set `aggregationInfo: null` or all period values to zero.

## Configuration override triage

NuPIC translates property names to environment variable names by replacing dots with underscores and prefixing `NTA_CONF_PROP_`.

```bash
# property: nupic.opf.metricWindow
export NTA_CONF_PROP_nupic_opf_metricWindow=500
```

The override is read by the Python process; exporting it in a shell after a long-running process has already started will not affect that process. If full swarming fails after config changes, use [../../swarming/](../../swarming/) for MySQL/service-specific guidance and [root troubleshooting](../../../references/troubleshooting.md) for import/runtime failures.

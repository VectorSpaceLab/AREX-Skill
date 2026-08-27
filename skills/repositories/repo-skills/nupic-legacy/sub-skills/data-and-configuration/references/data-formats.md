# NuPIC Legacy Data Formats

Evidence provenance: distilled from `docs/source/quick-start/example-data.rst`, `src/nupic/data/file_record_stream.py`, `src/nupic/data/field_meta.py`, `src/nupic/data/utils.py`, `src/nupic/data/aggregator.py`, and `tests/unit/nupic/data/file_record_stream_test.py`.

## CSV shape expected by `FileRecordStream`

NuPIC legacy stream files are CSV files with **three metadata header rows** followed by data rows.

| Row | Meaning | Example | Validation rule |
|---|---|---|---|
| 1 | Field names | `timestamp,consumption` | Names identify columns in model params, swarms, encoders, and `FileRecordStream.getFieldNames()`. Avoid duplicates. |
| 2 | Field types | `datetime,float` | Each value must be a known `FieldMetaType`. |
| 3 | Special flags | `T,` | Each cell is blank or a single special marker such as `T`; preserve column count even when most cells are blank. |
| 4+ | Data rows | `2010-07-02 00:00:00,5.4` | Every row should have the same column count as the headers and values should parse according to row 2. |

A minimal valid prediction stream:

```csv
timestamp,consumption
datetime,float
T,
2010-07-02 00:00:00,5.4
2010-07-02 00:15:00,3.6
2010-07-02 00:30:00,2.4
```

If there are no special flags, still include the third row with the right number of separators:

```csv
name,value
string,float
,
a,1.0
b,2.0
```

A blank third line is ambiguous and only matches a one-column stream cleanly. For multi-column input, write the comma placeholders explicitly.

## Field types

`FileRecordStream` reads the second header row into `FieldMetaType` values and converts data strings to Python objects.

| Type | Parsed as | Notes |
|---|---|---|
| `string` | string | Empty string is preserved for string fields; string escaping/unescaping handles commas, tabs, and newlines in NuPIC-written files. |
| `datetime` | `datetime.datetime` | Must match one of the legacy timestamp formats listed below. A `T` flag should be on a `datetime` column. |
| `int` | integer or missing sentinel | `None` and `NULL` are accepted as missing values by the legacy parser. Safest type for reset (`R`) fields. |
| `float` | float or missing sentinel | `None` is accepted as missing by the legacy parser. |
| `bool` | boolean | Accepts `true`, `t`, `1`, `false`, `f`, `0` case-insensitively. Quick-start docs show a bool reset column, but source comments/tests are stricter about reset being `int`; use `int` 0/1 for portable legacy behavior. |
| `list` | list of ints from a space-separated string | Public quick-start text calls `list` third-party/not supported, but the legacy source and tests parse it for category-style use. Use only when the consuming workflow expects list labels. |
| `sdr` | list of 0/1 integers | Supported by source-level utilities; not part of the simple quick-start CSV examples. |

Empty cells are treated as missing values before type conversion. Numeric missing values become NuPIC's missing-data sentinel in `FileRecordStream`; downstream code may still reject missing values for a chosen model or metric.

## Special flags

The public quick-start flags are:

| Flag | Meaning | Expected type | Behavior |
|---|---|---|---|
| blank | ordinary field | any valid type | Normal input value. |
| `R` | reset | safest: `int` 0/1 | Inserts a model reset when true/1. Use to mark explicit sequence starts. |
| `S` | sequence id | `string` or `int` | Inserts a reset when the sequence id changes. Reusing an old sequence id after leaving it can trigger a broken-sequence error in writer paths. |
| `T` | timestamp | `datetime` | Identifies the timestamp field used by aggregation and time-aware workflows. At most one timestamp field should carry `T`. |
| `C` | category | `int` or `list` | Identifies category labels. A list value is a space-separated list of integer category ids. |

The legacy source also defines `L` as a learning flag. It is not part of the quick-start R/S/T/C public guidance; preserve it only when maintaining an existing legacy stream that intentionally uses learning control.

Do not combine flags in one cell (`RT` is invalid). Use a single marker or leave the cell blank.

## Timestamp formats

Legacy `parseTimestamp` accepts these exact patterns:

```text
%Y-%m-%d %H:%M:%S.%f
%Y-%m-%d %H:%M:%S:%f
%Y-%m-%d %H:%M:%S
%Y-%m-%d %H:%M
%Y-%m-%d
%m/%d/%Y %H:%M
%m/%d/%y %H:%M
%Y-%m-%dT%H:%M:%S.%fZ
%Y-%m-%dT%H:%M:%SZ
%Y-%m-%dT%H:%M:%S
```

Gotchas:

- No AM/PM forms are accepted.
- ISO timestamps with offsets such as `+00:00` are not in the accepted list; use `Z` forms or strip the offset before feeding NuPIC.
- Microseconds use `%f`; the first format is NuPIC's default serialized datetime form.
- Timestamp order matters inside a sequence. Writer-side sequence checks raise errors for time going backward in the same sequence.

## `FileRecordStream` API shape

Constructor signature verified from installed/source inspection:

```python
FileRecordStream(streamID, write=False, fields=None, missingValues=None,
                 bookmark=None, includeMS=True, firstRecord=None)
```

Typical read pattern in a Python 2.7 NuPIC runtime:

```python
from nupic.data.file_record_stream import FileRecordStream

with FileRecordStream("data.csv") as stream:
    print(stream.getFieldNames())       # list of header names
    print(stream.getFields())           # FieldMetaInfo(name, type, special) tuples
    print(stream.getDataRowCount())     # count excluding three header rows
    record = stream.getNextRecord()     # list of typed values, or None at EOS
```

Useful methods and shapes:

| Method | Shape | Use |
|---|---|---|
| `getFieldNames()` | `list[str]` | Compare CSV columns to model params encoder `fieldname` values. |
| `getFields()` | list of `(name, type, special)` tuples | Inspect metadata used by `RecordSensor`, aggregation, and writers. |
| `getNextRecord()` | list of typed values or `None` | Pull one parsed data row; missing numeric fields become NuPIC's sentinel. |
| `getStats()` | `{'min': [...], 'max': [...]}` | Min/max for scalar columns; non-scalar fields have `None`. |
| `getDataRowCount()` | integer | Counts data rows only. |
| `setAutoRewind(True/False)` | no return | Rewind at EOF for streaming use cases. |
| `getBookmark()` / `firstRecord` | JSON bookmark / 0-based index | Resume reading from a known point. |

When constructing a Network API `RecordSensor` or `FileRecordStream`-backed input, validate the file here first, then use [../../network-api/](../../network-api/) for region construction and linking.

## Validate before handing off

Run the bundled validator from the generated skill tree:

```bash
python sub-skills/data-and-configuration/scripts/validate_nupic_csv.py data.csv
```

Add expected field checks when preparing OPF model params:

```bash
python sub-skills/data-and-configuration/scripts/validate_nupic_csv.py data.csv \
  --predicted-field consumption \
  --encoder-field timestamp \
  --encoder-field consumption
```

Then use [references/model-params-and-config.md](model-params-and-config.md) to align encoders, aggregation, and config overrides before moving to [../../opf-prediction/](../../opf-prediction/) or [../../swarming/](../../swarming/).

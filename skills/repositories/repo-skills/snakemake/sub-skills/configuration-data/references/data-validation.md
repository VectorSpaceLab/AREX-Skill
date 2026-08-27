# Data Validation

Use `snakemake.utils.validate(data, schema, set_default=True)` for JSON Schema validation of workflow config dictionaries and sample metadata tables. The function accepts a config `dict`, a pandas `DataFrame`, a Polars `DataFrame`, or a Polars `LazyFrame`. Schemas can be JSON or YAML.

## Config Dictionary Validation

Validate immediately after loading config and before rules consume values:

```python
from snakemake.utils import validate

configfile: "config/config.yaml"
validate(config, "schemas/config.schema.yaml")
```

Example schema:

```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
type: object
properties:
  samples:
    type: string
  adapter:
    type: string
    pattern: "^[ACGT]+$"
  threshold:
    type: number
    default: 0.8
required:
  - samples
additionalProperties: false
```

With the default `set_default=True`, schema defaults are inserted into dictionaries when the enclosing object has a `properties` schema. If a required key is missing, validation fails with `Error validating config file.` and the underlying jsonschema message.

## Sample Table Validation

For a pandas table, the schema models one row record:

```python
import pandas as pd
from snakemake.utils import validate

samples = pd.read_table(config["samples"]).set_index("sample", drop=False)
validate(samples, "schemas/samples.schema.yaml")
```

Example row schema:

```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
description: one sample row
type: object
properties:
  sample:
    type: string
  condition:
    type: string
  tissue:
    type: string
    default: blood
  n:
    type: integer
    default: 0
required:
  - sample
  - condition
additionalProperties: false
```

Expected behavior:

- For pandas `DataFrame`, Snakemake validates each row after excluding null values.
- Missing columns with defaults are added to the DataFrame.
- Null values in existing columns can be filled from defaults by positional alignment.
- A row failure is reported as `Error validating row N of data frame.`
- For Polars `DataFrame`, missing default columns are inserted and nulls can be filled.
- For Polars `LazyFrame`, Snakemake validates the first 1000 rows; defaults are not written back and a warning states that LazyFrame does not support setting default values.

## Relative `$ref` Resolution

Snakemake 9.23.1 injects a local file URI as the schema `$id` while validating. Relative `$ref` entries resolve relative to the local schema file, even if the schema itself declares a remote `$id`.

Example layout:

```text
schemas/
  config.schema.yaml
  fragments/
    sample-map.schema.yaml
```

```yaml
# schemas/config.schema.yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
type: object
properties:
  samples:
    $ref: "fragments/sample-map.schema.yaml"
required: [samples]
```

Troubleshooting signal: if a relative reference cannot be loaded, the error usually mentions a missing schema file path or a reference resolution failure. Check the schema file location relative to the referencing schema, not relative to the current shell directory.

## Standalone Preflight Script

The bundled script can validate config files and sample tables outside a full Snakemake run:

```bash
python sub-skills/configuration-data/scripts/validate_config_schema.py \
  --data config/config.yaml \
  --schema schemas/config.schema.yaml
```

```bash
python sub-skills/configuration-data/scripts/validate_config_schema.py \
  --data samples.tsv \
  --schema schemas/samples.schema.yaml \
  --table tsv \
  --index sample \
  --dump-normalized samples.normalized.tsv
```

The script uses `snakemake.utils.validate` so the success/failure behavior matches Snakemake where possible. It intentionally does not import local repository paths.

## Validation Design Checklist

- Use `required` for values the workflow cannot infer safely.
- Use `default` for non-sensitive, deterministic options that should be filled into `config` or sample tables.
- Use `additionalProperties: false` for production configs when typos should fail fast.
- Keep PEP schemas separate from workflow config schemas; PEP validation uses Eido via `pepschema`.
- Validate before deriving `samples.index`, helper lookups, rule `params`, or pathvars from config.
- For CLI overrides, dry-run with `--printshellcmds` after validation to catch type coercion surprises.

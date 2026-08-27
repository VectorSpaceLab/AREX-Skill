# Configuration Reference

This reference targets Snakemake 9.23.1 configuration behavior. It is self-contained; do not rely on source checkout examples at runtime.

## Standard Config Files

Load YAML or JSON config with a top-level Snakefile directive:

```python
configfile: "config/config.yaml"

rule all:
    input:
        expand("results/{sample}.txt", sample=config["samples"])
```

Important semantics:

- `config` is always available; it is an empty dictionary when no config source is used.
- `configfile: "relative/path.yaml"` is interpreted relative to the working directory for the run, not necessarily relative to the Snakefile that contains it.
- A config file must parse as JSON or YAML and must have mapping keys at the top level.
- YAML can opt into YTE processing by setting top-level `__use_yte__: true`.
- Top-level Python code can mutate `config`, for example with `snakemake.utils.update_config(config, {...})`; changes made inside rule execution are not visible to other rules.
- In shell string interpolation, use `{config[foo]}` rather than `{config["foo"]}`.

Minimal YTE example:

```yaml
__use_yte__: true
threads: ?2 * 4
outdir: results
```

## Precedence and Merging

Snakemake recursively merges configuration dictionaries. When the same key appears in multiple sources, the later or more specific source wins.

Typical order:

1. Workflow `configfile` directives and included config updates provide defaults.
2. CLI `--configfile` or `--configfiles` files are applied in the order given; later files overwrite same nested keys while preserving missing keys from earlier files.
3. CLI `--config KEY=VALUE` overwrites config-file values.
4. `--replace-workflow-config` changes the behavior of CLI config files: workflow-defined config is discarded, then CLI config files and CLI `--config` provide the resulting config.

Concrete command patterns:

```bash
snakemake --cores 1 --dry-run --printshellcmds \
  --configfile defaults.yaml override.yaml \
  --config threshold=0.8 'samples={"A":"data/A.fq","B":"data/B.fq"}'
```

```bash
snakemake --cores 1 --dry-run --printshellcmds \
  --replace-workflow-config \
  --configfile production.yaml \
  --config run_id=batch42
```

CLI values are parsed as Python-like values where possible. Quote at the shell boundary so Snakemake receives the whole key-value pair:

- Good: `--config 'threshold=0.8' 'enabled=True' 'nested={"mode":"strict"}'`
- Good for strings that look numeric in profiles: quote the YAML profile value, e.g. `sample_id: "001"`.
- Risky: `--config nested={"mode":"strict"}` without shell quotes; the shell may strip or split characters before Snakemake parses them.

## Profiles as Config Sources

Profiles and workflow profiles are primarily CLI defaults, but their YAML can set config-related CLI arguments. A profile entry like this becomes `--config sample=A threshold=0.8`:

```yaml
cores: 4
printshellcmds: true
config:
  sample: A
  threshold: 0.8
```

Profile behavior relevant to config work:

- `--profile` can be given multiple times; later profiles override earlier top-level profile entries.
- `--workflow-profile` is searched relative to the current working directory and workflow profile locations; it overrides general profile settings per key.
- Any explicit CLI option overrides the same profile option.
- Profile YAML is YTE-processed and expands environment variables in scalar strings.
- Profile `config:` is converted to CLI-style key-value pairs, so it has the same override role as `--config`.

Route profile selection and execution strategy to `../execution-cli/SKILL.md`; keep this sub-skill focused on the resulting `config` values.

## Sample Tables

For tabular sample metadata, keep workflow options in YAML/JSON config and per-sample metadata in a table:

```python
import pandas as pd
from snakemake.utils import validate

configfile: "config.yaml"
validate(config, "schemas/config.schema.yaml")

samples = pd.read_table(config["samples"]).set_index("sample", drop=False)
validate(samples, "schemas/samples.schema.yaml")

rule all:
    input:
        expand("results/{sample}.txt", sample=samples.index)

def reads_for_sample(wildcards):
    return samples.loc[wildcards.sample, "fastq"]
```

Use an input function when the metadata lookup depends on job wildcards. Plain `expand(...)` in a rule definition is evaluated during initialization, before job-specific wildcard values exist.

## PEP Metadata

Snakemake can parse Portable Encapsulated Project metadata with `pepfile`:

```python
pepfile: "pep/config.yaml"
pepschema: "schemas/pep.yaml"

rule all:
    input:
        expand("results/{sample}.txt", sample=pep.sample_table["sample_name"])
```

PEP guidance:

- `pepfile` creates a global `pep` project object.
- `pepschema` validates the project with Eido and requires `pepfile` to be set first.
- `pepfile` and `pepschema` accept strings and `pathlib.Path` values.
- PEP support requires `peppy`; PEP schema validation requires `eido`.
- Use PEP for portable sample/project metadata, not workflow-specific analysis options. Keep workflow options in ordinary config files.

## Envvars

Declare required environment variable names with `envvars:`:

```python
import os

envvars:
    "API_TOKEN"

rule fetch:
    output:
        "data/raw.json"
    params:
        token=os.environ["API_TOKEN"]
    shell:
        "curl -H 'Authorization: Bearer {params.token}' -o {output} https://example.invalid/data"
```

Semantics:

- Snakemake fails early if a declared variable is undefined.
- Names must contain only ASCII word characters: letters, digits, and `_`.
- Declaring an envvar does not automatically make it available inside every job shell command. Pass required values explicitly via `params` for provenance and reproducibility.
- CLI `--envvars NAME ...` registers variables for cloud/remote jobs, but it is not a substitute for explicit use in rule code.

## Pathvars

Pathvars let a workflow define named path fragments and refer to them as `<name>` in paths:

```python
pathvars:
    results="results/custom",
    per="{sample}",
    nested="<per>"

rule all:
    input:
        collect("<results>/qc/{sample}.txt", sample=["A", "B"])

rule qc:
    output:
        "<results>/qc/<nested>.txt"
    shell:
        "touch {output}"
```

Built-in defaults include `results`, `stats`, `reports`, `temp`, `resources`, `logs`, and `benchmarks`.

Pathvar precedence is level-based; lower level numbers override higher ones:

1. Rule-level `pathvars:`
2. Module-level `pathvars:` and module config `pathvars`
3. Config-provided `pathvars`
4. Workflow-level `pathvars:`
5. Built-in defaults

Config pathvars can be supplied from config files or CLI config:

```bash
snakemake --cores 1 --dry-run --printshellcmds \
  --config 'pathvars={"results":"scratch/results","logs":"scratch/logs"}'
```

Pathvar rules:

- Names must match lowercase alphanumeric/underscore syntax and start with a lowercase letter.
- Values must be strings.
- Nested references such as `nested="<per>"` are allowed.
- Cycles fail with `Cyclic pathvar reference detected`.
- Undefined references fail with `Undefined pathvar`.

## Data-Driven Helpers

Snakemake 9.23.1 exposes helper functions in workflows for metadata-driven paths.

### `lookup`

Use `lookup` against pandas DataFrames/Series with `query=...`, or mappings with `dpath=...`:

```python
import pandas as pd
samples = pd.read_table("samples.tsv")

rule selected:
    input:
        collect("results/{item.sample}.txt", item=lookup(query="condition == 'case'", within=samples))
```

```python
configfile: "config.yaml"

rule maybe_extra:
    input:
        branch(lookup(dpath="switches/extra", within=config, default=False), then="extra.txt")
```

Notes:

- DataFrame queries use `DataFrame.query()`.
- A query with one row returns a named tuple; multiple rows return a list of named tuples.
- `cols="column"` returns a list of values from one column; `cols=[...]` keeps named-tuple rows with selected columns.
- `is_nrows=N` returns a boolean.
- Wildcards and namespace arguments can be formatted into `query`, `dpath`, and `cols`; if wildcards are needed, `lookup` returns an input function.
- Missing mapping paths raise `LookupError` unless `default=` is provided.

### `branch` and `evaluate`

Use `branch` to select inputs from a boolean, callable, or keyed cases mapping. Use `evaluate` when a wildcard-formatted Python expression is clearer:

```python
rule choose_input:
    input:
        branch(evaluate("{sample} == 'control'"), then="controls/{sample}.txt", otherwise="cases/{sample}.txt")
    output:
        "results/{sample}.txt"
    shell:
        "cp {input} {output}"
```

`evaluate("{sample} == 'control'")` returns a function evaluated when wildcards are known. If expression evaluation fails, Snakemake reports both the original expression and the formatted expression.

### `collect`

`collect` is an alias for `expand` intended to document that files are being collected from previous jobs:

```python
rule all:
    input:
        collect("results/{sample}.txt", sample=samples["sample"])
```

### `subpath`

Use `subpath` to derive path components safely from strings, `Path` objects, or functions:

```python
rule index:
    input:
        bam="mapped/{sample}.bam"
    output:
        bai=subpath(input.bam, with_suffix=".bai")
```

Common options: `strip_suffix=`, `with_suffix=`, `basename=True`, `parent=True`, and `ancestor=N`. `basename`, `parent`, and `ancestor` are mutually constrained; invalid combinations raise `ValueError`.

### `exists`

Use `exists(path)` inside a Snakemake workflow when a decision must respect default storage settings:

```python
rule optional:
    input:
        branch(exists("data/optional.tsv"), then="data/optional.tsv", otherwise=[])
```

`exists()` requires a workflow context. It applies default storage modifiers before checking local existence or managed storage existence. Route storage-provider configuration to deployment/storage guidance.

## Smoke Commands

After editing configuration behavior, prefer dry-runs first:

```bash
snakemake --cores 1 --dry-run --printshellcmds
snakemake --cores 1 --dry-run --printshellcmds --configfile config.yaml --config 'threshold=0.8'
snakemake --cores 1 --dry-run --printshellcmds --replace-workflow-config --configfile production.yaml
```

Expected healthy signal: Snakemake builds the DAG and prints planned jobs/shell commands without schema, config, pathvar, or missing input errors.

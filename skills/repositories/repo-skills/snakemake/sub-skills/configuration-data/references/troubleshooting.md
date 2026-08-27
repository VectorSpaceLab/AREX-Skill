# Configuration Troubleshooting

## Config Precedence Surprises

Symptoms:

- A value from the Snakefile `configfile` appears to override a CLI file unexpectedly.
- Nested config keys disappear or remain from an earlier file.
- A workflow config key is missing only when `--replace-workflow-config` is used.

Checks:

1. List config sources in order: workflow `configfile`, included files, `--configfile` files in CLI order, profile `config`, explicit `--config`.
2. Remember recursive merge behavior: later files replace same nested keys but preserve unrelated nested keys.
3. Remember `--config` wins over config files.
4. If `--replace-workflow-config` is present, workflow config keys not supplied by CLI config files become undefined.
5. Add a temporary top-level rule or `print(config)` while debugging, then remove it before finalizing.

Useful dry-run:

```bash
snakemake --cores 1 --dry-run --printshellcmds --configfile defaults.yaml override.yaml --config 'mode="strict"'
```

## CLI Quoting and Type Coercion

Symptoms:

- Strings like `001` become numbers or lose leading zeros.
- Nested dictionaries do not parse.
- Shell splits a value before Snakemake sees it.

Fixes:

- Quote each complete key-value pair at the shell boundary: `--config 'sample_id="001"'`.
- Use Python dict syntax for nested values: `--config 'params={"min_cov":10,"mode":"strict"}'`.
- In profile YAML, quote strings that look numeric: `sample_id: "001"`.
- Prefer config files over complex CLI literals for nested or list-heavy data.

## Schema Defaults Not Appearing

Symptoms:

- A default from the schema is not present in `config` or the sample table.
- Polars LazyFrame validation warns about defaults.

Checks:

- `validate(..., set_default=True)` is the default; verify you did not pass `set_default=False`.
- Defaults are applied under JSON Schema `properties`; ensure the enclosing object schema is explicit.
- For sample tables, check that missing values are parsed as nulls (`NA`, empty cells) and that the column name matches the schema property.
- Polars LazyFrame validation checks up to 1000 rows and does not write defaults back.

## Missing Required Fields

Symptoms:

- `Error validating config file.`
- `Error validating row N of data frame.`
- Underlying jsonschema messages such as `'samples' is a required property` or a pattern/type failure.

Fixes:

- Validate config before reading dependent sample files so the failing key is clearer.
- For sample tables, inspect row `N` in the parsed DataFrame, not just the raw text file; delimiter or header mistakes can shift columns.
- Use `additionalProperties: false` only when you are ready for typo-like keys to fail.

## Relative `$ref` Failures

Symptoms:

- Schema fragments cannot be found.
- A remote `$id` seems to redirect local references unexpectedly.

Snakemake 9.23.1 resolves relative `$ref` entries against the local schema file. Check that referenced files exist relative to the schema that contains the `$ref`.

## YTE Syntax Errors

Symptoms:

- Config or profile parsing reports invalid JSON/YAML.
- A YTE expression is left unevaluated or raises during parsing.

Fixes:

- Add top-level `__use_yte__: true` to YAML files that need YTE processing.
- Keep valid YAML indentation; do not mix tabs and spaces.
- Start with a minimal expression such as `value: ?5 + 5`, then add complexity.
- Remember profiles are YTE-processed too; profile parse failures can occur before workflow parsing.

## PEP Optional Dependency Errors

Symptoms:

- `For PEP support, please install peppy.`
- `For PEP schema support, please install eido.`
- `Please specify a PEP with the pepfile directive.`

Fixes:

- Install/enable the optional package that provides PEP support before using `pepfile`.
- Install/enable Eido before using `pepschema`.
- Put `pepfile:` before `pepschema:` in the Snakefile.
- Keep workflow-specific knobs out of the PEP and in ordinary config files.

## Envvars Expectations

Symptoms:

- Snakemake fails before DAG construction with undefined environment variables.
- A shell command cannot see a variable even though it is listed under `envvars:`.
- An environment variable name is rejected.

Fixes:

- Export the variable before running Snakemake.
- Use only ASCII letters, digits, and `_` in names.
- Explicitly pass values via `params`, e.g. `params: token=os.environ["API_TOKEN"]`; `envvars:` asserts and propagates for remote/cloud contexts but does not automatically inject values into every job shell command.

## Pathvar Cycles and Invalid Names

Symptoms:

- `Cyclic pathvar reference detected`.
- `Undefined pathvar`.
- `Pathvars have to be a mapping of str to str`.

Fixes:

- Ensure every pathvar value is a string.
- Use lowercase names starting with a letter: `results`, `sample_dir`, not `Results` or `1dir`.
- Break cycles such as `foo="<bar>"` and `bar="<foo>"`.
- Check precedence: rule-level values override module/config/workflow/default values.

## Helper Misuse

Symptoms and fixes:

- `lookup` says `Must provide a dataframe, series, or mapping`: pass `within=samples` or `within=config`.
- `lookup` says query is only for DataFrames/Series: use `dpath=` for dictionaries.
- `lookup` raises `Dpath not found`: add `default=` if missing data is valid.
- `branch` raises missing case key: ensure the condition returns a key present in `cases`.
- `evaluate` reports a formatted expression: inspect the formatted expression; wildcard string quoting is often the issue.
- `subpath` raises suffix/argument errors: confirm the value is a string or `Path`, suffix matches exactly, and `basename`, `parent`, and `ancestor` are not combined invalidly.
- `exists()` says workflow context is missing: call it from a Snakefile workflow context, not from a standalone Python script.

## Version-Specific CLI Notes

For Snakemake 9.23.1, `--reason` is not a valid CLI flag. Dry-run output already includes job reasoning. Use:

```bash
snakemake --cores 1 --dry-run --printshellcmds
```

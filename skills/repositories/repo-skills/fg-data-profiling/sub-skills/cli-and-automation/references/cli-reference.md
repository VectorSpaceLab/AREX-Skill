# CLI Reference

## Command names

fg-data-profiling installs two console scripts:

```bash
data_profiling -h
pandas_profiling -h
```

`data_profiling` is the preferred current command. `pandas_profiling` remains as
a legacy command name for compatibility.

## Usage shape

```bash
data_profiling [options] input_file [output_file]
```

The CLI profiles a file that pandas can read and writes an HTML report by
default. If `output_file` is omitted, it replaces the input suffix with `.html`.

## Options

| Option | Meaning |
| --- | --- |
| `-h`, `--help` | Show help and exit. |
| `--version` | Print CLI version. |
| `-s`, `--silent` | Only generate the report; do not open it in a browser. |
| `-m`, `--minimal` | Use minimal configuration for large datasets. |
| `-e`, `--explorative` | Use exploratory configuration with richer unicode/file/image-oriented analysis. |
| `--pool_size N` | Number of CPU cores to use; `0` means multiprocessing CPU count. |
| `--title TEXT` | Report title. |
| `--infer_dtypes` | Infer DataFrame dtypes. |
| `--no-infer_dtypes` | Read dtypes as pandas read them. |
| `--config_file PATH` | Use a YAML settings file. Do not combine with `--minimal`. |
| `input_file` | Required data file. |
| `output_file` | Optional output report file. |

## Input extension behavior

The CLI uses the package's pandas reader utility. Supported extensions include
CSV, JSON, JSONL, Stata, TSV, Excel, HDF, SAS, parquet, pickle, and common
pandas-supported compression suffixes. Unknown extensions are read as CSV with a
warning. `.tar` is rejected; extract it first or write custom Python loading
code.

## Output files

- `report.html` is the normal CLI output.
- A missing `output_file` means `<input-stem>.html`.
- If a custom config disables inline assets through the Python API or YAML, keep
  generated asset directories with the HTML report.

## Examples

Minimal CSV profile:

```bash
data_profiling --silent --minimal customers.csv customers-profile.html
```

Explorative URL/text report:

```bash
data_profiling --silent --explorative urls.csv urls-profile.html
```

Custom YAML settings:

```bash
data_profiling --silent --config_file profiling-config.yml data.csv configured-profile.html
```

Do not add `--minimal` to the last command. Encode minimal-style settings inside
the YAML file instead.

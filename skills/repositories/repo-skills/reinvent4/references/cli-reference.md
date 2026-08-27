# CLI Reference

## Purpose

Read this when choosing REINVENT4 command-line entry points, global flags, config formats, logging, device overrides, seed handling, and safe smoke checks.

## Entry Points

| Command | Use | Safe check |
| --- | --- | --- |
| `reinvent` | Main molecular design CLI for sampling, scoring, transfer learning, staged learning, and enumeration configs. | `reinvent --help` |
| `reinvent_datapre` | SMILES preprocessing CLI driven by `data_pipeline.toml`. | `reinvent_datapre --help` |

## `reinvent` Flags

```bash
reinvent [OPTIONS] [FILE]
```

- `FILE`: input configuration file. The extension usually determines format.
- `-f`, `--config-format`: force `toml`, `json`, or `yaml`.
- `-d`, `--device`: override the config device, such as `cpu` or `cuda:0`.
- `-l`, `--log-filename`: write logs to a file instead of stderr.
- `--log-level`: choose `info`, `debug`, `verbose`, `warning`, `error`, or a standard Python logging level.
- `-s`, `--seed`: set random seeds for reproducibility.
- `--dotenv-filename`: load environment variables for scoring components that need them.
- `--enable-rdkit-log-levels`: enable selected RDKit logs: `all`, `error`, `warning`, `info`, `debug`.
- `-V`, `--version`: print package/version info and exit.

Use CPU for static smoke checks unless the task explicitly requires GPU behavior:

```bash
reinvent --device cpu --seed 123 --log-filename smoke.log config.toml
```

## `reinvent_datapre` Flags

```bash
reinvent_datapre [-l FILE] FILE
```

- `FILE`: TOML data-pipeline configuration.
- `-l`, `--log-filename`: write preprocessing logs to a file.

The preprocessor writes `output_smiles_file` from the config and also writes a `regex.smi` side-effect file in the working directory after regex filtering.

## Config Format Conversion

Use `scripts/convert_config_format.py` when a task needs TOML/JSON/YAML conversion without depending on source checkout utilities:

```bash
python scripts/convert_config_format.py config.toml config.json
python scripts/convert_config_format.py config.json config.yaml --output-format yaml
```

YAML input/output requires PyYAML. TOML input uses Python 3.11+ `tomllib`; TOML output is intentionally not supported because Python stdlib cannot write TOML.

## Routing Hints

- `run_type = "sampling"`: use `sub-skills/sampling/SKILL.md`.
- `run_type = "scoring"`: use `sub-skills/scoring/SKILL.md`.
- `run_type = "transfer_learning"` or `run_type = "staged_learning"`: use `sub-skills/learning/SKILL.md`.
- `run_type = "enumeration"`: use `sub-skills/enumeration/SKILL.md`.
- `data_pipeline.toml` or `reinvent_datapre`: use `sub-skills/data-pipeline/SKILL.md`.

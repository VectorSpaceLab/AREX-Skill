# CLI Reference

The legacy CLI is deprecated. Prefer the Python API for real work.
Use the CLI only when you need to mirror older workflows or inspect the surface
that the installed package still exposes.

The root help currently advertises:

```text
hls4ml [-h] [--version] {config,convert,build,report} ...
```

## Root subcommands

| Subcommand | Purpose | Notes |
| --- | --- | --- |
| `config` | Create a conversion configuration file | Keras `.h5` / `.json` inputs only in the current CLI implementation |
| `convert` | Convert a config file into a project | Uses the YAML config produced by `config` or by the Python API |
| `build` | Build a generated project | Legacy dispatcher only handles Vivado and Quartus in this codebase |
| `report` | Show a synthesis report | Legacy dispatcher only handles Vivado and Quartus in this codebase |

## `config`

```text
hls4ml config [-h] [-m MODEL] [-w WEIGHTS] [-p PROJECT] [-d DIR]
              [-f FPGA] [-bo BOARD] [-ba BACKEND] [-c CLOCK]
              [-g GRANULARITY] [-x PRECISION] [-r REUSE_FACTOR]
              [-o OUTPUT]
```

Useful flags:

- `-m, --model`: model file to convert
- `-w, --weights`: optional weights file for JSON models
- `-p, --project`: project name
- `-d, --dir`: output directory
- `-f, --fpga`: FPGA part
- `-bo, --board`: accelerator board
- `-ba, --backend`: backend name
- `-c, --clock`: clock period in ns
- `-g, --granularity`: config granularity
- `-x, --precision`: default precision string
- `-r, --reuse-factor`: default reuse factor
- `-o, --output`: output file name

Notes:

- The CLI config path is legacy and is Keras-oriented.
- ONNX and TensorFlow `.pb` creation are not supported by the current CLI
  config command.

## `convert`

```text
hls4ml convert [-h] [-c CONFIG]
```

- `-c, --config`: YAML configuration file to convert.

## `build`

Current root help:

```text
hls4ml build [-h] [-p PROJECT] [-l]
```

Root flags:

- `-p, --project`: generated project directory
- `-l, --list-options`: inspect backend-specific legacy build flags for that
  project

Vivado-specific extra flags accepted after the project is known:

- `-c, --simulation`
- `-s, --synthesis`
- `-r, --co-simulation`
- `-v, --validation`
- `-e, --export`
- `-l, --vivado-synthesis`
- `-a, --all`
- `--reset`

Quartus-specific extra flags accepted after the project is known:

- `-s, --synthesis`
- `-q, --quartus-synthesis`
- `-a, --all`

## `report`

Current root help:

```text
hls4ml report [-h] [-p PROJECT] [-l]
```

Root flags:

- `-p, --project`: generated project directory
- `-l, --list-options`: inspect backend-specific legacy report flags for that
  project

Vivado-specific extra flag:

- `-f, --full`

Quartus-specific extra flag:

- `-b, --open-browser`

## Practical guidance

- Use the Python API for new workflows.
- Use the CLI only for compatibility checks or to inspect an old project.
- If you need a backend beyond Vivado or Quartus, use the backend's Python
  methods and parser APIs instead of the legacy CLI.

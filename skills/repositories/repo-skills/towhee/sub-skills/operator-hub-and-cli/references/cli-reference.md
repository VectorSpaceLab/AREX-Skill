# CLI reference and safe validation

This reference covers Towhee's command entry points and safe help-only checks. It intentionally does not cover live service startup; route service runtime work to [serving-and-triton](../../serving-and-triton/SKILL.md).

## Package entry points

| Entry point | Target | Safe validation |
|---|---|---|
| `towhee` | `towhee.command.cmdline:main` | `towhee --help`, `towhee init --help`, `towhee server --help` |
| `python -m towhee` | Uses the package `__main__` module and reaches the same command main. | Use when the console script is absent or PATH is stale. |
| `triton_builder` | Triton pipeline-builder command in the non-model package install path. | Not covered here; route to [serving-and-triton](../../serving-and-triton/SKILL.md). |

Use [../scripts/check_cli_help.py](../scripts/check_cli_help.py) for a no-network, no-server smoke check.

## Top-level command

```bash
towhee --help
python -m towhee --help
```

Expected help signal:

- exits with code `0`;
- mentions the `init` subcommand;
- mentions the `server` subcommand.

If the console script fails because it is not on PATH, rerun the same check with `python -m towhee` or the script's `--python-module` option.

## `towhee init`

Help form:

```bash
towhee init --help
```

Grammar:

```text
towhee init [-h] [-d DIR] [-t {pyop,nnop}] uri
```

| Argument or flag | Meaning | Side-effect risk when used without `--help` |
|---|---|---|
| `uri` | Operator repo uri in `<repo-author>/<repo-name>` form. | Used to rewrite template names into the target operator identity. |
| `-d`, `--dir` | Directory for the operator repo; defaults to current directory. | Creates/writes files under this directory. |
| `-t`, `--type` | Template type: `pyop` for Python-only operator, `nnop` for neural-network operator. | Downloads a remote template repo before initializing files. |

Operational caveats:

- `towhee init --help` is safe.
- Running `towhee init ...` is not a parser-only action: it contacts the Towhee Hub, downloads either the Python-operator or NN-operator template, writes files into `--dir`, and removes a temporary template directory after success.
- Use actual initialization only with explicit user approval and an isolated target directory.
- `pyop` templates are for Python processing functions/classes. `nnop` templates are for model-backed operators; route training-loop work to [training-and-models](../../training-and-models/SKILL.md).

## `towhee server`

Help form:

```bash
towhee server --help
```

Grammar:

```text
towhee server [-h] [--host HOST] [--http-port HTTP_PORT] [--grpc-port GRPC_PORT]
              [--uri [URI ...]] [--params [PARAMS ...]] [source ...]
```

| Argument or flag | Meaning | Side-effect risk when used without `--help` |
|---|---|---|
| `source` | Python module service (`module:service`) or Hub pipeline repo names. | Imports user code or downloads/loads Hub pipelines. |
| `--host` | Service host, default `0.0.0.0`. | Binds network interfaces. |
| `--http-port` | HTTP port, default `8000`. | Starts an HTTP server when no GRPC port is supplied. |
| `--grpc-port` | GRPC port. | Starts a GRPC server when supplied. |
| `--uri` | Per-pipeline service route paths. | Used to build API service routes. |
| `--params` | Comma-separated initialization parameters. | Passed into pipeline config objects. |

Operational caveats:

- `towhee server --help` is safe.
- Running `towhee server ...` starts a long-running service, binds ports, and may import a local module or fetch Hub pipelines. Do not run it as a CLI validation step.
- If a task needs a live server, move to [serving-and-triton](../../serving-and-triton/SKILL.md) and plan ports, dependencies, process cleanup, and client checks.

## Safe CLI validation script

Run from any environment where Towhee is importable:

```bash
python ../scripts/check_cli_help.py
```

Force module execution when the `towhee` console script is unavailable:

```bash
python ../scripts/check_cli_help.py --python-module
```

The script runs only these help commands by default:

1. `towhee --help`
2. `towhee init --help`
3. `towhee server --help`

It asserts that the top-level help lists both subcommands, that `init` help includes `--dir`, `--type`, `pyop`, and `nnop`, and that `server` help includes `--host`, `--http-port`, `--grpc-port`, `--uri`, and `--params`.

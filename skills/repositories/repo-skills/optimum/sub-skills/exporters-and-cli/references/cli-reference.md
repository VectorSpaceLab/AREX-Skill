# Optimum CLI reference

This reference covers the base `optimum-cli` entry point, environment report, export-command routing, and dynamic subcommand registration. It is self-contained for runtime use; source facts were verified from Optimum package metadata, CLI implementation, public docs, tests, and installed inspection.

## Base command surface

The base distribution exposes the console script:

```bash
optimum-cli
```

Safe first checks:

```bash
optimum-cli --help
optimum-cli env
optimum-cli export --help
```

Base root subcommands are:

| Command | Base responsibility | Notes |
| --- | --- | --- |
| `env` | Print versions and platform facts for issue reports. | Reports Optimum, Transformers, Python, Hugging Face Hub, PyTorch, and CUDA availability. |
| `export` | Parent command for exporter subcommands. | Backend children such as `onnx` are registered by partner packages, not by base Optimum alone. |

If `optimum-cli --help` lists `export` and `env` but `optimum-cli export --help` does not list `onnx`, the base CLI is working and the ONNX partner command is not registered in the active environment.

## CLI implementation model

The base CLI uses these concepts:

- `CommandInfo(name, help, subcommand_class, formatter_class=RawTextHelpFormatter)` describes a command.
- `BaseOptimumCLICommand` creates an argparse parser, can register subcommands, and defaults `run()` to printing help.
- `RootOptimumCLICommand` is the root parser for `optimum-cli`.
- `ExportCommand` is the base `export` parent command.
- `EnvironmentCommand` is the base `env` command.

Startup sequence:

1. Create the root parser.
2. Register base root commands (`export`, `env`).
3. Load selected namespace subpackages that declare commands through the `optimum_cli_subcommand` decorator.
4. Scan the `optimum.commands.register` namespace for lightweight registration modules.
5. Register each discovered command either under the root or under its requested parent command.
6. Parse arguments and run the resolved command service.

## Dynamic registration contract

Partner or extension packages can contribute CLI commands through the `optimum.commands.register` PEP 420 namespace.

Registration module requirements:

- The module lives in the `optimum.commands.register` namespace of an installed package.
- It should be lightweight at import time; expensive imports belong inside the command's `run()` method.
- The namespace should not contain an `__init__.py` file because it is intended to be a PEP 420 namespace.
- The module defines `REGISTER_COMMANDS`.

`REGISTER_COMMANDS` accepts either:

```python
REGISTER_COMMANDS = [MyRootCommand]
```

for a root command available as:

```bash
optimum-cli my-root-command
```

or:

```python
REGISTER_COMMANDS = [(MyExportCommand, ExportCommand)]
```

for a subcommand available as:

```bash
optimum-cli export my-export-command
```

Command classes must subclass `BaseOptimumCLICommand` and set a `COMMAND = CommandInfo(...)`. The parent command in a tuple must be a subclass of `BaseOptimumCLICommand`, such as `ExportCommand`.

Do not copy registration modules into an installed base package to diagnose a user environment. Use an isolated development install or a proper package that contributes the namespace.

## Why `optimum-cli export onnx` can be absent

Base Optimum provides the `export` parent only. ONNX export command registration is supplied by the ONNX partner package. Depending on the target workflow, install one of the ONNX-related optional distributions in the user environment, for example:

```bash
python -m pip install --upgrade --upgrade-strategy eager "optimum[onnx]"
python -m pip install --upgrade --upgrade-strategy eager "optimum[onnxruntime]"
```

Then re-run:

```bash
optimum-cli export --help
python scripts/probe_optimum_cli.py --run-env
```

If the command still does not appear, confirm the same Python environment is being used for `python`, `pip`, and `optimum-cli`, and check that the partner package contributes a module under `optimum.commands.register`.

## Safe CLI probe

Run the bundled probe to inspect command help and registration state without mutating package files:

```bash
python scripts/probe_optimum_cli.py
```

Useful options:

```bash
python scripts/probe_optimum_cli.py --run-env
python scripts/probe_optimum_cli.py --no-export-help
python scripts/probe_optimum_cli.py --json
```

The probe intentionally does not run any export command. It only executes help commands and, when requested, `optimum-cli env`.

## Optional native verification boundaries

The CLI checks that are safe in a base environment are root help and `env`. Export subcommands and pipeline tests require partner packages and often model cache or network access. Treat them as optional verification, not as required base-package coverage.

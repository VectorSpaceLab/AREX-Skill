# AG Bench

AG Bench (`agbench`) is AutoGen’s benchmark runner for repeated scenario execution under controlled initial conditions. It can initialize tasks, run benchmark JSONL scenarios, lint benchmark configuration, remove incomplete results, and tabulate previous results.

## Package and Commands

- Distribution: `agbench`.
- Console script: `agbench`.
- Verified installed fact for this skill: `agbench==0.0.1a1` imports and `agbench --help` works.
- Package metadata requires Python `>=3.8,<3.13` and depends on packages including `docker`, `openai`, `huggingface_hub`, `azure-identity`, `pandas`, `scipy`, and `tabulate`.

Top-level commands from the CLI source:

- `agbench run`: run benchmark scenario files.
- `agbench tabulate`: summarize results from previous runs.
- `agbench lint`: lint benchmark configuration.
- `agbench remove_missing`: remove result folders with missing outputs.
- `agbench --version`: print AutoGenBench version.
- `agbench --help`: print top-level help.

## Safe Help-Only Workflow

Use this when the user wants to inspect capabilities without Docker, credentials, providers, or network calls:

```bash
agbench --help
agbench run --help
agbench tabulate --help
agbench lint --help
agbench remove_missing --help
```

These commands should only display help and should not run scenarios. If the command is missing, check whether the environment’s script directory is on `PATH` or run through the same interpreter used for installation.

## Benchmark Execution Safety

`agbench run` is not a harmless command. It may:

- Build or use Docker images and containers by default.
- Read provider credentials from `OAI_CONFIG_LIST`, an `OAI_CONFIG_LIST` file, `OPENAI_API_KEY`, or benchmark-specific `ENV.json`.
- Download or initialize task data depending on the benchmark setup.
- Execute generated code and write result directories.
- Use network services, model providers, or Docker daemon access.

Do not run `agbench run` unless the user explicitly approves Docker/provider/network behavior and has prepared credentials and an output location.

## Configuration and Credentials

Common inputs:

- Scenario JSONL files under a benchmark’s `Tasks` directory.
- Optional `--config` pointing to an environment variable name or credentials file for `OAI_CONFIG_LIST`.
- Optional `ENV.json` for benchmark-specific variables such as search keys or provider selection.
- Optional `--requirements` for extra Python requirements to install before scenario execution.
- Optional `--docker-image` to choose the Docker image.
- `--native` to disable Docker, which is strongly discouraged because it runs benchmark code directly on the host environment.

Keep secrets out of generated logs, result directories, and committed configuration files.

## Results and Tabulation

Benchmark outputs are organized as nested result directories by scenario, task id, and instance id. Result folders commonly include console logs, timestamp/version data, per-agent message logs, and generated code/artifacts.

Use `agbench tabulate <results-dir>` only after a run has completed and the results directory is known. Tabulation reads existing result files; it should not call model providers, but it may fail if the directory layout is incomplete.

## Lint First

For new or modified benchmark scenarios, prefer:

```bash
agbench lint --help
agbench lint <scenario-or-directory>
```

Linting is safer than running. Still review whether the linter reads local files, expects benchmark-relative paths, or emits output into the working directory.

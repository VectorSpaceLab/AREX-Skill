# Troubleshooting AutoGen Tooling

## CLI Not Found

Symptoms:

- `agbench: command not found`, `autogenstudio: command not found`, or `m1: command not found`.
- Import succeeds but console script is unavailable.

Actions:

1. Check the package is installed in the active interpreter: `python -m pip show agbench autogenstudio magentic-one-cli`.
2. Check the script directory for the active interpreter is on `PATH`.
3. Try module/import metadata checks with the active interpreter before changing environments.
4. Reinstall only after confirming compatibility boundaries in `compatibility.md`.

## Python Version Constraints

- AutoGen root guidance requires Python 3.10 or later for modern libraries.
- `agbench` metadata allows `>=3.8,<3.13`.
- `magentic-one-cli` requires `>=3.10`.
- Studio metadata allows `>=3.9`, but its AutoGen package pins are the more important boundary.

If `pip` refuses to install, check both Python version and dependency ranges.

## Dependency Conflicts

Common conflict:

- Existing env has `autogen-agentchat==0.7.5`, `autogen-core==0.7.5`, `autogen-ext==0.7.5`.
- `magentic-one-cli==0.2.4` wants `autogen-agentchat>=0.4.4,<0.5` and `autogen-ext[...]>=0.4.4,<0.5`.
- Studio metadata wants AutoGen packages `<0.7`.

Fixes:

- Do not force-install with dependency overrides into the same env unless debugging a disposable environment.
- Create a separate environment for Studio or `m1`.
- Keep modern AutoGen application environments aligned on one version line.
- Use `python -m pip check` after any install.

## Studio Server and Database Issues

Symptoms:

- Port already in use.
- App starts but cannot read/write the app directory.
- Database URL errors, migration errors, or PostgreSQL authentication failures.
- Browser opens but backend endpoints fail.

Actions:

1. Run only `autogenstudio --help` and `autogenstudio version` as safe checks.
2. Choose an explicit disposable `--appdir` for experiments.
3. Use SQLite first unless the task specifically requires PostgreSQL.
4. Verify the port is free and host binding is loopback unless remote access is required.
5. Treat `--upgrade-database` as a schema-changing action; back up existing app data first.

## AG Bench Docker, Credential, and Network Issues

Symptoms:

- Docker daemon unavailable or image build fails.
- Missing `OAI_CONFIG_LIST`, `OPENAI_API_KEY`, or benchmark-specific `ENV.json` keys.
- Benchmark initialization downloads data and fails offline.
- `--native` works differently or damages the host environment.

Actions:

1. Start with `agbench --help`, subcommand help, and `agbench lint` where possible.
2. Confirm Docker is installed, running, and approved for the workspace.
3. Confirm provider credentials are intentionally supplied and not logged.
4. Prefer Docker execution; use `--native` only in a disposable environment.
5. Set output/result directories deliberately and inspect disk space before repeated runs.

## Result Directory Problems

Symptoms:

- `agbench tabulate` cannot find results.
- Runs are mixed across scenarios or repeated attempts.
- Cleanup commands remove more than expected.

Actions:

- Record the benchmark working directory before running.
- Use unique output directories per experiment when supported.
- Tabulate only known result roots.
- Review `remove_missing` help before cleanup; do not run cleanup blindly.

## Magentic-One CLI Runtime Issues

Symptoms:

- `m1` imports fail because package versions do not match.
- `m1` starts but model client loading fails.
- Docker executor fails or writes into an unsafe working directory.
- Human input blocks automation.

Actions:

1. Resolve package versions first; `m1` is not compatible with modern 0.7.x packages according to its metadata.
2. Use `m1 --sample-config` before writing a real config.
3. Verify provider credentials outside version-control files.
4. Run from a disposable working directory if Docker code execution is enabled.
5. Decide whether human-in-the-loop mode is desired before using `--no-hil`.

## Maintenance-Mode Decisions

If the task asks for a new production tool, benchmark platform, or UI built from scratch, point the user to Microsoft Agent Framework. If the task is existing AutoGen maintenance, keep the solution minimal, version-pinned, and explicit about the risks of old tooling.

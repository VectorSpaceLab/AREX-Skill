# `scl` command reference

This reference distills the Click command tree and live help observed for the
SMARTS 2.0.1 package. Always rerun the installed help because command behavior
can vary by release:

```bash
scl --help
scl scenario --help
scl run --help
```

## Command tree

```text
scl
├── benchmark
│   ├── list
│   └── run
├── diagnostic
│   └── run
├── envision
│   └── start
├── run
├── scenario
│   ├── build
│   ├── build-all
│   ├── clean
│   └── replay
├── waymo
│   ├── export
│   ├── overview
│   └── preview
└── zoo
    ├── build
    ├── install
    └── manager
```

The package entry point is `scl=cli.cli:scl`. The following are the verified
help signatures; use `--help` on a leaf before copying a command into a script.

| Command | Arguments/options | Effect and safety |
|---|---|---|
| `scl run <script> [SCRIPT_ARGS...]` | `--envision`; `-p, --envision_port TEXT` | Runs a Python experiment child. With `--envision`, starts a server on the selected port (default 8081), waits briefly, and opens a browser. The process group is cleaned up when the command exits; use only in an isolated run. |
| `scl scenario build <scenario>` | `--clean`; `--seed INTEGER` (default 42) | Generates one scenario. `<scenario>` must exist. `--clean` first removes generated artifacts and is destructive to derived files, not a read-only check. |
| `scl scenario build-all <scenarios...>` | `--clean`; `--seed INTEGER` (default 42) | Generates all scenarios below the supplied directories. Scope the arguments explicitly. |
| `scl scenario clean <scenario>` | none | Removes previously generated scenario artifacts. Confirm the path and preserve source files before use. |
| `scl scenario replay` | repeatable `-d, --directory`; `-t, --timestep FLOAT` (default 0.01); `--endpoint` (default `ws://localhost:8081`) | Finds `*.jsonl` records in each directory and sends them concurrently to an Envision websocket. It needs a reachable server and valid records; it does not start one. |
| `scl envision start` | `-p, --port INTEGER` (default 8081); `-c, --max_capacity FLOAT` (default 500 MB) | Starts the Envision web server and remains in the foreground. A port conflict is expected if another server owns the port. |
| `scl diagnostic run <scenarios...>` | no leaf options | Runs all diagnostic cases and writes a report. It is a performance measurement workflow, not a cheap health check; use the optional diagnostic extra and approved cases only. |
| `scl benchmark list` | `--benchmark-listing TEXT` | Lists benchmarks from the default or supplied listing. Treat a custom listing as untrusted input even for inspection. |
| `scl benchmark run <benchmark_id> <agent_locator>` | `--benchmark-listing TEXT`; `--auto-install` | Runs an integrated benchmark. `benchmark_id` may be `NAME==VERSION`; without a version, the latest listed version is selected. `--auto-install` can install requirements and must not be used on an untrusted listing. |
| `scl zoo build <policy>` | none | Changes into a policy directory, runs its `setup.py clean --all` and wheel build, then cleans again. It mutates the policy tree and needs packaging tools. |
| `scl zoo install <agent_path...>` | one or more existing paths | Runs `pip install .` in each local agent path. This changes the active environment; do not invoke as a probe. |
| `scl zoo manager [PORT]` | integer port (default 7432) | Starts the remote-worker manager in the foreground. It is a service, not a smoke test. |
| `scl waymo overview <tfrecord_file>` | existing file | Reads Scenario-proto records and prints scenario ID, timestamps, vehicles, and pedestrians. It is the safest Waymo command, but still needs the dataset and optional dependencies. |
| `scl waymo preview <tfrecord_file> <scenario_id>` | `--animate`; `--label_vehicles` | Plots one scenario and may require display/plotting support. It does not replace a renderer or simulator lifecycle check. |
| `scl waymo export <tfrecord_file> <scenario_id> <export_folder>` | none | Creates `<export_folder>/<scenario_id>/scenario.py`. Treat the export directory as a deliberate write target and validate generated data before building it. |

## Path and cwd rules

- Relative paths are interpreted by the process's current working directory,
  except diagnostic scenario names, which are resolved by the diagnostic module
  beneath its packaged diagnostic scenario directory. Use absolute or
  deliberately anchored paths in automation.
- `build`, `clean`, and `build-all` require paths that exist at Click validation
  time. A missing scenario fails before scenario construction.
- A scenario's source files and generated artifacts are different concerns.
  Build in a disposable copy when testing `--clean`; never use a repository
  root or valuable dataset as a scratch directory.
- The run command checks the experiment script path, then passes unparsed
  trailing arguments to that script. Put script options after the script path;
  if an option is accidentally consumed by Click, inspect `scl run --help` and
  use the script's own parser contract.
- `scl scenario replay -d A -d B` creates one replay worker per discovered
  JSONL file. An empty directory is not evidence that Envision is broken.

## Safe command progression

1. `python -m ...` import probe or `check_scl_help.py`.
2. Leaf `--help` and path existence checks.
3. Read-only listing/replay inspection with a disposable record directory.
4. A bounded build into a disposable output or copy.
5. Only then start a server, run a diagnostic, benchmark, or zoo workflow.

`--clean`, `zoo install`, `benchmark --auto-install`, Waymo export, and
long-lived `envision start`/`zoo manager` are never implicit prerequisites for
core CLI availability.

# Aim cross-cutting troubleshooting

Use this reference for package-level install/import, version, repository, cleanup, optional dependency, and service boundary issues. Use sub-skill troubleshooting files for workflow-specific details.

## Installation and import failures

### `import aim` fails

Check:

```bash
python -m pip show aim
python -m pip check
python -c "import aim; print(getattr(aim, '__version__', 'unknown'))"
```

Likely causes and fixes:

- The package is installed in a different Python environment. Run the import check with the same Python that will execute the user's code.
- The compiled storage dependency is missing or incompatible. Reinstall Aim for the target Python version instead of mixing package directories across environments.
- A local file or directory named `aim.py` or `aim/` shadows the installed package. Rename it or run from a neutral directory.
- Very new Python versions may be unsupported by compiled dependencies. Prefer a Python version documented or wheel-tested by Aim.

### `aim` CLI not found but import works

The console script may not be on `PATH`. Run:

```bash
python -m pip show aim
python -c "import sys, pathlib; print(pathlib.Path(sys.executable).parent)"
```

Then either add the environment's script directory to `PATH`, invoke the full executable path, or use the bundled `scripts/check_aim_environment.py` to confirm whether the CLI is beside the current Python.

## Version and dependency mismatches

Symptoms:

- `pip check` reports conflicting FastAPI, SQLAlchemy, Pydantic, numpy, Pillow, or web packages.
- UI/server imports fail after upgrading unrelated dependencies.
- SDK works in one environment but CLI fails in another.

Recovery:

1. Create a clean environment for Aim rather than repairing a heavily shared environment.
2. Install the base package first.
3. Add optional ML frameworks only when a selected integration needs them.
4. Re-run `python scripts/check_aim_environment.py --check-optional` from this skill to separate base Aim problems from optional integration gaps.

## Repository path confusion

Symptoms:

- Runs are created but the UI shows no data.
- Queries from a script return no runs.
- A command initializes a different `.aim` directory than expected.

Recovery:

- Use explicit paths everywhere:
  ```bash
  aim init --repo ./aim-repo
  aim up --repo ./aim-repo
  ```
  ```python
  from aim import Repo, Run
  repo = Repo.from_path("./aim-repo", init=True)
  run = Run(repo=repo)
  ```
- Avoid relying on the current working directory inside agents, notebooks, job schedulers, and tests.
- In remote tracking setups, distinguish the local Aim repository path on the server from the client URL used by training processes.

## Cleanup and temporary directories

Aim stores data in RocksDB-backed files. If a script deletes a temporary repository before all `Run` and `Repo` resources close, cleanup warnings or missing data can appear.

Safe pattern:

```python
run = None
repo = None
try:
    repo = Repo.from_path(str(repo_dir), init=True)
    run = Run(repo=repo, system_tracking_interval=None, capture_terminal_logs=False)
    run.track(1.0, name="smoke")
finally:
    if run is not None:
        run.close()
    if repo is not None:
        repo.close()
```

Only delete the repository directory after explicit closes have completed. The `tracking-sdk` smoke script includes a safer persistent-temp pattern.

## Optional integration imports

Many Aim adapters intentionally import their framework at module import time. Missing optional packages can produce errors such as:

- `This contrib module requires PyTorch Lightning to be installed`
- `This contrib module requires Transformers to be installed`
- `No module named 'tensorflow'`

Do not install all optional stacks by default. Use `framework-integrations` to choose between installing one specific framework dependency and falling back to direct `Run.track` instrumentation.

## Service/listener issues

### UI or server starts on the wrong address

Use explicit flags:

```bash
aim up --repo ./aim-repo --host 127.0.0.1 --port 43800
aim server --repo ./aim-repo --host 0.0.0.0 --port 53800
```

For reverse proxies, normalize base paths with a leading slash and no trailing slash. Route to `cli-and-services` for details.

### Remote client cannot connect

Check:

- Server process is running `aim server`, not only `aim up`.
- Training code uses a remote URL such as `aim://host:port` in `Run(repo=...)` or `Repo.from_path(...)`.
- Firewall/proxy/SSL/base-path settings match server flags.
- Certificates and keys are readable by the service process, but do not paste private keys into logs.

## Storage and maintenance risk

Storage commands can mutate or delete run data. Before running maintenance:

1. List target runs with `aim runs --repo <repo> ls`.
2. Record hashes and current repository path.
3. Back up the repository if the operation cannot be trivially reversed.
4. Prefer help/dry-run-like inspection first.
5. Avoid `-y` unless the user has explicitly accepted the action.

Use `cli-and-services/references/storage-and-run-maintenance.md` for command-level guidance.

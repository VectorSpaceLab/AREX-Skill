# Submission format

A packaged job contains:

```text
code/
run.sh
config.yaml
```

Folder Python jobs copy the whole folder under `code/`. If `code/pyproject.toml` exists, generated `run.sh` runs `uv sync` before installing PySyft and dependencies. Single-file jobs install dependencies with `uv pip install` and run the entrypoint from `code/`.

Use `scripts/inspect_job_submission.py` to validate shape without executing code.

# Operational checklist

## Before a run

- [ ] `python --version` is 3.10 or 3.11, or the chosen release documents another supported version.
- [ ] `python -m pip show rdagent` and `import rdagent` resolve to the intended installation.
- [ ] `python -m pip check` passes.
- [ ] The exact subcommand's `--help` output was captured.
- [ ] Provider variables, data roots, Docker/Java/system tools, and GPU expectations are explicit.
- [ ] Output and log directories are disposable and writable.
- [ ] A small fixture or dry-run path exists.

## After a run

Record the command, package/revision, resolved settings (with secrets redacted), start/end times, output path, evaluator metric, and first traceback if it failed. Distinguish a clean CLI exit from a valid experiment result.

## Safe evidence commands

```bash
python -m pip check
python -c "import rdagent; print(rdagent.__file__)"
rdagent --help
rdagent health_check --no-check-env --no-check-docker
```

Avoid using `pip freeze` or environment dumps as a substitute for the specific dependency/import check; save them only as supplementary evidence.

---
name: dvc
description: "Use the DVC repository skill for data versioning, pipelines,
  experiments, remotes/cache, metrics/params/plots, Python API usage, and DVC
  codebase maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DVC Repo Skill

Use this skill when a task names DVC, Data Version Control, `dvc` CLI commands, the `dvc` Python package, DVC pipeline files, DVC experiments, or maintenance of the DVC codebase itself.

## Install And Smoke Check

- End-user install: `pip install dvc` for core local/HTTP workflows.
- Optional remotes: install only the needed extra, such as `pip install 'dvc[s3]'`, `pip install 'dvc[gs]'`, `pip install 'dvc[azure]'`, `pip install 'dvc[ssh]'`, `pip install 'dvc[gdrive]'`, `pip install 'dvc[webdav]'`, `pip install 'dvc[webhdfs]'`, `pip install 'dvc[hdfs]'`, or `pip install 'dvc[oss]'`.
- Development install: use an editable checkout and install test/lint extras only when maintaining DVC itself.
- Minimal checks: `python -c "import dvc; print(dvc.__version__)"`, `dvc --help`, and `dvc version`.

## Route By Task

- `sub-skills/data-and-pipelines/SKILL.md`: use for `dvc init`, `dvc add`, `.dvc` files, `dvc.yaml`, `dvc.lock`, `dvc stage add`, `dvc repro`, `dvc status`, `dvc diff`, `dvc dag`, `.dvcignore`, and safe pipeline planning.
- `sub-skills/experiments/SKILL.md`: use for `dvc exp run/show/diff/apply/branch/save/push/pull/remove/rename/clean`, queued sweeps, Hydra/set-param runs, and experiment table troubleshooting.
- `sub-skills/remotes-and-cache/SKILL.md`: use for `dvc remote`, storage extras, `push`, `pull`, `fetch`, cloud status, cache configuration, `gc`, `unprotect`, `import-url`, `get-url`, and missing backend/credential failures.
- `sub-skills/metrics-params-plots/SKILL.md`: use for `dvc metrics`, `dvc params`, `dvc plots`, stage metric/plot/param declarations, JSON/Markdown/Vega reporting, and API summaries of metrics or params.
- `sub-skills/python-api/SKILL.md`: use for `dvc.api.open`, `read`, `get_url`, `DVCFileSystem`, `Repo` automation, and Python exception handling around DVC data access.
- `sub-skills/repo-development/SKILL.md`: use only when editing or reviewing the DVC source repository, selecting focused tests, changing CLI command internals, updating package metadata, or maintaining contribution workflows.

## Cross-Cutting References

- Read `references/troubleshooting.md` for install/import, optional extra, no-repo, remote/cache, and command-routing failures that span several sub-skills.
- Read `references/repo-provenance.md` before deciding whether this skill matches a current DVC checkout or should be refreshed.
- Read `references/repo-routing-metadata.json` only when importing this skill through DisCo's managed repo-skills-router.
- Run `scripts/check_dvc_install.py --help` for a safe local package and CLI smoke-check helper.

## Decision Pattern

1. Decide whether the task is end-user DVC usage, Python API usage, or DVC codebase maintenance.
2. Route to the most specific sub-skill before reading long references.
3. Prefer dry-run/help/config/API inspection before commands that mutate workspace data, remote storage, cache, Git refs, or experiment queues.
4. Install only the optional remote/backend extra required by the task; do not default to broad `dvc[all]`.
5. For original DVC repository tests or examples, use `repo-development` guidance; public runtime workflows should not depend on the original checkout.

## Safety Boundaries

- Treat cloud remotes, Studio, network URLs, credentials, and large data transfers as opt-in operations.
- Use `dvc repro --dry`, helper scripts, or CLI `--help` before expensive or destructive workflow changes.
- Do not assume optional remote backends are installed just because core `dvc` imports.
- Do not use private `dvc.*` internals for user projects when a public CLI, `dvc.api`, or `Repo` method covers the task.

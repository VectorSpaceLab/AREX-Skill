# Metaflow Cross-Cutting Troubleshooting

## Install or import fails

Symptoms:
- `ModuleNotFoundError: No module named 'metaflow'`
- `metaflow` command is missing from the shell
- `pip check` reports broken requirements

Actions:
1. Install the public package in the environment that will run the flow:
   ```bash
   python -m pip install metaflow
   python -m pip check
   python - <<'PY'
   import metaflow
   print(metaflow.__version__)
   PY
   ```
2. If the task is repository development, read `sub-skills/repo-maintenance/` before changing code or installing dev dependencies.
3. If the failure occurs inside a Metaflow step environment, read `sub-skills/dependency-environments/` because the step may need `--environment=conda|pypi|uv` or datastore-specific pinned libraries.

## Username cannot be determined

Metaflow flow CLIs may fail in non-login automation when no username environment variable is visible. Set a harmless value for local smoke tests:

```bash
export USERNAME=${USERNAME:-disco}
```

For organization deployments, prefer the organization's supported identity mechanism rather than hard-coding a personal username.

## Version command confusion

- Correct for a flow script: `python flow.py version`.
- Incorrect: `metaflow --version`.

## Optional service, cloud, and GPU claims

A CPU import does not prove AWS Batch, S3, Kubernetes, Argo, Airflow, Azure, GCP, devstack, or GPU/PyTorch execution. For these workflows, verify credentials, datastore roots, service URLs, clusters, container images, and hardware before claiming the backend is ready.

## Source checkout dependency mistake

Generated skill guidance must not say to open or run original repository docs, tests, examples, notebooks, or scripts. Use bundled files in this skill tree. If a needed recipe is missing, treat it as a skill gap and extend or refresh the skill.

# Towhee Troubleshooting

## Purpose

Use this root troubleshooting guide for install/import/cache/optional-dependency issues that cut across Towhee workflows. For workflow-specific failures, use the nearest sub-skill troubleshooting reference.

## Import fails: `No module named 'towhee'`

Likely causes:

- Towhee is not installed in the active Python environment.
- The notebook/kernel or shell is using a different Python than the one where Towhee was installed.
- Editable install was performed from a source checkout that is no longer available.

Recovery:

1. Run `python -m pip show towhee` and confirm the distribution exists.
2. Run `python -c "import sys; print(sys.executable)"` in the same shell or kernel.
3. Install into that exact environment: `python -m pip install towhee`.
4. Restart notebooks/kernels after installing.

## Import fails: `No module named 'pkg_resources'`

Towhee 1.1.x imports `pkg_resources`, historically provided by setuptools. Newer packaging environments may remove it.

Recovery:

```bash
python -m pip install 'setuptools<81'
python -c "import towhee; print('ok')"
```

If the task is packaging-sensitive, pin this in the user's environment file or installation instructions.

## Pydantic or service model errors

Towhee 1.1.x was verified with Pydantic v1 during skill creation, and the repository's own test requirements use `pydantic<2`. If `APIService`, service IO models, or Pydantic `BaseModel` validation behaves unexpectedly:

1. Check `python -m pip show pydantic`.
2. Prefer `python -m pip install 'pydantic<2'` for old Towhee service workflows unless the user must stay on Pydantic v2.
3. Re-run `python scripts/check_towhee_environment.py --skip-cli` from this skill tree or a copied helper.

## Hub operator or AutoPipes download fails

Symptoms:

- Operator/pipeline not found.
- Network timeouts while loading an operator or predefined pipeline.
- Dependency prompts or downloads happen during a pipeline call.
- Docs mention deleting `.towhee` when dependencies are not automatically installed.

Recovery:

1. Reproduce with a local lambda pipeline first to isolate graph syntax from Hub/network problems.
2. Pin Hub operator revisions when reproducibility matters: `ops.namespace.operator().revision('tag-or-branch')`.
3. Clear or move the user's Towhee cache only with approval because it may remove downloaded operators/models.
4. If the environment is offline, write the pipeline around local callables or preinstalled operators instead of relying on Hub resolution.
5. If optional dependencies are missing, install only the operator's required packages rather than all Towhee test/model extras.

## CLI help emits a deprecation warning

Towhee help commands may print a `pkg_resources is deprecated` warning while still exiting successfully. Treat it as non-fatal if the command output still shows `init` and `server` subcommands. If the warning becomes an import error, use the setuptools pin above.

## Optional training/model imports auto-install packages

Towhee's dependency-control helpers may try to install missing optional packages when importing training/model code. This can unexpectedly install PyTorch/TorchVision/TorchMetrics/YAML dependencies.

Recovery:

- Import `towhee.trainer` only in an isolated environment when optional installs are acceptable.
- For config templates that do not need Torch, use the bundled `training-and-models/scripts/training_config_template.py` without `--check-imports`.
- For actual training, decide CPU vs CUDA and install the matching PyTorch stack deliberately before importing trainer modules.

## Live services, Docker, and Triton side effects

Do not use live HTTP/GRPC/Triton/Docker workflows as routine checks. They may bind ports, start long-lived processes, create large Docker images, or require GPU/CUDA.

Safe alternatives:

- Use `serving-and-triton/scripts/api_service_smoke.py` to validate `APIService` object construction.
- Use `towhee server --help` rather than starting a server.
- Plan Docker/Triton commands with explicit image names, CUDA version, port mappings, cleanup commands, and user approval before running.

## Where to go next

- Pipeline graph errors: `sub-skills/pipeline-programming/references/troubleshooting.md`.
- Operator registry, Hub, and CLI errors: `sub-skills/operator-hub-and-cli/references/troubleshooting.md`.
- Service/Triton errors: `sub-skills/serving-and-triton/references/troubleshooting.md`.
- DataCollection/media wrapper errors: `sub-skills/data-utilities/references/troubleshooting.md`.
- Trainer/model-zoo errors: `sub-skills/training-and-models/references/troubleshooting.md`.

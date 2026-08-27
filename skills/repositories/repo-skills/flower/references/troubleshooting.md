# Flower troubleshooting

This cross-cutting reference covers the most common Flower, flwr-datasets, and
repo-level failure modes that affect multiple sub-skills.

## First checks

1. Run `scripts/check_flower_install.py` to confirm the installed packages,
   import paths, safe CLI help/version output, and a tiny dataset smoke.
2. Read `references/repo-provenance.md` to confirm the skill still matches the
   checkout you are using.
3. If the task is maintainer-oriented, switch to
   `sub-skills/repository-maintenance/` for the repo command family.

## Install and import mismatch

**Symptoms**

- `import flwr` or `import flwr_datasets` fails.
- CLI help works, but the package import comes from the wrong environment.
- `pip check` reports broken requirements.

**Likely causes**

- The user is in a runtime-only environment, not a repo contributor environment.
- The wrong Python interpreter is active.
- A package was installed without the matching editable checkout or distribution.

**Recovery**

- Re-run the minimal install smoke with `scripts/check_flower_install.py`.
- Confirm the interpreter is the isolated Python 3.11 environment you intended.
- Install only `flwr` and `flwr-datasets` for runtime inspection unless the task
  explicitly needs simulation, extras, or maintainer tooling.

## Optional dependency gaps

**Symptoms**

- A simulation or example workflow reports a missing extra such as Ray, torch,
  TensorFlow, JAX, MLX, or another framework package.
- Example dependencies differ sharply between example directories.

**Likely causes**

- The requested workflow depends on an optional extra that was intentionally not
  installed in the minimum inspection environment.
- The example uses a framework-specific dependency stack that is larger than the
  base runtime packages.

**Recovery**

- Route the request to the relevant sub-skill and read the example catalog
  before expanding the environment.
- Install only the extra or framework stack needed by the selected workflow.
- If the workflow is optional, keep it documented as unverified rather than
  claiming coverage.

## Local SuperLink / simulation state issues

**Symptoms**

- Local `flwr run` or `flwr list/log/stop` behavior looks inconsistent.
- SQLite locking errors appear on a network filesystem.
- `flower-supernode --help` or other CLI commands show an INFO startup line.

**Likely causes**

- The managed local SuperLink is using on-disk state on a slow or shared file
  system.
- A custom Flower Configuration profile is not the one the user expects.
- The CLI help path emits a startup log line before the usage text.

**Recovery**

- Use the simulation-and-deployment sub-skill for profile selection, local
  SuperLink behavior, and runtime troubleshooting.
- If persistence is a problem on the current filesystem, switch to the
  in-memory local profile only when the loss of run history is acceptable.
- Treat help output plus the startup INFO line as a verified behavior, not as a
  failure by itself.

## Flower Datasets download or partitioning problems

**Symptoms**

- Dataset downloads fail because the network is unavailable.
- A partitioner errors on invalid split names or impossible partition settings.
- Local CSV/JSON/image/audio inputs are not partitionable as-is.

**Likely causes**

- Hugging Face access is required for the selected dataset.
- The data layout does not match the partitioner or preprocessor.
- A required `vision` or `audio` extra is missing.

**Recovery**

- Use the datasets-and-examples sub-skill and its tiny in-memory smoke first.
- Confirm the split name, partitioner arguments, and any required casting or
  preprocessor step before attempting a larger dataset.
- Keep network-dependent dataset downloads out of the minimum environment when
  the workflow can be demonstrated with a tiny local fixture.

## Maintainer command failures

**Symptoms**

- Generated protobuf files differ from the source `.proto` definitions.
- Alembic checks fail after a schema change.
- Docs or contributor commands fail because the dev toolchain is missing.
- Public imports work only from implementation modules.

**Likely causes**

- A maintainer workflow was executed in the runtime inspection environment
  instead of a contributor environment.
- Generated files were edited directly instead of regenerated.
- A public symbol was not added to the package `__all__` surface.

**Recovery**

- Switch to the repository-maintenance sub-skill.
- Use the package-local dev commands and generator-first workflows described in
  that sub-skill before editing generated files.
- For export mistakes, run the bundled public-API check and add import-path tests
  near the owning package.

## When to stop

Stop and ask for help when the fix requires:

- credentials or private services,
- a missing GPU or other unavailable backend,
- a large framework-specific dependency stack that the task did not request,
- or a maintainer environment mutation that may break the user's existing
  setup.

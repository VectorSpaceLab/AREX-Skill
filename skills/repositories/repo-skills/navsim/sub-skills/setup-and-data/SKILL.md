---
name: setup-and-data
description: "Set up NAVSIM v2 dependencies and workspace data, select a
  supported split, validate paths, and use the Scene, Frame, AgentInput,
  SensorConfig, and SceneLoader contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# NAVSIM setup and data

Use this route before training, evaluation, or submission work. It is a
read-only setup and data contract: it may inspect an existing environment and
workspace, but it must not download archives, delete partial downloads, create
large caches, train, score, or upload anything by default.

## Route

1. Read [installation.md](references/installation.md) for the Python/dependency
   baseline and environment variables.
2. Read [data-layout.md](references/data-layout.md) to map a selected split to
   logs, original sensors, synthetic scenes/sensors, maps, and experiment/cache
   roots. Treat original and synthetic sensor/log/cache roots as different
   resources.
3. Run the bundled, side-effect-free [workspace validator](scripts/validate_workspace.py)
   before a data-dependent runner:

   ```bash
   python scripts/validate_workspace.py --split mini
   ```

   A successful run ends with `VALIDATION PASSED`; failures identify the
   missing variable or path and exit nonzero. Use `--help` for split names and
   `--json` for machine-readable diagnostics. The validator does not read a
   project config, download data, or create directories.
4. Read [data-api.md](references/data-api.md) when constructing a loader or
   agent input. Use no-sensor loading first when checking metadata/filtering;
   enable only the camera history and/or LiDAR iterations actually required by
   the agent.
5. For failures, use [troubleshooting.md](references/troubleshooting.md) and
   preserve the distinction between an unavailable optional backend and a
   broken required data contract.

## Split guardrails

- `mini`, `trainval`, and `test` are OpenScene log/sensor splits.
- `navmini` and `navtrain` are filtered NAVSIM views over `mini` and
  `trainval`; `navtest` and the v2 two-stage test views are filtered views over
  `test`. A filtered view does not imply a separate complete log root.
- `navhard_two_stage`, `warmup_two_stage`, and
  `private_test_hard_two_stage` require synthetic/competition assets in
  addition to the appropriate original assets. Select their matching bundle;
  do not silently reuse `navhard_two_stage` assets for warmup or private data.
- Never use `test`, `navtest`, `navhard_two_stage`, `warmup_two_stage`, or
  `private_test_hard_two_stage` as training data for a competition submission.
  See the split matrix in [data-layout.md](references/data-layout.md).

The nearest references are the authoritative distilled operating context for
this sub-skill. They intentionally describe interfaces and layouts rather than
asking a later agent to open or execute source-checkout files.

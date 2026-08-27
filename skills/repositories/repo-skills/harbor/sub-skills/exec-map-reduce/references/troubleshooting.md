# `harbor exec` troubleshooting

Use `harbor exec --help` and `--print-config` as the first diagnostics. They
are read-only with respect to agent/model execution. The errors below are
classified by the stage that can fail.

## Command and mode errors

### `harbor: command not found`

The installed CLI is not on `PATH`. Check the installation/environment that is
supposed to own Harbor, then rerun `harbor --version`. Do not infer a module
entry point or silently install a large optional environment while debugging a
run.

### `--config cannot be combined with flags mode options`

`--config` is an exclusive mode. Remove all compilation/job/reducer flags and
put their values in the config file, or remove `--config` and use a complete
flags-mode invocation. `--print-config` is compatible with either mode and is
the right way to inspect the selected form.

### Unsupported config suffix

Only `.yaml`, `.yml`, `.json`, and `.toml` are loaded by the CLI. Rename the
file or convert it; do not pass a generic extension and expect content sniffing.
A missing config file is reported as a file error.

### `Invalid exec config` / extra inputs are not permitted

Validate the exact nested model shape. `ExecConfig`, `ExecMapConfig`,
`ExecReduceConfig`, and `ExecJobConfig` forbid unknown fields. In particular:

- `map` is required and contains `compile` and optional `job`.
- `reduce`, when present, contains `task` and optional `job`.
- `tasks`, `datasets`, and compile artifacts do not belong under a job section.
- A reducer requires non-empty `map.compile.artifacts`.
- A compile instruction has exactly one of `text` or `path`.
- A compile environment has at most one of `path` or `paths`.
- A compile verifier has exactly one of `path` or `auto_verifier`.
- A reducer task needs `output_dir` and exactly one reducer instruction source.

Use the live fields reported by this small inspection command when a local
installation has drifted:

```bash
python - <<'PY'
from harbor.models.exec import (
    ExecConfig, ExecJobConfig, ExecMapConfig, ExecReduceConfig,
    ExecReduceEnvironment, ExecReduceTaskConfig,
)
for model in (ExecConfig, ExecMapConfig, ExecJobConfig, ExecReduceConfig,
              ExecReduceTaskConfig, ExecReduceEnvironment):
    print(model.__name__, list(model.model_fields))
PY
```

### Missing task source

Flags mode requires `--instruction`, `--instruction-path`, or
`--task-template`. A template used without either instruction option must be a
directory containing `instruction.md`. A reducer is implied by reducer options,
but it separately requires `--reduce-instruction`/`--reduce-prompt` or
`--reduce-instruction-path`; a reducer artifact option alone is not enough.

### Mutually exclusive instruction options

`--instruction`/`--prompt` cannot be combined with
`--instruction-path`. The reducer has the same rule for its inline and path
forms. Pick one source and confirm it in `--print-config`.

## Path scan and compilation errors

### Unexpected number of map tasks

Check the resolved `map.compile.environments` in `--print-config`:

- One directory or one glob scans by default.
- Multiple paths do not scan by default and become one environment.
- `--scan` flattens matches from all inputs; directory scanning considers only
  immediate child directories.
- `--no-scan` disables the single-directory/single-glob default.
- Matches are sorted per input, de-duplicated by resolved path, and then capped
  by `--limit`.

Use `--limit N` only with scanning. A limit of less than 1 is rejected by the
CLI. An empty directory, non-matching glob, missing path, or scan with no path
is an error rather than an empty job.

### `--limit only applies to scanned paths`

Add `--scan`, remove `--limit`, or explicitly use `--no-scan` without a limit.
Do not use a limit as a general cap on a grouped multi-file environment.

### Input path pattern did not match anything / path does not exist

Resolve globs from the caller's current working directory and quote shell glob
patterns when the CLI—not the shell—should perform expansion. Confirm that
paths are readable files/directories. A compile environment `paths` glob is
also expanded at compile time and fails if it matches nothing.

### `Compiled task is not a valid task directory`

The compiler copied the template/inputs but could not produce Harbor's minimum
task layout. Check template contents, instruction source, environment paths,
and verifier paths. A template with a `tests/` directory must include an
OS-compatible verifier script; otherwise compilation rejects it. Run
`--print-config` first to catch path and source mistakes without compiling.

### Relative artifact is collected from the wrong location

Artifact paths are container paths. In flags mode, an inferred relative mention
is joined to the configured workdir (`/app` by default), while an absolute
mention remains absolute. For example, `reports/summary.txt` with workdir
`/workspace` becomes `/workspace/reports/summary.txt`. `-f/--artifact` replaces
inferred artifacts, so it is the corrective override. The agent must write at
the artifact's container source path, not at its host-side destination.

## Artifact and verification errors

### Inferred artifact list is empty or contains a false positive

Only inline instruction text is scanned. The matcher recognizes a conservative
set of common file extensions and known dotfiles, avoids common version/domain
false positives, and does not inspect `--instruction-path` contents. It also
cannot reliably infer extensionless names such as `Makefile` or `Dockerfile`.
Use explicit `-f` or `--reduce-artifact`, then verify the exact list in printed
config. Do not rely on an artifact mention in an external prompt file.

### A required artifact is missing

The generated auto-verifier performs existence checks after the trial. Confirm
that the instruction names the same container path as the artifact, that the
agent writes it in the task workdir/container, and that a directory artifact is
created when a directory is expected. If using an `ArtifactConfig`, remember
that `destination` controls host collection placement; it does not change the
container `source` the agent must produce.

### Reward promotion fails

The reward source must exist and contain a **non-empty JSON object**. Every key
must be a string and every value must be an `int` or `float`; booleans are not
accepted as numbers. A successful generated verifier copies the validated
object to `/logs/verifier/reward.json`; failure writes a zero verifier result.
The reward source is also collected as a normal artifact.

Do not pair `--reward-artifact` or `--reduce-reward-artifact` with
`--disable-verification`. If a config sets `auto_verifier.reward_artifact`,
ensure the source is included in `artifacts` or understand that the compiler
adds it to the generated required list.

### Verifier unexpectedly disabled

In flags mode, verification is enabled when generated artifact checks exist or
a supplied template has a `tests/` directory. `--disable-verification` forces
both generated compile verifiers and the flags-generated job verifier off. In
config mode, inspect both compile `verifiers` and the phase `job.verifier`; a
config file does not inherit flags-mode generation behavior.

## Reducer and persistence errors

### `reduce requires map.compile.artifacts`

Add at least one map artifact under `map.compile.artifacts` (strings or
`ArtifactConfig` objects). Prompt inference may produce this in flags mode, but
config mode has no prompt inference step; declare it explicitly.

### `Cannot reduce a map job with no trial results`

The map job returned no trials. Check map task generation, job selection, and
agent execution results before attempting reduction. This is distinct from a
trial that ran but did not collect artifacts.

### `Cannot reduce a map job with no trial artifacts`

The map job had trial results, but none had an artifacts directory. Check the
map artifact declarations, artifact existence, trial result paths, and whether
verification/collection actually completed. Per-trial missing artifact
folders are skipped; the reducer needs at least one staged folder.

### Reducer cannot find map outputs

The executor injects map artifacts under the reducer environment's
`artifacts/` directory. With the default `/app` workdir, read
`/app/artifacts/<ordinal>-<slug>/...`. The reducer is compiled exactly once;
there is no reducer path scan. Do not expect original host paths or the map
trial's full absolute URI inside the reducer.

### Compiled tasks disappeared

In flags mode without `--tasks-dir`, the CLI replaces the temporary compile
output in the execution copy and removes it after the run. This is intentional.
Use `--tasks-dir PATH` to retain map and reducer task directories for inspection.
Job results are separate and default to `jobs`; use `--jobs-dir` to place them
elsewhere. In config mode, task output is not automatically rewritten or
cleaned by this CLI path, so its configured directory is the durable source of
compiled tasks.

### Job location is not where expected

Flags mode defaults both phases to the relative `jobs` directory, while phase
names are timestamped `...-map` and `...-reduce` unless overridden. The CLI
prints each actual job directory after execution. Use `--print-config` to
inspect names and `jobs_dir`; do not confuse temporary task output with job
persistence.

## Provider and agent boundary

A parsed `--env` or `EnvironmentConfig` only selects a Harbor environment. It
does not prove that Docker, a cloud SDK, credentials, an agent binary, model
credentials, or network access are available. Diagnose those as a later
execution-stage issue. Keep preflight checks read-only, and use a map-only
config with `--print-config` to isolate config errors from provider/agent
failures.

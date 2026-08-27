# `harbor exec` CLI reference

This reference describes the installed Harbor `0.22.0` help surface and the
corresponding flags-mode construction behavior. Re-run `harbor exec --help`
before relying on an experimental option after an upgrade.

## Mode and inspection

```text
harbor exec --config EXEC_CONFIG [--print-config]
harbor exec [flags-mode options] [--print-config]
```

- `-c, --config PATH` loads an `ExecConfig` from YAML, JSON, or TOML. It cannot
  be combined with flags-mode options. The CLI checks this before loading the
  file; `--print-config` is an inspection option and can be used with config
  mode.
- `--print-config` prints resolved `ExecConfig` JSON, including inferred
  artifacts, and exits before the experimental warning, compilation, or job
  execution.
- Normal execution prints the experimental warning first, then map results and
  job locations; with a reducer it prints a second reduce-results section.

## Task compilation flags

| Flag | Meaning and verified behavior |
| --- | --- |
| `-p, --path TEXT` | File, directory, or glob to copy into each compiled task environment; repeatable. |
| `--scan/--no-scan` | Fan out into one task environment per glob match or per immediate child directory. An explicit `--no-scan` groups the supplied paths into one environment. |
| `-l, --limit INTEGER` | Maximum scanned matches; must be at least 1 and is invalid unless scanning is enabled. |
| `-i, --instruction TEXT`; `--prompt TEXT` | Inline map instruction. `--instruction` and `--instruction-path` are mutually exclusive. |
| `--instruction-path PATH` | File containing the map instruction; it is copied when compilation runs. Its contents are not read for artifact inference in flags mode. |
| `--task-template PATH` | Optional Harbor task-template directory. If it is the only task-source option, it must contain `instruction.md`. |
| `--image TEXT` | Compiled map-task image; flags-mode default is `ubuntu:latest`. |
| `--workdir TEXT` | Compiled map-task workdir; flags-mode default is `/app`. Relative inferred artifact names are resolved under this workdir. |
| `-f, --artifact TEXT` | Artifact path to collect after each map trial; repeatable. Any supplied list replaces, rather than extends, prompt-inferred artifacts. |
| `--reward-artifact TEXT` | Artifact path to collect and promote to `/logs/verifier/reward.json` after verification. It is normalized relative to the map workdir. |
| `--disable-verification` | Disables generated existence-only artifact verification and template verification. It cannot be combined with a map reward-artifact option or a reducer reward-artifact option. |
| `--tasks-dir PATH` | Persist compiled map and (in flags mode) reducer tasks here. If omitted in flags mode, a temporary task directory is used and cleaned up after execution. |

### Scan decision table

The default is computed from the paths, not from whether the user intended a
batch:

| Input | Default |
| --- | --- |
| One directory | Scan immediate child directories. An empty directory is an error. |
| One glob | Scan sorted glob matches. A non-matching glob is an error. |
| One existing file | Do not scan; pass it as one input. |
| Multiple paths | Do not scan; group all paths in one environment. |
| Any input with explicit `--scan` | Scan every supplied value, flattening matches in input order; de-duplicate resolved paths and then apply the limit. |
| Any input with explicit `--no-scan` | Do not scan; `--limit` is rejected. |

When scanning, glob matches are sorted per pattern; directory scans include
only immediate subdirectories, not files in the directory. `--limit` applies
after de-duplication across all supplied patterns/paths.

## Job and map-agent flags

| Flag | Map behavior |
| --- | --- |
| `-e, --env TEXT` | Execution provider/type, resolved as Harbor's environment spec. |
| `-n, --n-concurrent INTEGER` | Maximum concurrent trials; flags-mode default comes from `ExecJobConfig` (`4`). |
| `-r, --max-retries INTEGER` | Map retry maximum; minimum `0`. In flags mode the retry config is copied to the reducer. |
| `--jobs-dir PATH` | Directory for map and reducer job results; flags-mode default is `jobs`, and the reducer shares it. |
| `-q, --quiet` | Suppress trial progress; inherited by the reducer in flags mode. |
| `-a, --agent TEXT` | Map agent name. Agent-specific flags require this option. |
| `-m, --model TEXT` | Repeatable map model names. Multiple models create multiple map agent configs. |
| `--ak, --agent-kwarg KEY=VALUE` | Repeatable map agent kwarg. Values use Harbor's key/value parser. |
| `--ae, --agent-env KEY=VALUE` | Repeatable map agent environment variable. |
| `--agent-timeout FLOAT` | Map agent execution timeout override in seconds; the resolved agent config is inherited by a flags-mode reducer. |
| `-k, --n-attempts INTEGER` | Map attempts per task; `ExecJobConfig` requires at least 1. |
| `--job-name TEXT` | Map job name. If omitted, flags mode creates a timestamped `YYYY-MM-DD__HH-MM-SS-map` name. |

If `--model`, `--ak`, or `--ae` is supplied without `--agent`, flags mode
fails with an agent-required error. A map job's `agents` list also has Harbor's
normal concurrency validation; an individual agent's requested concurrency
cannot exceed the job trial concurrency.

## Reduce-task and reduce-job flags

Any reducer option makes a reducer config. The reducer still needs exactly one
instruction source: `--ri/--reduce-instruction/--reduce-prompt` or
`--reduce-instruction-path`.

| Flag | Reduce behavior |
| --- | --- |
| `--ri, --reduce-instruction, --reduce-prompt TEXT` | Inline reducer instruction; mutually exclusive with its path form. |
| `--reduce-instruction-path PATH` | Reducer instruction file. |
| `--reduce-task-template PATH` | Optional reducer template directory. |
| `--reduce-image TEXT` | Reducer task image; default `ubuntu:latest`. |
| `--reduce-workdir TEXT` | Reducer task workdir; default `/app`. |
| `--reduce-artifact TEXT` | Repeatable reducer artifact list. Supplied values replace reducer prompt inference. |
| `--reduce-reward-artifact TEXT` | Reducer reward JSON artifact; also collected and verified. |
| `--reduce-agent TEXT` | Reducer agent; defaults to the map agent configuration. |
| `--reduce-model TEXT` | Repeatable reducer model list; defaults to map models/configs. |
| `--reduce-ak, --reduce-agent-kwarg KEY=VALUE` | Reducer agent kwargs; when omitted, map kwargs are retained. |
| `--reduce-ae, --reduce-agent-env KEY=VALUE` | Reducer agent environment; when omitted, map environment variables are retained. |
| `--reduce-job-name TEXT` | Reducer job name; default is the same timestamp stem with `-reduce`. |
| `--rk, --n-reduce-attempts INTEGER` | Reducer attempts; minimum `1`. It does not inherit map `--n-attempts`; flags-mode default is `1`. |

In flags mode, the reducer inherits the map job's provider, concurrency,
quiet setting, retry configuration, metrics, jobs directory, and—unless
reducer-specific agent/model/kwarg/env options are passed—the map agent
configs. Reducer-specific settings are partial overrides, not a second
independent complete job definition.

## Output and verification flags

Map and reducer artifacts are container-side paths (normally under `/app`).
The generated auto-verifier checks that required paths exist. A reward artifact
is added to the collected/required list and, only after the existence checks
pass, is validated and copied to `/logs/verifier/reward.json`. A run with no
reward artifact but generated verification writes a plain reward result; a
reward-artifact run gets structured reward JSON.

`--disable-verification` removes generated compile verifiers and marks the
flags-mode job verifier disabled. It does not make a missing artifact usable,
and it is incompatible with reward-artifact flags because promotion requires
verification.

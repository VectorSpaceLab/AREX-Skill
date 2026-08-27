---
name: exec-map-reduce
description: "Operate Harbor's experimental `harbor exec` map/reduce workflow:
  choose flags or ExecConfig mode, compile paths into tasks, inspect inferred or
  explicit artifacts, run map jobs, stage map artifacts into a reducer, and
  troubleshoot configuration and output failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Harbor `exec`: map and reduce

Use this skill only for Harbor's experimental `harbor exec` command. It is a
small compile → map-job → optional-reduce-job workflow, not a general
`harbor run` job configuration guide. Keep the run inspectable and avoid
starting an agent/model job until the resolved configuration and artifact
contract are clear.

## Route by intent

- **One-off invocation:** use [references/cli-reference.md](references/cli-reference.md)
  for flags, scan semantics, defaults, and aliases.
- **Repeatable workflow:** write a complete YAML, JSON, or TOML `ExecConfig`; use
  [references/config-schema.md](references/config-schema.md) for the model
  fields and map/reduce invariant.
- **Aggregation:** use
  [references/map-reduce-recipes.md](references/map-reduce-recipes.md) for the
  map artifact contract, reducer input layout, and reward-artifact examples.
- **Failure or surprising output:** start with
  [references/troubleshooting.md](references/troubleshooting.md), then run
  `--print-config` rather than launching another trial.

## Safe operating sequence

1. Check the installed surface before making version-sensitive claims:
   `harbor --version` and `harbor exec --help`. The command is explicitly
   experimental; the verified help surface includes `--print-config` for
   resolving config and inferred artifacts without executing a job.
2. Select exactly one input mode:
   - **Flags mode:** supply compilation and job options directly. A reducer is
     created when any reducer option is passed, but it still requires a reducer
     instruction source.
   - **Config mode:** pass `--config FILE`, where the suffix is `.yaml`, `.yml`,
     `.json`, or `.toml`. Put the complete workflow under `map` and optional
     `reduce`; do not mix it with flags-mode options. `--print-config` remains
     useful with either mode.
3. Make the input cardinality explicit when it matters. A single directory or
   glob scans by default; multiple paths are grouped into one environment by
   default. Use `--scan` or `--no-scan` deliberately and use `--limit` only for
   scanning.
4. Define the output contract. Prefer `-f/--artifact` and
   `--reduce-artifact` over prompt inference. If scoring is needed, configure a
   reward artifact that is a non-empty JSON object whose values are numbers;
   do not combine reward-artifact options with `--disable-verification`.
5. Run `--print-config` and inspect the JSON: paths, instructions, workdirs,
   task output directory, artifact list, generated verifiers, agents/models,
   attempts, concurrency, retry settings, provider, and job names. This is a
   read-only preflight; it does not compile tasks or run agents.
6. Only after preflight approval run the same command without `--print-config`.
   Record the printed map/reduce job directories. Omitted task output is
   temporary in flags mode and is cleaned up after execution; jobs default to
   `jobs` and persist unless a caller chooses another `--jobs-dir`.

## Boundaries and cautions

- A reducer requires non-empty `map.compile.artifacts`. Those map artifacts are
  staged into the reducer as implicit inputs; the reducer has no path-scan
  option for them.
- Auto-inference is conservative and is based on **inline** instruction text.
  It does not inspect an instruction file's contents. Explicit artifact paths
  are safer for correctness and for reducer eligibility.
- Auto-verification checks artifact existence. A reward artifact adds a JSON
  promotion step; it is not a substitute for a domain verifier.
- Do not claim a live agent/model, Docker, cloud provider, or external API was
  verified merely because a config parsed. This skill's checks are config/help
  checks only unless the caller separately authorizes a real execution.
- For ordinary evaluation jobs, route to the Harbor evaluation workflow rather
  than expanding this skill.

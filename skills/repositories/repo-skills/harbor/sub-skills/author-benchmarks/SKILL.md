---
name: author-benchmarks
description: "Author and validate Harbor benchmark tasks, datasets, adapters,
  verifiers, metrics, and registry packages without launching evaluation jobs or
  mutating remote state."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Author Harbor benchmarks

Use this skill to define and preflight **what Harbor evaluates**: task
contracts, sandbox environments, dataset manifests, benchmark adapters,
verifiers, RewardKit criteria, dataset metrics, parity inputs, and registry
packages. Produce a locally reviewable artifact. Do not launch an agent, trial,
Docker/cloud environment, model/API judge, parity run, upload, download from a
remote registry, authentication flow, visibility mutation, or publish unless a
separately approved workflow owns that action.

## Route before editing

Identify the primary artifact and keep the boundary visible:

| Request | This skill owns | Route elsewhere |
|---|---|---|
| Task definition | `task.toml`, instruction, environment, resources, network, MCP/skills declarations, artifacts, solution/oracle layout, tests, multi-step gates | Running the task/job/trial → [`run-evaluate`](../run-evaluate/SKILL.md) |
| Dataset | `dataset.toml`, local task membership, pinned digests, metric script, local add/remove/sync review | Result aggregation, registry inspection, or sharing outcomes → [`analyze-publish`](../analyze-publish/SKILL.md) |
| Adapter | benchmark conversion package, stable generated names, task template, adapter metadata, parity plan and structural validation | Custom agent/environment/plugin implementation → [`integrations`](../integrations/SKILL.md); completed parity/result analysis → [`analyze-publish`](../analyze-publish/SKILL.md) |
| Verifier/reward | shell or pytest verifier, RewardKit programmatic/judge criteria, reward dimensions and gates | Framework-level verifier or RewardKit extension code → [`integrations`](../integrations/SKILL.md) |
| Task-side MCP/skills | `[[environment.mcp_servers]]` and `environment.skills_dir` declarations | Implementing an MCP server, skill system, bridge, or plugin → [`integrations`](../integrations/SKILL.md) |

Do not route ordinary task authoring to `integrations` merely because the task
uses an existing MCP server or RewardKit. Do not route a task definition error
to `run-evaluate`; do not use a failed run to replace schema validation.

## Operating workflow

1. **Normalize the contract.** Record the task/dataset/adapter package name,
   local output path, intended behavior, source benchmark assumptions, oracle
   availability, target OS/provider/backend, reward shape, acceptance check,
   parity subset, and any credential/network/hardware limits. Keep unknowns
   explicit.
2. **Scaffold locally.** From a disposable output directory, use the matching
   command:

   ```bash
   harbor task init "org/task-name" --description "..."
   harbor task init "org/multi-step" --steps 2
   harbor dataset init "org/dataset-name" --description "..."
   harbor dataset init "org/dataset-name" --with-metric
   harbor adapter init adapter-name --name "Benchmark Name"
   # Equivalent umbrella command:
   harbor init --task "org/task-name"
   harbor init --dataset "org/dataset-name" --with-metric
   ```

   Inspect the generated tree immediately. Replace placeholders; never put the
   reference solution, hidden tests, answer-bearing fixture, or rubric in the
   agent-facing `instruction.md`.
3. **Author the smallest complete contract.** Give the agent an observable
   goal and constraints; make environment dependencies reproducible; use
   absolute verifier paths; make generated task names deterministic; select
   shared versus separate verification; declare artifact transfer explicitly.
4. **Preflight without execution.** Parse TOML through the installed Harbor
   model or a safe CLI/parser check, verify required files/scripts and reward
   shape, inspect artifact collisions and manifest changes, and run the
   bundled adapter validator on a bounded fixture. Do not start an environment
   or call a model as a syntax check.
5. **Prepare, do not spend, parity.** When an oracle exists, record how it will
   be checked. Freeze versions, prompts, agent/model settings, timeouts,
   environment dependencies, task order, and the symmetric sanity/full/repeat
   plan. Parity runs and result interpretation belong to approved workflows.
6. **Gate mutations.** `add`, `remove`, and `sync` mutate a local manifest;
   review the diff. `publish`, remote `download`, auth, visibility, Hub access,
   and external registry operations require explicit credentialed approval.

Read the detailed contracts in this order:

1. [`task-format.md`](references/task-format.md)
2. [`datasets-adapters.md`](references/datasets-adapters.md)
3. [`verifiers-rewardkit-metrics.md`](references/verifiers-rewardkit-metrics.md)
4. [`registry-publishing.md`](references/registry-publishing.md)
5. [`troubleshooting.md`](references/troubleshooting.md)

The portable adapter checker is bundled at
[`scripts/validate_adapter.py`](scripts/validate_adapter.py). It accepts only
caller-supplied adapter paths, imports no Harbor modules, performs no network
operation, and writes reports only where the caller requests them.

## Task contract

A single-step task normally contains:

```text
task/
├── task.toml
├── instruction.md
├── README.md
├── environment/              # Dockerfile, Compose file, image, or runtime files
├── solution/solve.sh          # optional Oracle solution; solve.bat on Windows
└── tests/test.sh              # test.bat on Windows
```

Use `schema_version = "1.4"`. A registry task needs a stable
`[task].name = "org/name"`, a package `[task].version`, description/authors,
and searchable keywords. Put resources and the environment-start network
baseline under `[environment]`; `[agent]` and `[verifier]` network fields are
phase overrides. Network modes are `public`, `no-network`, and `allowlist`;
allowlist entries are hosts/IPs/CIDRs or supported leading wildcards, not URLs,
ports, or paths.

For a separate verifier, set `verifier.environment_mode = "separate"` and
provide `[verifier.environment]` when it needs a distinct image, OS, network
baseline, dependencies, or hidden grader. The verifier image must own its
OS-appropriate `/tests/test.sh` or `/tests/test.bat`; tests are not uploaded to
it at runtime. Transfer agent outputs with `artifacts = [...]` using original
absolute source paths. Sidecar evidence needs a Compose-capable provider,
absolute service paths, and (when necessary) a POSIX-compatible
`[[verifier.collect]]` snapshot.

For multi-step tasks, list ordered `[[steps]]` matching `steps/<name>/`, give
per-step instructions/tests/workdir/setup hooks, and choose
`multi_step_reward_strategy = "mean"` or `"final"`. Use scalar
`min_reward = 1.0` only for the `reward` key; use a mapping such as
`min_reward = { correctness = 0.8, style = 0.5 }` for named dimensions. A
run-time `--resume-trajectory` choice is not task configuration and belongs to
`run-evaluate`.

## Verifier and reward boundary

The OS-appropriate test entrypoint must create `/logs/verifier/reward.txt` (one
numeric value) or `/logs/verifier/reward.json` (an object whose values are
numeric). Harbor prefers JSON if both exist. Use absolute paths, create the
reward directory if needed, return a useful test status, and keep grader inputs
out of the agent-visible workspace.

Choose the simplest verifier that expresses the rubric:

- shell for a few deterministic checks;
- pytest for assertion-oriented checks translated to a numeric reward;
- RewardKit programmatic criteria for reusable/weighted/multi-dimensional
  checks;
- RewardKit LLM or agent judge only for subjective criteria, with an explicit
  key/network/provider/separate-environment gate;
- a custom Harbor verifier only when the task-side test contract cannot express
  the requirement, then route implementation to `integrations`.

RewardKit's dimensions are internal to each verifier invocation. Harbor's
multi-step aggregation and `min_reward` gating happen outside RewardKit; design
the exact reward keys before choosing gates. A dataset `metric.py` is a
separate aggregation script, not a task verifier and not an agent judge.

## Dataset and adapter boundary

A dataset is a versioned collection of task packages. Its manifest pins task
archives with `sha256:<64 lowercase hex>` digests and dataset files such as
`metric.py` with simple filenames and hashes. Use local paths while authoring:

```bash
harbor add path/to/task
harbor add path/to/tasks --scan
harbor add metric.py
harbor remove "org/task-name"
harbor sync path/to/dataset
```

Review `dataset.toml` after every mutating command. Remote refs such as
`org/task@latest` and `harbor sync --upgrade` are explicitly networked and
version-changing.

An adapter must generate reproducible task trees and support bounded
conversion/debugging flags:

```bash
uv run python -m adapter_package.main \
  --output-dir /tmp/generated --limit 10 --overwrite --task-ids id-1
# When implemented:
uv run python -m adapter_package.main \
  --split parity --output-dir /tmp/parity
python scripts/validate_adapter.py --help
python scripts/validate_adapter.py --json-output /tmp/adapter-report.json \
  path/to/adapter
```

Every generated task needs a stable `[task].name`, `schema_version = "1.4"`,
`instruction.md`, an environment definition, and an OS-appropriate verifier;
include an Oracle solution when available. Use singular
`parity_experiment.json`. Treat validator warnings as review items and a
non-zero exit as a blocking structural defect. The validator is not an Oracle
run, parity proof, code review, or publish check.

For parity preparation, preserve raw scores and use sample SEM
`sqrt(sum((x - mean)^2) / (n * (n - 1)))`. Compare both sides symmetrically:
5–10 task sanity subset, one full run, then three runs. Do not claim parity
until an approved execution workflow has actually checked it.

## Registry and publishing boundary

Use package names, not directory names, as the registry identity:

```toml
[task]
name = "org/task"
version = "1.0.0"

[dataset]
name = "org/dataset"
version = "1.0.0"
```

Before handoff, report local paths, package names, parsed task/file counts,
digest changes, requested tags, visibility, whether dataset tasks should be
included, oracle/parity evidence, and known omissions. The credentialed
publishing workflow may then run:

```bash
harbor auth status
harbor publish path/to/task --tag v1.0
harbor publish path/to/dataset --tag v1.0 --no-tasks
# Public visibility is an explicit mutation:
harbor publish path/to/dataset --tag v1.0 --public
```

`latest` is always added by publish. Do not execute these mutation commands in
this authoring workflow. Registry download, visibility changes, sharing, and
post-publication inspection are also gated; completed result/trajectory review
belongs to `analyze-publish`.

## Validation commands

Use the installed environment and temporary paths:

```bash
harbor --version
harbor task init --help
harbor dataset init --help
harbor adapter init --help
harbor adapter review --help
harbor check --help                 # quality check; may launch an evaluator
harbor publish --help
python scripts/validate_adapter.py --help
python -m py_compile scripts/validate_adapter.py
```

`harbor task check` is a removed compatibility command; use the root
`harbor check` only when its evaluator/model execution is explicitly approved.
For a local task, prefer TOML/model parsing, file/permission checks, and
fixture tests first. Do not claim Docker, Compose, GPU, Windows, cloud,
provider, external model, credentials, judge, or parity viability from help or
static checks alone.

## Completion record

Hand off only:

- files created or updated and local paths;
- source/docs/tests consulted;
- parser, help, static, and fixture checks performed;
- optional backends and credentialed operations not exercised;
- unresolved schema, reward, adapter, or parity gaps;
- one or two difficult synthetic usability cases for later verification.

Keep test cases, reports, logs, parity JSON, generated benchmark data, and
review notes outside this runtime skill tree.

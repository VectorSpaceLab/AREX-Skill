---
name: harbor
description: "Use Harbor to evaluate agents and language models in sandboxed
  tasks, author benchmark datasets and verifiers, run map-reduce jobs, inspect
  trajectories and artifacts, publish results, or extend Harbor with custom
  integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Harbor

Harbor is a Python framework and CLI for evaluating agents and language models
against task environments, building benchmark datasets, scaling trials across
sandbox providers, and generating rollouts for optimization. Use this skill for
**operating Harbor**, not for editing arbitrary repository code.

## First checks

Use a compatible Python installation (the inspected release is Harbor `0.22.0`,
which requires Python `>=3.12`) and verify the actual installation before
making version-sensitive claims:

```bash
python -m pip install harbor
harbor --version
harbor run --help
```

For a safe, no-network diagnostic of Harbor plus the optional first-party
packages, run [`scripts/check_install.py`](scripts/check_install.py). Read
[`references/troubleshooting.md`](references/troubleshooting.md) when import,
CLI, optional-extra, or provider setup fails.

## Route by task shape

- **Run an existing task, dataset, job, or trial:** read
  [`run-evaluate`](sub-skills/run-evaluate/SKILL.md). It covers agents, models,
  environments, concurrency, retries, resources, network, artifacts,
  multi-step sessions, and trajectory loading.
- **Create or validate tasks, datasets, adapters, verifiers, RewardKit checks,
  metrics, or registry packages:** read
  [`author-benchmarks`](sub-skills/author-benchmarks/SKILL.md).
- **Compile files into tasks and optionally aggregate map outputs:** read
  [`exec-map-reduce`](sub-skills/exec-map-reduce/SKILL.md). This is the
  experimental `harbor exec` workflow, not ordinary `harbor run`.
- **Inspect, compare, regrade, view, export, upload, or publish outcomes:**
  read [`analyze-publish`](sub-skills/analyze-publish/SKILL.md). Keep
  credentialed and mutating actions gated.
- **Implement custom agents, environments, bridges, plugins, MCP/skills
  injection, or optional provider integrations:** read
  [`integrations`](sub-skills/integrations/SKILL.md).

Start with the narrowest route. When a request spans routes, finish the safe
configuration or inspection prerequisite first and hand off the resulting
paths/config; do not duplicate sibling instructions.

## Core model

Harbor's operating objects are task → dataset → trial → job → result. A task
contains an instruction, environment, and verifier. A dataset groups tasks. An
agent performs a task inside an environment; a trial is one attempt; a job is a
parallel collection of trials. Artifacts, verifier rewards, logs, and native or
ATIF trajectories are persisted for later inspection. Read
[`references/architecture.md`](references/architecture.md) for the verified
relationships and config layering.

## Safety and evidence gates

Before a costly run, resolve the input path/package, agent and model, provider,
credentials, task count, attempts, concurrency, timeout/resource/network
policy, artifacts, and output directory. Use `--print-config` where available
and prefer a tiny local or install-only preflight. Do not treat a parsed config
as proof that Docker, a cloud provider, a GPU, Windows containers, a model API,
or a registry credential works. Do not disable verification to hide a malformed
task or verifier.

The generated references are self-contained and do not require the source
checkout. Read [`references/repo-provenance.md`](references/repo-provenance.md)
before deciding whether this graph is stale for a new Harbor release or
checkout. Router placement for managed repo-skill discovery is recorded in
[`references/repo-routing-metadata.json`](references/repo-routing-metadata.json).

---
name: experiments-analysis
description: "Reuse OASIS legacy experiment patterns, user-generation notes, and
  post-simulation analysis workflows without assuming unsafe execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Experiments analysis

Use this sub-skill when a request is about legacy OASIS experiment families, generated-user pipelines, or post-simulation visualization and triage.

## Start here
1. Identify the experiment family and artifact type.
2. Read [legacy experiments](references/legacy-experiments.md).
3. Read [profile generation and analysis](references/profile-generation-and-analysis.md) if the request touches generated profiles, score plots, counterfactual scoring, or Neo4j follow graphs.
4. If the task starts from a SQLite database and needs schema or table inspection, hand off first to `platform-actions` DB summary before custom analysis.
5. If the request is really about profile validation, env lifecycle, or action arguments, route to `agent-profiles`, `simulation-workflows`, or `platform-actions`.

## What this sub-skill owns
- Mapping legacy experiment folders to their config knobs and result artifacts.
- Explaining how to downscale or adapt a legacy config without changing the scenario unnecessarily.
- Reading generated DB, JSON, CSV, or graph outputs and deciding whether a plot, table, or graph export is the right next step.
- Flagging blocked runs caused by missing credentials, GPU or server pieces, or large-scale cost.

## What it does not own
- Root install, import, or API smoke.
- Profile schema validation.
- Environment lifecycle or step-by-step execution.
- Detailed action argument matrices or recsys internals.

## Safe defaults
- Treat OpenAI, Hugging Face, VLLM, Slurm, and Neo4j dependencies as conditional.
- Prefer analysis of existing outputs over rerunning simulations.
- For tiny budgets, lower `num_timesteps`, `round_post_num`, and `activate_prob` before changing the scenario.

## Deliverables
- Adaptation notes for legacy YAMLs.
- Analysis plans for existing outputs.
- Blocker lists when a requested run is not safe to attempt.

## References
- [Legacy experiments](references/legacy-experiments.md)
- [Profile generation and analysis](references/profile-generation-and-analysis.md)
- [Troubleshooting](references/troubleshooting.md)

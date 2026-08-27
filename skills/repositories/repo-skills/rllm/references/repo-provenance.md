# Repo Provenance

This public provenance file records the source revision and evidence baseline used to create the repo skill. It intentionally omits local checkout paths and private environment paths.

```yaml
schema: disco.repo-provenance.v1
skill_id: rllm
generated_at_utc: "2026-08-15T07:33:27Z"
source:
  branch: main
  commit: cf0ff432d2c5632e6eeb5232aaa89e61b0523ec5
  working_tree_before_generation: clean
packages:
  - name: rllm
    version_from_source_metadata: 0.3.0.pre
    python: ">=3.10"
  - name: rllm-model-gateway
    version_from_source_metadata: 0.1.0
    python: ">=3.10"
entry_points:
  - rllm = rllm.cli.main:cli
  - rllm-model-gateway = rllm_model_gateway.server:main
extraction_scope:
  decision: agent-confirmed
```

## Evidence families used

- Core package modules for agents, types, eval, CLI, datasets, tasks, workflows, engines, gateway management, sandbox hooks, trainer backends, SFT, and registries.
- Sibling `rllm-model-gateway` package for server, client, config, worker, session, and trace data models.
- Documentation covering installation, quickstart CLI, AgentFlow/evaluator, workflows, tasks, harnesses, datasets, running evaluations, trainer APIs, unified trainer, backend comparison, Tinker, Verl, training customization/distribution, and AgentCore runtime.
- Representative cookbooks/examples for math, frozen lake, solver/judge flow, agent framework integrations, AgentCore math, countdown unified trainer, Harbor SWE, verifiers environment, and SFT data flows.
- Representative tests for CLI commands, rollout/evaluator decorators, gateway manager, trace converter, Verl config validation, Tinker LR schedules, and integration runtime behavior.
- Repository scripts were classified before bundling: safe config/dump ideas were distilled into skill-owned helpers; network/download/install/service launchers remain reference-only and are not runtime dependencies.

Refresh this skill when the source commit, CLI surface, backend config schema, gateway API, or exported decorator/type locations change.

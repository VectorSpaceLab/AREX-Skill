---
name: rllm
description: "Use rLLM for language-agent evaluation, dataset/task management,
  RL/SFT post-training, CLI setup, and gateway-backed rollout tracing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# rLLM

Use this root skill when a task names **rLLM**, `rllm`, `rllm-model-gateway`, `AgentFlow`, `@rllm.rollout`, `rllm eval`, `rllm dataset`, `rllm train`, `rllm sft`, Tinker, Verl, Fireworks, sandboxed language-agent benchmarks, or the rLLM CLI.

This is a router, not a full manual. First classify the request, then read the focused sub-skill and only the references needed for that workflow.

## Fast Start

1. **Check installation scope.** Read `references/installation-and-environment.md` before installing extras. Core eval/data workflows are lighter than Tinker/Verl/Fireworks/AgentCore training workflows.
2. **Run a safe smoke check when setup is uncertain:**

   ```bash
   python scripts/rllm_smoke_check.py
   ```

   The script imports core packages, inventories CLI entry points, and reports optional backend availability without training, downloading data, or contacting providers.
3. **Use current public APIs, not stale docs.** Confirmed source facts: `rollout` and `evaluator` are top-level `rllm` exports; `AgentConfig` lives in `rllm.types`; `SimpleWorkflow` is imported from `rllm.workflows.simple_workflow`, not directly from `rllm.workflows`.
4. **Keep credentials explicit.** Provider API keys, Tinker/Fireworks credentials, UI login, and remote sandbox services are never implied by a successful import check.
5. **Treat full training as backend-specific.** CPU/import tests can validate guidance, but local `verl`, Tinker, Fireworks, AgentCore, and long distributed runs require their actual backend/runtime evidence.

## Route By Task

- **Evaluate agents and author AgentFlows:** read `sub-skills/evaluation/SKILL.md` for `@rllm.rollout`, `@rllm.evaluator`, `AgentFlow`, `Task`, `Episode`, `Trajectory`, `rllm eval`, pass@k, harness selection, sandboxed eval, and saved episode/result interpretation.
- **Manage datasets and task layouts:** read `sub-skills/datasets/SKILL.md` for `rllm dataset`, registered datasets, local benchmark directories, `dataset.toml`, `task.toml`, Harbor-compatible task packages, verifier metadata, and eval-to-SFT curation.
- **Train or fine-tune models:** read `sub-skills/training/SKILL.md` for `rllm train`, `rllm sft`, `AgentTrainer`, `AgentSFTTrainer`, `BackendProtocol`, Tinker, Verl, Fireworks, remote runtimes, gateway-backed traces, algorithm config, and backend validation failures.
- **Operate the CLI around workflows:** read `sub-skills/cli-ops/SKILL.md` for `rllm model`, `rllm login`, `rllm init`, `rllm agent`, `rllm view`, and `rllm snapshot` setup/utility workflows.
- **Debug gateway or trace capture:** start with `references/gateway-and-traces.md`, then use `training` for end-to-end training/eval wiring or `cli-ops` for provider/model configuration.

## Shared References

- `references/cli-command-map.md` maps every top-level CLI command to its owning sub-skill and common non-destructive help checks.
- `references/gateway-and-traces.md` covers the bundled `rllm-model-gateway` service, client/config types, sessions, workers, traces, and trace-conversion pitfalls.
- `references/troubleshooting.md` covers cross-cutting import, optional dependency, provider, sandbox, and backend errors.
- `references/repo-provenance.md` records the source revision and extraction evidence used to build this skill.

## Avoid

- Do not run long RL/SFT jobs, large dataset downloads, provider calls, snapshot builds, or remote sandbox provisioning unless the user explicitly wants those side effects.
- Do not tell users to read or run files from the original checkout. This skill tree contains the distilled references and safe helper scripts needed after the checkout is gone.

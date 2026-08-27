---
name: agent-lightning
description: "Use this repo skill for Agent Lightning package tasks: authoring
  trainable agents, tracing rewards and spans, running LightningStore/Trainer
  loops, using agl CLI services, choosing examples, and troubleshooting optional
  backends."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Agent Lightning Repo Skill

Use this skill when a user asks for help with Agent Lightning (`agentlightning`): writing trainable agents, collecting spans and rewards, coordinating runners/stores/trainers/algorithms, using `agl` services, selecting example recipes, or diagnosing package/backend issues.

Agent Lightning's core loop is: a runner executes a `LitAgent`, a tracer emits spans into a `LightningStore`, algorithms read those traces and update resources, and `Trainer` wires those components together.

## First steps for any task

1. Identify the user's workflow and route to the nearest sub-skill below.
2. If the user is using a different checkout or package version, read [repo provenance](references/repo-provenance.md) before relying on version-sensitive details.
3. For install or import trouble, run or adapt [scripts/check_agentlightning_install.py](scripts/check_agentlightning_install.py) and read [compatibility](references/compatibility.md) plus [cross-cutting troubleshooting](references/troubleshooting.md).
4. Treat GPU, MongoDB, cloud API, W&B/Tinker, Docker/SWE-bench, and dashboard workflows as optional unless the user explicitly provides those resources.

## Route map

| User intent | Use this sub-skill | What it contains |
| --- | --- | --- |
| Write or wrap an agent, fix `@rollout` signatures, use `PromptTemplate` or `LLM`, debug one rollout | [agent-authoring](sub-skills/agent-authoring/SKILL.md) | Agent function/class patterns, resource injection, return contracts, runner single-step smoke |
| Emit rewards/messages/objects, inspect spans, adapt traces to messages/triplets, debug missing token IDs | [tracing-and-instrumentation](sub-skills/tracing-and-instrumentation/SKILL.md) | `OtelTracer`, `AgentOpsTracer`, emitters, `operation`, adapters, trace troubleshooting |
| Operate `LightningStore`, runners, algorithms, `Trainer.fit`, `Trainer.dev`, status/retry behavior | [runner-store-training](sub-skills/runner-store-training/SKILL.md) | Store API, rollout/attempt lifecycle, resources, custom algorithms, training loop recipes |
| Use `agl` CLI, store/prometheus services, LLM proxy, vLLM bridge, endpoint checks, metrics | [cli-and-services](sub-skills/cli-and-services/SKILL.md) | Help-confirmed CLI flags, service launch patterns, safe LiteLLM/OpenAI-compatible checks |
| Choose or adapt examples such as APO, SQL, RAG, ChartQA, Unsloth, Azure, Claude Code, Tinker | [examples-and-recipes](sub-skills/examples-and-recipes/SKILL.md) | Example/backend catalog, optional dependency matrix, maintainer example rules |

## Installation orientation

General use:

```bash
python -m pip install --upgrade agentlightning
python - <<'PY'
import agentlightning as agl
print(agl.__version__)
print(type(agl.InMemoryLightningStore()).__name__)
PY
```

For source development, use the repository's `uv` workflow and choose only the optional groups needed for the task. CPU-only work can inspect and run base package APIs without CUDA. APO requires the `apo` extra (`poml`) plus an OpenAI-compatible endpoint for full examples. VERL/vLLM/Unsloth/vision/RAG examples require larger dependency groups and usually CUDA-compatible hardware.

## Core public objects to recognize

- Agent authoring: `rollout`, `llm_rollout`, `prompt_rollout`, `LitAgent`, `PromptTemplate`, `LLM`, `ProxyLLM`, `NamedResources`.
- Execution: `LitAgentRunner`, `Runner`, `Hook`, `Trainer`, `Algorithm`, `FastAlgorithm`, `Baseline`, `algo`.
- Store/control plane: `LightningStore`, `InMemoryLightningStore`, `LightningStoreClient`, `LightningStoreServer`, `LightningStoreThreaded`, `RolloutConfig`.
- Tracing: `OtelTracer`, `AgentOpsTracer`, `DummyTracer`, `emit_reward`, `emit_message`, `emit_object`, `emit_exception`, `operation`, `find_final_reward`, `TracerTraceToTriplet`, `LlmProxyTraceToTriplet`, `TraceToMessages`.
- Services: `agl`, `LLMProxy`, `ProxyLLM`, metrics backends, OpenAI-compatible endpoint patterns.

## Fast validation

Use this when a user asks whether the installed package is basically usable:

```bash
python scripts/check_agentlightning_install.py
```

For deeper workflow checks, run the nearest sub-skill smoke script:

- Agent authoring: `python sub-skills/agent-authoring/scripts/agent_rollout_smoke.py`
- Tracing: `python sub-skills/tracing-and-instrumentation/scripts/local_trace_smoke.py`
- Store/training control plane: `python sub-skills/runner-store-training/scripts/store_status_smoke.py`
- Services: `python sub-skills/cli-and-services/scripts/check_litellm_proxy.py --help` or `python sub-skills/cli-and-services/scripts/check_prometheus_metrics.py --duration 1 --host 127.0.0.1`

Run scripts from the generated skill directory or pass explicit paths/URLs where the script supports them. The scripts are safe by default: they do not train models, download data, mutate Docker/Mongo/Ray, or print secrets.

## Known limits

This skill was verified for CPU-compatible package import, CLI help, and in-memory store/runner/tracing smokes. It preserves guidance for optional GPU/cloud/service workflows but does not claim those backends were available or verified. When a user requests optional workflows, first confirm or detect the required hardware, credentials, endpoints, datasets, and dependency groups before running expensive commands.

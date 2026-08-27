---
name: custom-data-rewards-workflows
description: "Author and validate AReaL custom datasets, reward functions,
  RolloutWorkflow implementations, VLM workflows, and OpenAI-compatible agent
  workflows without starting training or services."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Custom Data, Rewards, and Workflows for AReaL

Use this sub-skill when the user wants to add, review, or debug:

- HuggingFace-style datasets or custom sample schemas for AReaL trainers.
- RLVR reward functions and `AsyncRewardWrapper` behavior.
- `RolloutWorkflow`, `RLVRWorkflow`, `VisionRLVRWorkflow`, multi-turn, tool, or VLM trajectory contracts.
- Agent workflows that call AReaL through OpenAI/Anthropic-compatible proxy APIs or the legacy direct `ArealOpenAI` client.
- Safe contract checks for user-provided import paths and sample JSON before any expensive run.

## Route away first

- For training command construction, experiment YAML design, checkpoint/recovery, or trainer invocation details, route to [`post-training-experiments`](../post-training-experiments/SKILL.md).
- For service lifecycle, `areal agent` / inference-service CLI operations, online sessions, admin keys, ports, or interactive Hermes-style loops, route to [`services-cli-operations`](../services-cli-operations/SKILL.md).
- For SGLang/vLLM worker failures, CUDA/NCCL errors, backend allocation strings, weight sync, Megatron/FSDP/Archon internals, or GPU memory failures, route to [`distributed-engines-backends`](../distributed-engines-backends/SKILL.md).

## Minimum safe workflow

1. Classify the customization target:
   - data only, reward only, `RolloutWorkflow`, proxy agent workflow, legacy direct `ArealOpenAI`, VLM workflow, or tool/sandbox workflow.
2. Establish the contract before coding:
   - dataset row keys, reward signature and return type, workflow return type, agent mode, VLM image representation, tool-call parser, and whether any service/backend is required.
3. Validate safely before training:
   - Use [`scripts/check_workflow_contract.py`](scripts/check_workflow_contract.py) on import paths and sample records. The script does not start training, launch services, download models, or require credentials by default.
4. Hand off only the trainer launch portion:
   - Once dataset/reward/workflow contracts are valid, send the user to `post-training-experiments` for the actual `PPOTrainer`/`GRPOConfig` command or config edits.

## Bundled references

- [`references/data-reward-workflow-contracts.md`](references/data-reward-workflow-contracts.md): dataset schemas, reward signatures, tensor returns, built-in RLVR/VLM workflow contracts, and safe validation commands.
- [`references/agentic-workflow-recipes.md`](references/agentic-workflow-recipes.md): proxy vs direct agent integration, inline/subprocess/online modes, multi-turn rewards, tool calling, VLM requests, and framework patterns.
- [`references/troubleshooting.md`](references/troubleshooting.md): import, schema, reward, async, proxy, session, tool parser, VLM, and routing failure modes.

## Default recommendations

- Prefer proxy-style agent workflows: an importable class with `async def run(self, data, **extra_kwargs) -> float | dict[str, float]` that uses the injected `base_url`, `api_key`, and shared async HTTP client.
- Use direct `ArealOpenAI` only for legacy or framework-specific cases where a custom OpenAI client object must be passed directly to the framework.
- Keep reward functions synchronous, module-level, picklable, and scalar-returning when used with `RLVRWorkflow` or `VisionRLVRWorkflow`.
- Keep top-level imports light. Heavy SDK, credential, sandbox, or provider setup should happen inside functions or guarded code paths so workers can import the workflow class reliably.
- Never run training, launch proxy services, download datasets/models, or call external providers as a validation step in this sub-skill.

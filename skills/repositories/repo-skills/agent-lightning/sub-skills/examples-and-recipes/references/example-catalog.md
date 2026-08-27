# Example catalog

## Purpose

Use this catalog to select and adapt Agent Lightning examples without running expensive or credentialed workflows by accident.

## Example families

| Example family | Primary workflow | Required/typical resources | Safe default action |
| --- | --- | --- | --- |
| APO room selector | Prompt optimization of a room-booking agent with built-in APO; custom algorithm and debug variants | `apo` extra, `poml`, OpenAI-compatible endpoint/API key for full run | Read/adapt recipe; run local authoring/store/tracing smokes first |
| Minimal building blocks | Small scripts for traces, metrics, LLM proxy, vLLM hosting | Base package; metrics needs `prometheus-client`; proxy/vLLM needs service/backend | Use bundled safe smokes in this skill tree |
| Azure OpenAI SFT | Roll out capital lookup, export traces to JSONL, fine-tune and deploy via Azure | Azure subscription, Azure CLI/auth, fine-tuning quota, OpenAI SDK | Documentation/planning only unless credentials are supplied |
| Calc-X VERL math | AutoGen + MCP calculator + VERL RL for math reasoning | GPU for training, VERL/vLLM/torch stack, OpenAI-compatible service for sanity | Interface planning only; do not train by default |
| ChartQA vision-language RL | LangGraph chart QA with GPT/vLLM and VERL/GRPO/self-refinement | GPU, image/vision deps, model/data downloads, API or vLLM | Dependency/backend planning only |
| Claude Code SWE-bench | Instrument Claude Code on SWE-bench and stream traces | Docker, SWE-bench, Anthropic/OpenAI/vLLM backend, possible GPU | Documentation/assertion planning only |
| RAG / MuSiQue | Retrieval + MCP + GRPO training | FAISS/index data, retrieval deps, GPU for full training | Treat as optional/historical unless resources exist |
| Spider SQL agent | LangGraph text-to-SQL with Spider benchmark | SQL/langchain deps, datasets, OpenAI/vLLM, GPU for training | Plan data/backend; do not assume benchmark present |
| Tinker integration | Feed Agent Lightning traces into Tinker RL backend | Tinker service credentials, OpenAI/CrewAI deps, W&B optional | Dry-run only if example supports it and credentials are supplied |
| Unsloth SFT | Rank rollouts and fine-tune with 4-bit LoRA/TRL/Unsloth | GPU, TRL/Unsloth stack, torch/vLLM-compatible environment | Dependency planning only |

## How to adapt an example safely

1. Identify whether the user's goal is authoring, tracing, training, serving, or data integration.
2. Route core API details to the focused sub-skill.
3. Use this catalog to choose the closest example family.
4. Check the dependency/backend matrix before installing anything heavy.
5. Prefer a tiny local smoke or help-only check before full example execution.
6. If the example requires credentials, ask for confirmation and avoid printing secrets.
7. If the example requires GPU or large data, verify hardware and data layout first.

## APO recipe summary

Use APO when the resource being optimized is a prompt template and the agent returns rewards. Required components:

- agent decorated with `@rollout` or subclassing `LitAgent`,
- task dataset,
- initial `PromptTemplate`,
- `APO` algorithm with OpenAI-compatible client,
- `TraceToMessages` adapter,
- `Trainer.fit` with train/validation datasets.

Run CPU-local authoring/tracing/store smokes before full APO. Full APO needs an LLM endpoint.

## Minimal recipe summary

Use minimal examples to isolate primitives:

- trace writing -> `tracing-and-instrumentation/scripts/local_trace_smoke.py`,
- metrics -> `cli-and-services/scripts/check_prometheus_metrics.py`,
- LLM proxy endpoint -> `cli-and-services/scripts/check_litellm_proxy.py`,
- local rollout -> `agent-authoring/scripts/agent_rollout_smoke.py`,
- store lifecycle -> `runner-store-training/scripts/store_status_smoke.py`.

## GPU/RL example recipe summary

For VERL/vLLM/ChartQA/Spider/Calc-X/RAG/Unsloth workflows:

1. Confirm CUDA-capable hardware and driver.
2. Use a separate environment from CPU-only package checks.
3. Install the documented torch/vLLM/VERL/TRL groups for the selected example.
4. Verify model and dataset availability.
5. Run a tiny example-specific debug mode before training.
6. Inspect spans and rewards before launching expensive training.

## Cloud/service example recipe summary

For Azure, Anthropic, OpenAI, Tinker, W&B, and Claude Code flows:

1. Confirm credentials and service quotas.
2. Use environment variables or provider SDK config; never hard-code secrets.
3. Verify endpoint/model availability with a tiny call.
4. Keep fine-tuning/deployment/cleanup steps explicit and reversible.
5. Stop if the requested action would deploy, delete, or incur cost without authorization.

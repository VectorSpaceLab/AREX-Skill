# MiniMind Capability and Artifact Overview

## When to read

Read this reference when the task spans more than one MiniMind workflow, when the user is unsure which weight/data format they have, or when a route needs a shared vocabulary before handing off to a sub-skill.

## Capability surface

MiniMind exposes three practical workflow families:

1. **Core model and supervised training**
   - `MiniMindConfig` and `MiniMindForCausalLM` implement a decoder-only Transformer with RMSNorm, RoPE/YaRN support, grouped query/key-value heads, SwiGLU, and optional MoE feed-forward routing.
   - `PretrainDataset` consumes JSONL records with a non-empty `text` string.
   - `SFTDataset` consumes JSONL records with `conversations` messages and supports system tools, assistant `tool_calls`, `reasoning_content`, and chat-template rendering.
   - Core stages are pretraining, full SFT, and native LoRA SFT. Tokenizer retraining is an educational experiment, not the default compatibility path.

2. **Inference, serving, and export**
   - Local generation supports raw MiniMind `.pth` weights when matching source modules and tokenizer assets are available, or Transformers-format model directories for portable loading.
   - The API server exposes an OpenAI-compatible `/v1/chat/completions` route with streaming/non-streaming content, `reasoning_content`, `tool_calls`, and `open_thinking` handling.
   - The Streamlit UI is interactive and expects Transformers-format model directories in its scan area.
   - Conversion helpers cover raw PyTorch to MiniMind-Transformers, raw PyTorch to Qwen3-compatible Transformers, Transformers back to raw state dicts, and base+LoRA merging.

3. **Post-training and online reward**
   - White-box distillation uses teacher/student logits with CE+temperature-scaled KL.
   - DPO uses static `chosen`/`rejected` preference pairs and a frozen reference model.
   - PPO uses Actor/Critic/Reference/Reward Model components with online rollout and GAE.
   - GRPO/CISPO uses grouped generations, group-relative advantages, reference KL, and a selectable loss variant.
   - Agentic RL adds multi-turn tool calls, deterministic tool observations, `gt`-based reward checks, response masks, and optional external reward-model scoring.

## Data formats at a glance

| Workflow | Required top-level shape | Main fields | Validator |
| --- | --- | --- | --- |
| Pretraining | one object per JSONL line | `text: string` | `training-basics/scripts/validate_minimind_jsonl.py --schema pretrain` |
| SFT/LoRA | one object per JSONL line | `conversations: message[]` | `training-basics/scripts/validate_minimind_jsonl.py --schema sft` |
| DPO | one object per JSONL line | `chosen: message[]`, `rejected: message[]` | `rlhf-agentic/scripts/validate_post_training_jsonl.py --schema dpo` |
| PPO/GRPO/CISPO RLAIF | one object per JSONL line | `conversations: message[]`, final assistant placeholder recommended | `rlhf-agentic/scripts/validate_post_training_jsonl.py --schema rlaif` |
| Agentic RL | one object per JSONL line | `conversations`, optional system `tools`, top-level `gt: scalar[]` | `rlhf-agentic/scripts/validate_post_training_jsonl.py --schema agent-rl --require-tools` |

Use proper JSON for nested `tools` and `tool_calls` fields when the dataset stores them as strings. Keep `gt` scalar and canonical so reward matching can find it in final text.

## Artifact naming and handoffs

Dense raw weights conventionally look like `<prefix>_<hidden_size>.pth`; MoE weights add `_moe` before `.pth`.

| Stage | Typical prefix | Handoff |
| --- | --- | --- |
| Pretrain | `pretrain` | Feed to full SFT or inspect with local inference. |
| Full SFT | `full_sft` | Base for LoRA, DPO, distillation, PPO, GRPO, or Agentic RL. |
| LoRA | `lora_<domain>` | Stack for raw inference or merge before portable export. |
| Distillation | `full_dist` | Route to inference or another post-training stage. |
| DPO | `dpo` | Route to inference and compare against the SFT baseline. |
| PPO | `ppo_actor` | Route to inference; inspect KL/reward trade-offs. |
| GRPO/CISPO | `grpo` | Route to inference; compare group-reward gains against broad quality. |
| Agentic RL | `agent` | Route to tool-call evaluation and separately check general Q&A regressions. |

Resume checkpoints add `_resume.pth` and carry optimizer, scaler, epoch, step, world-size, and optional logging state. Keep architecture flags and stage prefixes aligned when resuming.

## Dependency surfaces

- Core inspection/training: PyTorch, Transformers, Datasets, tokenizer support, NumPy, and the dependencies in the public requirements list.
- API service: FastAPI, Uvicorn, Pydantic, PyTorch, Transformers.
- Client probe: OpenAI Python SDK or a compatible HTTP client.
- UI: Streamlit plus the model/runtime dependencies.
- Optional RL acceleration: a local SGLang service with logprob-returning generation and weight-update support.
- External reward models and model/data downloads are user-provided runtime assets, not bundled dependencies.

## Shared safety rules

- Do not download large datasets or model weights just to prove that a route is syntactically correct.
- Do not use raw `.pth` files with a third-party engine that expects a Transformers directory.
- Do not retrain the tokenizer unless the user explicitly accepts a new model-family compatibility boundary.
- Do not enable online logging, external reward models, or SGLang until a tiny local smoke and schema validation pass.
- Do not claim a reward improvement is a general capability improvement; compare post-training weights with the SFT baseline on held-out tasks.

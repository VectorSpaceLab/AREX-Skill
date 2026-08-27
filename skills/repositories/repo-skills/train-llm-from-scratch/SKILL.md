---
name: train-llm-from-scratch
description: "Route train-llm-from-scratch workflows for from-scratch PyTorch
  LLM pretraining, SFT, reward modeling, DPO/ORPO/KTO, PPO, GRPO/RLVR,
  evaluation, chat, configs, UI, and data validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# train-llm-from-scratch

Use this repo skill when a task involves the `train-llm-from-scratch` project: a
pure-PyTorch educational LLM stack covering raw text tokenization, decoder-only
Transformer pretraining, SFT, reward modeling, DPO/ORPO/KTO, PPO, GRPO/RLVR,
GSM8K evaluation, chat, JSON configs, and a Streamlit control panel.

## Start Here

1. If the task may depend on repo freshness, read
   [`references/repo-provenance.md`](references/repo-provenance.md).
2. For setup, optional extras, backend expectations, and import checks, read
   [`references/installation.md`](references/installation.md).
3. Run [`scripts/check_environment.py`](scripts/check_environment.py) when you
   need a safe import/backend smoke check in the user's environment.
4. If checkpoint contents or model dimensions are unclear, run
   [`scripts/inspect_checkpoint.py`](scripts/inspect_checkpoint.py) before
   loading the model.
5. Route to the narrowest sub-skill below. Keep this root as the router; do not
   bury detailed stage work here.

## Sub-Skill Routing

| User task | Read |
|---|---|
| Prepare or validate Pile HDF5, packed SFT HDF5, preference JSONL, RL prompt JSONL, arithmetic curriculum, tokenizer/mask/data-loader issues | [`sub-skills/data-preparation/SKILL.md`](sub-skills/data-preparation/SKILL.md) |
| Inspect the custom Transformer, plan base pretraining, choose legacy vs modern pretraining, DDP/bf16, memory, checkpoint/resume, tiny model smoke | [`sub-skills/model-pretraining/SKILL.md`](sub-skills/model-pretraining/SKILL.md) |
| Run or debug SFT, reward model, DPO/ORPO/KTO, PPO, GRPO/RLVR, rollout/log-probs, KL/reward metrics, post-training pipeline sequencing | [`sub-skills/post-training-rlhf/SKILL.md`](sub-skills/post-training-rlhf/SKILL.md) |
| Evaluate on GSM8K, build stage tables, chat with checkpoints, choose raw vs chat mode, sampling controls, answer parsing/verifier behavior | [`sub-skills/evaluation-chat/SKILL.md`](sub-skills/evaluation-chat/SKILL.md) |
| Edit JSON configs, use smoke configs, inspect CLI override precedence, operate the Streamlit UI, inspect metrics JSONL/job logs | [`sub-skills/configuration-ui/SKILL.md`](sub-skills/configuration-ui/SKILL.md) |

## Install And Import Baseline

The package metadata exposes import roots `config`, `data_loader`, `src`, and
`ui`. A typical editable install from a compatible checkout is:

```bash
pip install -e .
pip install -e ".[train]"   # datasets + optional wandb for data/post-training
pip install -e ".[ui]"      # streamlit + pandas + altair for the control panel
pip install -e ".[docs]"    # mkdocs tooling, only for docs-site work
```

For the selected training workflows, use a PyTorch build that matches the
machine. Full training is CUDA-oriented; CPU smoke configs are useful for parser,
config, and algorithm checks but do not verify large CUDA/bf16/DDP training.

Minimal import smoke:

```bash
python - <<'PY'
from src.models.transformer import Transformer
from src.post_training.chat_template import encode_chat, EOT_ID
ids, mask = encode_chat([
    {"role": "user", "content": "What is 2+2?"},
    {"role": "assistant", "content": "<answer>4</answer>"},
])
print(len(ids), len(mask), sum(mask), ids[-1] == EOT_ID)
print(Transformer(n_head=2, n_embed=16, context_length=8, vocab_size=64, N_BLOCKS=1).__class__.__name__)
PY
```

## Common Operating Rules

- Start with smoke configs or dry-run command builders before launching long
  training, data downloads, or multi-GPU jobs.
- Validate data files before training. Mask/data errors silently corrupt SFT,
  preference optimization, and RL rewards.
- Treat `/ephemeral`-style paths in examples as user-configurable storage roots,
  not mandatory constants.
- Keep Weights & Biases optional. The repo writes local JSONL metrics even when
  W&B is disabled or unavailable.
- Use greedy decoding for comparable GSM8K stage tables; sampling is for chat.
- Do not claim CUDA coverage from CPU-only smoke tests. For CUDA claims, verify a
  torch CUDA allocation and at least a tiny model forward on the target host.

## Troubleshooting

Read [`references/troubleshooting.md`](references/troubleshooting.md) for
cross-cutting install/import/backend/checkpoint routing. Workflow-specific
failures live in each sub-skill's nearest `references/troubleshooting.md`.

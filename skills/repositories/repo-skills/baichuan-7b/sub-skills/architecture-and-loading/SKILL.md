---
name: architecture-and-loading
description: "Operate Baichuan-7B architecture, local source loading, tiny
  synthetic forward checks, Hugging Face inference loading, and generation/cache
  preparation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Architecture and Loading

Use this sub-skill when the user asks to load or inspect Baichuan-7B model code, reason about `BaiChuanConfig` defaults, construct `BaiChuanForCausalLM`, run a tiny local forward smoke, understand `generate()`/cache preparation, or debug attention/head shape constraints.

## Route here for

- Loading Baichuan-7B or compatible local weights with Hugging Face `AutoTokenizer` / `AutoModelForCausalLM` and `trust_remote_code=True`.
- Inspecting the local classes `BaiChuanConfig`, `Model`, `Attention`, `DecoderLayer`, and `BaiChuanForCausalLM`.
- Running a safe config-only smoke that needs no official 7B weights, no datasets, and no network.
- Explaining generation preparation: `past_key_values`, `attention_mask`, `position_ids`, `use_cache`, and newer Transformers generation warnings.
- Diagnosing invalid `hidden_size` / `num_attention_heads` combinations or direct attention-mask shape errors.

## Do not route here for

- C-Eval/MMLU benchmark data, scoring commands, or result files: use sibling `evaluation-workflows`.
- DeepSpeed pretraining, corpus shards, tokenizer placement for training, hostfiles, or cluster launch commands: use sibling `pretraining-and-deepspeed`.
- General package installation decisions that affect multiple workflows: start at the parent root skill and shared troubleshooting.

## Operating map

1. For a quick answer, read [workflows](references/workflows.md) first.
2. For local source verification, run [scripts/local_model_smoke.py](scripts/local_model_smoke.py) with `--repo-root /path/to/Baichuan-7B`.
3. For known failures, read [local troubleshooting](references/troubleshooting.md), then escalate cross-cutting install/backend issues to [shared troubleshooting](../../references/troubleshooting.md).
4. For broader API placement, use the parent [Baichuan-7B repo skill](../../SKILL.md) and shared [API reference](../../references/api-reference.md).

## Minimal safe smoke

```bash
python sub-skills/architecture-and-loading/scripts/local_model_smoke.py --repo-root /path/to/Baichuan-7B
```

Expected coverage: local source import, tiny `BaiChuanConfig`, eval-mode `BaiChuanForCausalLM` forward, logits shape `(1, 4, 32)`, finite causal-LM loss, cache-aware `prepare_inputs_for_generation`, invalid head-divisibility failure, and `has_generate` reporting.

Add `--cuda` only when the user explicitly wants a CUDA availability/allocation check; it does not download or run the real 7B model.

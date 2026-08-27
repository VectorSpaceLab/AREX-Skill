---
name: inference-evaluation
description: "Guides RWKV-LM RWKV-7 inference modes, checkpoint/tokenizer setup,
  prompt sampling, and MMLU-style evaluation troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RWKV inference and evaluation

Use this route when the request mentions running an RWKV checkpoint, GPT-mode,
RNN-mode, fast decoding, `rwkv_v7_demo`, `RWKV_RNN`, sampling settings, model
state, tokenizer setup, MMLU, multiple-choice scoring, or generation debugging.

## Route by task

- **Choose a demo path**: read [inference-workflows.md](references/inference-workflows.md)
  to decide between GPT-mode prefill, RNN-mode token-by-token decoding, and the
  fast mixed path.
- **Build a safe config**: use [build_inference_config.py](scripts/build_inference_config.py)
  to emit a JSON config with checkpoint, architecture, sampling, and mode fields.
- **Adapt MMLU or another MCQ evaluation**: read
  [evaluation-workflows.md](references/evaluation-workflows.md) and use
  [render_mmlu_prompt.py](scripts/render_mmlu_prompt.py) to validate the prompt
  shape.
- **Debug a failed run**: read [troubleshooting.md](references/troubleshooting.md)
  before changing dtype, backend, or tokenizer.

## Inference decisions

1. Confirm checkpoint family and dimensions (`n_layer`, `n_embd`, `vocab_size`,
   head size). The demo scripts hard-code these values; a mismatch can produce
   shape errors or nonsense logits.
2. Confirm tokenizer family. Current RWKV-7 demos use `rwkv_vocab_v20230424`
   with vocabulary size 65,536. Older v4/v4neo examples may use the 20B JSON
   tokenizer and 50k vocabulary.
3. Choose mode:
   - GPT-mode is convenient for full-sequence prefill and comparison.
   - RNN-mode is appropriate for stateful autoregressive generation.
   - Fast mixed mode combines prefill and decoding but depends on CUDA custom
     extension compilation and a compatible GPU/toolkit.
4. Keep prompt, temperature, `top_p`, `top_k`, length, and trial count explicit
   in a config file or command record.
5. Treat local model paths from repository examples as placeholders. Replace
   them with the user's actual checkpoint and do not publish private paths.

## Evaluation decisions

The MMLU script formats each sample as a four-choice prompt and scores the
last-token probabilities for tokens corresponding to `" A"`, `" B"`, `" C"`,
and `" D"`. Adapt that pattern carefully when choices are not single tokens or
when a different tokenizer is used.

Full evaluation requires a checkpoint, tokenizer, dataset, and often GPU time.
For local validation, test prompt rendering and answer-token mapping before
running the complete benchmark.

## Handoff

Route data preparation or training commands to `training-data`. Route tensor
names, Qwen comparison, or context-parallel state composition to
`architecture-reference`. Route RWKV-8/ROSA toy scripts to `rosa-experiments`.

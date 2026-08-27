---
name: evaluation
description: "Guides ChatGLM2-6B C-Eval dataset preparation, benchmark command
  planning, schema validation, score interpretation, and safe handling of
  expensive CUDA evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# ChatGLM2-6B Evaluation

Use this route for the repository's C-Eval benchmark script, validation/test
JSONL layout, answer extraction, accuracy aggregation, or benchmark
troubleshooting. Use [`ptuning`](../ptuning/SKILL.md) for evaluation of tuned
checkpoints and [`chat-and-demos`](../chat-and-demos/SKILL.md) for ordinary
local generation.

## Before a benchmark run

1. Acquire the C-Eval data through an approved source and place it under a
   model-specific `evaluation/CEval/` directory. Do not bundle or download it
   from the skill helper.
2. Run the bundled validator before allocating a GPU:
   `python sub-skills/evaluation/scripts/validate_ceval_layout.py --root evaluation/CEval`.
3. Ensure a compatible model/tokenizer is cached, CUDA is available, and the
   model uses the same tokenizer/model revision. The source script loads
   `THUDM/chatglm2-6b` in BF16 and calls `.cuda()`.
4. Treat the benchmark as expensive: the script iterates every subject JSONL,
   batches by eight, generates up to 512 new tokens, then performs a second
   forward pass over answer-extraction prompts.

Read [`ceval-workflow.md`](references/ceval-workflow.md) for the scoring
algorithm and val/test adaptation. Read [`troubleshooting.md`](references/troubleshooting.md)
when a layout, label, tokenizer, or CUDA error occurs. The validator is a
schema/layout check only; it never loads model weights or claims benchmark
accuracy.

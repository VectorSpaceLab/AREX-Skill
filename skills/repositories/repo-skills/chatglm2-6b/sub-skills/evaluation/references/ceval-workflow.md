# C-Eval Workflow

## Data layout

The repository's evaluation notes expect a processed C-Eval directory under
`evaluation/CEval`. Validation files are discovered recursively with
`CEval/val/**/*.jsonl`; to work with the benchmark test set, adapt the glob to
`CEval/test/**/*.jsonl` and follow C-Eval's official submission format.

Each JSONL record must provide at least:

- `inputs_pretokenized`: the question text used to build the prompt.
- `label`: the correct multiple-choice index. The source compares the model's
  predicted index to this value; the bundled validator accepts integer `0`–`3`
  and can normalize `A`–`D` with an explicit warning.

Validate before a GPU run:

```text
python sub-skills/evaluation/scripts/validate_ceval_layout.py \
  --root evaluation/CEval --split val --strict-label-type
```

## Scoring flow from the source

1. Load the tokenizer and ChatGLM2-6B model with remote code, BF16, and CUDA.
2. Build `[Round 1]` prompts containing each question and an answer marker.
3. Generate an intermediate answer with `do_sample=False`, `max_new_tokens=512`,
   and tokenization capped at `max_length=2048`.
4. Append the extraction phrase `综上所述，ABCD中正确的选项是：` to the question
   plus generated reasoning.
5. Run a second forward pass with `return_last_logit=True`, select logits for
   the tokenizer ids of `A`, `B`, `C`, and `D`, and choose the maximum.
6. Print per-file accuracy and compute a dataset-size-weighted aggregate.

The source uses a DataLoader batch size of eight. Reduce the batch or token
limits if the model's KV cache exceeds available VRAM. Do not compare a result
from a different prompt, tokenizer revision, or label encoding as if it were
comparable.

## Validation and result handling

The repository notes report that benchmark results may vary slightly. Preserve
per-subject outputs and the aggregate denominator when comparing runs. For a
test-set submission, adapt only the split glob and the result serialization
needed by the official C-Eval instructions; do not submit generated data without
reviewing its license and benchmark rules.

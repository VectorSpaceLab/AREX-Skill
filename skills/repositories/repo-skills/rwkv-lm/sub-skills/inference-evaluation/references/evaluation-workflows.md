# RWKV evaluation workflows

## MMLU-style multiple choice

`rwkv_mmlu_eval.py` uses a prompt that embeds the question and four answer
choices, then scores the next-token logits for the tokens representing
`" A"`, `" B"`, `" C"`, and `" D"`. This is simple and effective only when the
answer labels are single tokens in the selected tokenizer.

Key constraints:

- The tokenizer must make `" A"`, `" B"`, `" C"`, and `" D"` each a single token.
- Choice order matters; if you shuffle choices, you must also remap the gold
  answer index.
- The prompt should be stripped and normalized consistently before encoding.
- `torch.no_grad()` and a fixed seed make the score comparison repeatable.

## Adapting to another dataset

To adapt the script to a different multiple-choice benchmark:

1. Replace the subject/question/choice rendering.
2. Validate that every label token is a single token for the selected tokenizer.
3. Keep a single ground-truth index per sample.
4. Compute argmax over the label-token logits.
5. Decide whether to shuffle choices. If so, shuffle after recording the gold
   answer text and before tokenization.

## Local verification ideas

Safe, low-cost checks that do not require a full benchmark run:

- confirm prompt strings render correctly
- confirm the tokenizer encodes the label tokens as a one-token list
- confirm the selected checkpoint and mode can run a tiny prompt
- confirm the score extraction uses the final logit of the prefix sequence

## Troubleshooting notes

- If a label becomes multiple tokens, the scoring rule is invalid. Choose a
  different label scheme or tokenizer.
- If the script reports a dataset download failure, keep the check at the prompt
  formatting level unless the user authorizes network access.
- If a GPU-only checkpoint is unavailable, the prompt rendering logic can still
  be checked separately from the full evaluation run.

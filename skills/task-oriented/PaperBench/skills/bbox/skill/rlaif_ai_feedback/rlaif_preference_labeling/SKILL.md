---
name: rlaif_preference_labeling
description: Build RLAIF pairwise AI-feedback labels from label-token logits, optional chain-of-thought rationales, and swapped-order position-bias mitigation.
---

# RLAIF Preference Labeling

Use this skill when a recovery or implementation needs to convert two candidate responses into the soft AI preference label used by RLAIF. It is appropriate for summarization, helpful-dialogue, or harmless-dialogue pairwise comparisons where an LLM or deterministic scorer can return logits for displayed labels `1` and `2`.

Do not use this skill to train a reward model, score a single generation from 1 to 10, or update a policy. Those are separate RLAIF mechanisms.

## Inputs

- `task`: one of `summarization`, `helpful_dialogue`, or `harmless_dialogue`.
- `context`: source post or dialogue history.
- `response1`, `response2`: candidate responses in the original order.
- A labeler that returns logits for displayed labels `1` and `2`; in tests this is a deterministic fake.
- Optional flags for detailed preamble, chain-of-thought rationale, and swapped-order scoring.

## Outputs

- A normalized preference `[p_response1, p_response2]` over the original response order.
- Prompt and scoring records that identify displayed order, logits, rationale text, and remapped probabilities.
- No reward-model parameters, direct reward, policy update, or evaluation decision.

## Workflow

1. Build a pairwise prompt from the task preamble, context, response fields, and label ending.
2. If chain-of-thought is enabled, first request a rationale and append it before final label scoring.
3. Convert label logits for `1` and `2` to probabilities with stable softmax.
4. If position-bias mitigation is enabled, repeat scoring with the two responses swapped.
5. Remap swapped probabilities back to the original response identities.
6. Average original-order and remapped swapped-order preferences.
7. Return records that make the displayed-order mapping auditable.

## Validation

Run:

```bash
python scripts/preference_labeling.py --smoke
python tests/test_preference_labeling.py
```

The tests verify softmax conversion, swapped-order remapping, chain-of-thought prompt metadata, and the module boundary that preference labels must not contain reward or policy fields.

## Limitations

This skill can emulate the paper's label-token API, but it does not provide a real PaLM 2 labeler. Full paper-scale labeling requires an external LLM endpoint and the original preference datasets.

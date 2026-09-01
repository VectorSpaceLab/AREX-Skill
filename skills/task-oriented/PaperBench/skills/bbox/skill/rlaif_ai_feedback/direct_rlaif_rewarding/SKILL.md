---
name: direct_rlaif_rewarding
description: Compute direct-RLAIF rewards from one-to-ten score-token logits without training a separate reward model.
---

# Direct RLAIF Rewarding

Use this skill when a RLAIF experiment needs the paper's direct reward path: a scorer rates one generated response with score tokens `1` through `10`, the token logits become a score distribution, and the expected score is mapped to a normalized reward.

Do not use this skill for pairwise preference labeling or reward-model distillation. Direct-RLAIF is a single-response reward mechanism.

## Inputs

- `task`: `summarization` or `helpful_dialogue`.
- `context`: source post or dialogue history.
- `response`: generated text to score.
- A scorer that returns logits for score tokens `1` through `10`.

## Outputs

- `score_probabilities`: probabilities for scores 1 through 10.
- `expected_score`: the probability-weighted score.
- `normalized_reward`: expected score mapped from `[1, 10]` to `[-1, 1]`.
- Prompt metadata for auditing.

## Workflow

1. Build the direct scoring prompt for the task and candidate response.
2. Obtain logits for score tokens `1` through `10`.
3. Apply stable softmax over score-token logits.
4. Compute the expected score.
5. Normalize the reward with `((expected_score - 1) / 9) * 2 - 1`.
6. Check the reward remains inside `[-1, 1]`.

## Validation

Run:

```bash
python scripts/direct_reward.py --smoke
python tests/test_direct_reward.py
```

The tests verify normalization, monotonic score ordering, uniform-distribution behavior, and output bounds.

## Limitations

The bundled scorer is deterministic and is meant for reduced recovery only. A full d-RLAIF run needs an actual off-the-shelf LLM with score-token likelihoods during policy training.

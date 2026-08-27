# Hack EE Contest Format

The Hack EE contest challenges participants to recover plaintext token mappings
from encrypted/private token IDs for a Llama-family model.

## Objective

Each day, participants receive encrypted token IDs for prompts and model
responses. The goal is to provide mappings from encrypted token IDs to original
text tokens.

## Submission shape

A submission is a JSON object with a top-level `tokens` mapping:

```json
{
  "tokens": {
    "12": "an",
    "345": "swer",
    "678": " he"
  }
}
```

Rules for local validation:

- Top-level value must be a JSON object.
- `tokens` must be a JSON object.
- Token IDs should be strings containing non-negative integers.
- Mapped token text must be strings.
- Duplicate JSON keys are not reliably detectable after parsing; warn users to
  generate keys from a map/dictionary only once.

## Scoring described by the contest

- Correct mapping: `+10` points.
- Incorrect mapping: `-1` point.
- Daily winner: highest score, with earliest submission as tie-breaker.
- One submission per day.
- Grand prize: decode all provided tokens for a day without errors and provide
  reproducible code.
- Clues may be released; after a clue, the hinted token no longer earns points.
- Bonus: the daily winner may receive extra payout for tweeting the rarest token
  before the stated deadline, according to contest rules.

The generated skill cannot verify live leaderboard state, hint timing, portal
acceptance, or bonus eligibility. Treat those as external contest facts.

## Practical local workflow

1. Keep the encrypted input/output sequences, mapping guesses, and any hints in
   separate files.
2. Validate JSON shape before submission.
3. If using a local gold fixture for practice, score locally and inspect false
   positives/negatives.
4. Record the timestamp and rule assumptions before any live submission.
5. Submit only after the user confirms the final mapping and contest identity.

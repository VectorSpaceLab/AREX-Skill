# Security Contest Troubleshooting

## Submission JSON

| Symptom | Likely cause | Fix |
|---|---|---|
| JSON parser fails | Trailing comma, comments, or invalid quotes. | Use strict JSON with double quotes only. |
| Top-level `tokens` missing | Mapping object was submitted directly. | Wrap as `{"tokens": {...}}`. |
| Token ids are numbers instead of strings | JSON parser accepts them as object keys inconsistently across tools. | Emit ids as strings, e.g. `"12"`. |
| Mapping values are token IDs instead of token text | Misread expected mapping direction. | The contest example maps encrypted token id strings to original text token strings. |
| Duplicate ids disappear | JSON keeps only the last duplicate key in many parsers. | Generate submissions from one dictionary and check key counts before writing. |

## Scoring/rules

| Symptom | Likely cause | Fix |
|---|---|---|
| Score is lower than expected | Incorrect mappings incur `-1`, and hinted tokens may no longer count. | Track which guesses came from hints and validate on toy/gold data first. |
| Tie lost despite same score | Earlier submission is tie-breaker. | Record timestamps and avoid repeated attempts; only one submission per day is allowed. |
| Bonus not granted | Tweet/rare-token condition or deadline missed. | Treat bonus conditions as external contest state; do not automate without explicit approval. |

## Analysis pitfalls

- Frequency guesses are priors, not proof.
- LLM-as-judge losses may reward fluent but wrong decryptions.
- Hill climbing can overfit to released pairs and local minima.
- A mapping that works for a toy example may fail on the secret daily tokenizer.

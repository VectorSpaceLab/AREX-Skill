# Crosswords Troubleshooting

## Invalid action format

Likely cause: the move is not exactly `h1. apple` or `v3. panel`.

Recovery:

- keep the `h`/`v` prefix and the dot-space separator;
- ensure the word is exactly five letters;
- use lowercase in the candidate output even if the model produced mixed
  case.

## Proposal parsing returns nothing

Likely cause: the model did not emit `h1. apple (medium)` style lines.

Recovery:

- keep the confidence labels `certain`, `high`, `medium`, and `low`;
- ensure each candidate line contains exactly five alphabetic letters;
- lower temperature if the model starts inventing prose instead of rows.

## DFS prunes too aggressively

Likely cause: the current board state already contains a conflict or the
`impossible` count is too eager.

Recovery:

- inspect the rendered board before pruning;
- disable pruning once to confirm the path exists;
- reduce `max_per_state` only after the parser is stable.

## API and auth failures

Use the shared root troubleshooting file for OpenAI credential, endpoint,
and network errors.

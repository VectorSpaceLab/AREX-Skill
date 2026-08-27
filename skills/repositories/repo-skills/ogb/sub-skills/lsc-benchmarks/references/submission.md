# LSC submission notes

## File names

- `PCQM4M` -> `y_pred_pcqm4m.npz`
- `PCQM4Mv2` -> `y_pred_pcqm4m-v2_test-dev.npz` or
  `y_pred_pcqm4m-v2_test-challenge.npz`
- `MAG240M` -> `y_pred_mag240m.npz`, `y_pred_mag240m_test-dev.npz`, or
  `y_pred_mag240m_test-challenge.npz`
- `WikiKG90M` -> `t_pred_wikikg90m.npz`
- `WikiKG90Mv2` -> `t_pred_wikikg90m-v2_test-dev.npz` or
  `t_pred_wikikg90m-v2_test-challenge.npz`

## Shape expectations

- `PCQM4M` / `PCQM4Mv2` use 1-D float predictions.
- `MAG240M` uses 1-D class predictions.
- `WikiKG90M` / `WikiKG90Mv2` use top-10 ranked candidate arrays.

## Practical guidance

- Check the exact split name before constructing a submission array.
- Keep `test-dev` and `test-challenge` arrays separate for the `v2` tasks.
- If the user only needs a quick check, use the bundled evaluator smoke script
  rather than the full dataset download.

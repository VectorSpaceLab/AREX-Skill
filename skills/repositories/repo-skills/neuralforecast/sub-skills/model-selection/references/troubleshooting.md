# Model Selection Troubleshooting

## Purpose

Read this when the chosen model family does not match the data shape or the
optional dependency stack is incomplete.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `n_series` required | The selected family is multivariate-first. | Pass `n_series` or choose a univariate model. |
| Exogenous-list error | The model does not support the requested exogenous variables. | Switch to a model family that accepts those features. |
| `input_size` / horizon mismatch | The constructor choices do not fit the desired forecast window. | Reduce the horizon or increase the input size. |
| `TimeLLM` import lacks features | `transformers` and related optional packages are missing. | Install the optional stack only if the user really needs TimeLLM. |
| `xLSTM` import lacks features | `xlstm` package is missing. | Install the optional stack only if the user really needs xLSTM. |
| Alias confusion | The user is mixing model class names and wrapper names. | Use the public model list from `../../scripts/list_models.py`. |

## Next checks

1. Run `../../scripts/list_models.py` and compare the chosen model family.
2. If the data shape is unclear, route to `../data-and-exogenous/SKILL.md`.
3. If the user only needs the run itself, route to `../core-forecasting/SKILL.md`.

## When to stop

If the user wants a probabilistic loss or interval story, route to
`probabilistic-losses`. If the user wants tuning or distributed execution,
route to `tuning-and-distributed`.

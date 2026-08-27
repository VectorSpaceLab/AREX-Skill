# Forward-Forward Troubleshooting

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError: cannot import name 'Generator' from 'collections'` | The source-era code is running on Python 3.10+. | Use Python 3.9 or patch the import to `collections.abc.Generator`. |
| `predicted_tokens must be specified for NLP model` | The NLP branch requires the keyword argument. | Re-run with `predicted_tokens` in `kwargs`. |
| MNIST or Aesop Fables download fails | The loader depends on external dataset/network access. | Reuse cached data or retry in a network-enabled environment. |
| `model_type` is invalid | The public API only accepts the three source-defined values. | Choose `progressive`, `recurrent`, or `nlp`. |
| Accuracy or perplexity is poor | The hyperparameters or device choice are not appropriate for the branch. | Tune `epochs`, `hidden_size`, `theta`, and `batch_size`, then retry. |

## Next step

If the issue is about dataset layout or the Python-version constraint, start from `data-and-compatibility.md`. If it is about the optimizer stack or torch installation, consult the root installation notes first.

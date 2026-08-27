# Conditioning and Guidance Troubleshooting

## Class labels wrong shape or dtype

CFG `classes` and external classifier labels `y` should be integer tensors shaped `(batch,)`. Their batch size must match the image batch or the number of requested class-conditioned samples.

## CFG sinusoidal assertion

`classifier_free_guidance.GaussianDiffusion` asserts that the model does not use random/learned sinusoidal conditioning. Construct `CFGUnet(..., learned_sinusoidal_cond=False, random_fourier_features=False)`.

## Guidance too strong or oversaturated

High `cond_scale` can overemphasize the class direction. Lower `cond_scale`, use `rescaled_phi` such as `0.7`, or compare with `cond_scale=1.0` to isolate base model quality.

## CFG++ confusion

`use_cfg_plus_plus=True` changes the CFG sampler model-prediction path and is most relevant to sampling. It is not a training-loss option and does not fix bad class labels or an untrained model.

## External `cond_fn` returns errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `element 0 of tensors does not require grad` | `cond_fn` did not use `torch.enable_grad()` and `requires_grad_(True)` on detached `x`. | Follow the recipe in `api-reference.md`. |
| shape mismatch in mean update | Returned gradient shape differs from `x`. | Return a tensor exactly shaped like `x`. |
| device mismatch | Classifier, `y`, or returned gradient is on another device. | Move classifier and labels to the same device as `x`. |
| index error selecting labels | `y` batch size or class values are wrong. | Use `y.view(-1)` with one label per batch item and valid class ids. |

## XMWrapper `candidates` assertion

`candidates` must be at least 1. Use `candidates=1` to disable multi-candidate behavior while keeping the wrapper.

## XMWrapper cannot find a tensor input

For `candidates > 1`, the wrapper discovers batch size from the first non-scalar tensor in `args` / `kwargs`. Pass the data tensor positionally or as a keyword argument.

## Missing `random_times`

If `random_time_kwarg` (default `times`) is absent, `XMWrapper` calls `flow_model.random_times(batch)`. Some wrappers do not expose that method. Fix by passing the time tensor explicitly with the expected keyword, or set `random_time_method` / `random_time_kwarg` to names supported by the wrapped model.

## Candidate memory growth

The wrapper repeats batch-shaped tensors to `(batch * candidates, ...)`. If memory grows too much, reduce `candidates`, reduce batch size, or set `max_batch_size` to chunk candidate evaluation.

## `loss_reduction` behavior

If the wrapped model forward signature includes `loss_reduction`, `XMWrapper` uses `loss_reduction='none'` internally so it can select the minimum candidate per original sample. If a custom model lacks per-sample loss support, verify that scalar loss behavior still matches the intended selection semantics.

# Residual Quantizers Troubleshooting

## Quick symptom table

| Symptom | Likely cause | Fix |
|---|---|---|
| `get_output_from_indices` does not match a previous `quantized` tensor | Indices were generated from a different model state, codebooks changed by EMA, or training-time stochastic/dropout behavior was active. | Generate reconstruction indices in `.eval()`; save/load the same model state with the indices; use `freeze_codebook=True` for training-mode checks that must compare immediately. |
| Target-index loss mode fails with a message about dropped residual VQ indices | The supplied `indices` contain `-1` from quantize dropout. | Use `.eval()` to create full-depth labels, or filter/regenerate targets. `-1` marks skipped layers and is not a valid class label for cross-entropy mode. |
| Indices contain `-1` unexpectedly | `quantize_dropout=True` and the model is in training mode. | Switch to `.eval()` for deterministic full-depth indices, or intentionally handle `-1` as skipped fine residual layers. |
| Constructor assertion when using `eval_beam_size` | `eval_beam_size` was set without `beam_size`. | Set both, e.g. `beam_size=2, eval_beam_size=3`, or omit `eval_beam_size`. |
| Beam search is too slow or runs out of memory | Beam expansion multiplies candidate tensors by beam size across sequence length, depth, and codebook choices. | Start with `beam_size=2`, shorten sequences, reduce codebook/depth, lower eval beam, or turn off beam search for training. |
| `shared_codebook=True` fails with tuple `codebook_size` | Shared residual layers require a uniform codebook size. | Use a single integer `codebook_size`, or disable sharing for layer-specific tuple sizes. |
| `GroupedResidualVQ` assertion on input dimension | `dim` is not divisible by `groups`, or the tensor feature/channel dimension is not `dim`. | Pick `groups` that divides `dim`; for image maps with `accept_image_fmap=True`, ensure the channel dimension equals `dim`. |
| Grouped reconstruction has wrong shape or wrong content | Group axis was removed or transposed. | Preserve index shape `(groups, batch, sequence, num_quantizers)` and pass it unchanged to `grouped_vq.get_output_from_indices(indices)`. |
| `ResidualVQ` assertion about multi-headed codes | `heads` was set above `1`. | ResidualVQ supports only `heads=1`; use base `VectorQuantize` for multi-headed single-stage VQ or manually split features. |
| DiVeQ model does not show expected commitment/EMA behavior | `diveq=True` changes codebook learning to gradient-based updates. | Optimize downstream loss through quantized outputs; do not expect EMA updates or commitment auxiliary loss to update codebooks. |

## Eval-mode reconstruction from indices

`get_output_from_indices(indices)` decodes indices using the current codebooks. It does not store historical code vectors inside the indices. Exact reconstruction requires the same quantizer state used to create the indices.

Recommended pattern:

```python
residual_vq.eval()
with torch.no_grad():
    quantized, indices, _ = residual_vq(x)
    reconstructed = residual_vq.get_output_from_indices(indices)
assert torch.allclose(quantized, reconstructed, atol=1e-5)
```

If the comparison fails:

1. Confirm the same constructor options were used (`dim`, `codebook_dim`, `num_quantizers`, `codebook_size`, `shared_codebook`, `implicit_neural_codebook`, and `diveq`).
2. Load the exact same state dict before decoding.
3. Ensure the model is in `.eval()` when generating the indices.
4. Avoid a training forward that mutates EMA codebooks between producing `quantized` and decoding `indices`; if necessary, use `freeze_codebook=True` for the check.
5. Check for stochastic sampling temperature or dropout in training mode.

## Training dropout and `-1` indices

With `quantize_dropout=True`, training forwards randomly stop after a residual layer and fill later residual-layer indices with `-1`. This is expected.

Implications:

- `-1` means the fine residual layer was skipped and should contribute zero during reconstruction.
- `get_output_from_indices` can mask `-1` entries when the model was configured for quantize dropout.
- Forward target-index loss mode rejects `-1` because cross-entropy labels must be valid code indices.
- `.eval()` disables quantize dropout and produces full-depth indices.
- If you pass a shorter/coarser index tensor, the model must have `quantize_dropout=True`; otherwise shorter depth is invalid.

For reproducible tests, pass `rand_quantize_dropout_fixed_seed=` to `forward`.

## Tuple `codebook_size` semantics

`codebook_size` can be an integer or a tuple.

- Integer: every residual layer has the same codebook size, and `num_quantizers` controls depth.
- Tuple: each tuple element is the size of one residual layer. If `num_quantizers` is omitted, depth is inferred from tuple length.
- Tuple length must equal `num_quantizers` if both are supplied.
- Non-uniform tuple sizes produce a tuple from the `codebooks` property rather than one stacked tensor.
- `shared_codebook=True` requires a uniform codebook size; do not use it with `(5, 128, 256)`-style heterogeneous sizes.

## Grouped index shape

Default sequence layout for grouped residual VQ is:

```text
x:        (batch, sequence, dim)
indices: (groups, batch, sequence, num_quantizers)
losses:  (groups, num_quantizers) in common reduced modes
```

Common mistakes:

- Treating grouped indices as `(batch, sequence, groups, num_quantizers)`.
- Flattening the group axis before reconstruction.
- Passing only one group's indices to `GroupedResidualVQ.get_output_from_indices`.
- Choosing `groups` that does not divide `dim`.

If you need to decode one group separately, use the corresponding underlying group residual quantizer intentionally. Otherwise pass the full grouped index tensor to `GroupedResidualVQ.get_output_from_indices`.

## Beam search memory and runtime

Beam search uses `topk=beam_size` inside each residual layer and keeps candidate residuals, indices, losses, and scores. Symptoms of too-large settings include slow training, high CPU/GPU memory, or process termination.

Tuning order:

1. Start with greedy mode (`beam_size=None`) and verify shapes/losses.
2. Try `beam_size=2` on short sequences.
3. Use a smaller `eval_beam_size` if eval is too slow; use a larger one only after memory is measured.
4. Reduce `num_quantizers`, `codebook_size`, or sequence length for smoke checks.
5. Keep `beam_score_quantizer_weights` length exactly equal to residual depth.

`eval_beam_size` cannot be configured by itself; it depends on `beam_size` existing in the constructor.

## DiVeQ vs auxiliary/EMA losses

`diveq=True` is not a minor loss flag. It changes codebook learning:

- EMA updates are disabled.
- Codebooks become learnable.
- Input-gradient routing is disabled.
- Commitment weight is set to `0`.
- `quant_grad_frac` is forced to `1.0`.

Use DiVeQ when a downstream differentiable loss should update codebooks by gradient descent. If the training recipe expects EMA updates, commitment loss tuning, dead-code expiration, or auxiliary VQ losses, keep `diveq=False` and configure the underlying VQ arguments instead.

## Implicit neural codebook pitfalls

`implicit_neural_codebook=True` transforms codebooks with residual MLPs conditioned on the current quantized output.

Watch for:

- Higher memory/compute than plain residual VQ.
- Learnable codebooks and no EMA updates.
- Extra sensitivity to `mlp_kwargs` depth/hidden width.
- More complicated reconstruction: decode indices only with the same model state, because later code vectors depend on previous quantized outputs.

Start with small codebooks and short sequences, then scale after a reconstruction check passes.

## Shared codebook update expectations

When `shared_codebook=True`, all layers point at the same codebook object. EMA or in-place optimizer updates are coordinated after the residual stack, not independently after each layer. This is expected and is why uniform codebook size is required.

If shared-codebook training appears unstable:

- Lower `sample_codebook_temp` for less stochastic sampling.
- Verify the codebook size is large enough for the combined residual workload.
- Check that `commit_loss` reduction in your training loop gives each layer an intended weight.
- Use a short eval reconstruction check to separate codebook state problems from downstream model loss problems.

# Lookup-Free and Latent Troubleshooting

## `codebook_size` is not a power of two

Symptom:

```text
AssertionError: your codebook size must be a power of 2 for lookup free quantization
```

Applies to `LFQ`, `ResidualLFQ`, `GroupedResidualLFQ`, and `EvoLFQ` when it constructs an internal LFQ.

Fix:

- Pick `codebook_size = 2 ** bits`, such as 16, 256, 4096, or 65536.
- Remember that `codebook_dim = log2(codebook_size)`, not the embedding dimension.
- For multiple codebooks, internal width is `log2(codebook_size) * num_codebooks`.

## LFQ dimension mismatch

Symptom:

```text
AssertionError: expected dimension of ... but received ...
```

Likely causes:

- Rank-3 LFQ input is expected as `(batch, seq, dim)`. A tensor shaped `(batch, dim, seq)` will be read as having feature dimension `seq`.
- Rank-4 and rank-5 LFQ inputs default to channel-first `(batch, dim, ...)`; a channel-last image will be misread unless rearranged or `channel_first=False` is set deliberately.
- `dim` was set to the model hidden size, but the actual tensor's feature axis differs.

Fix:

```python
# sequence
x = x.reshape(batch, seq, dim)

# image/video default
x = x.reshape(batch, dim, height, width)
video = video.reshape(batch, dim, time, height, width)
```

If `dim != log2(codebook_size) * num_codebooks`, LFQ will use projections by default. That is valid, but exact no-projection binary width calculations no longer apply.

## `num_codebooks > 1` and missing codebook axis

Symptom:

```text
AssertionError
```

Cause:

- LFQ and LatentQuantize require `keep_num_codebooks_dim=True` when `num_codebooks > 1`. The constructors set this automatically by default; overriding it to `False` is invalid.

Fix:

- Remove `keep_num_codebooks_dim=False`.
- Expect returned indices to include a final `num_codebooks` axis.

## LFQ entropy mask errors or misleading losses

Symptoms:

- Shape/indexing errors when passing `mask`.
- Entropy or commitment loss does not reflect padded tokens.
- Reconstruction from `indices_to_codes` is correct but auxiliary loss is unexpected.

Facts:

- `mask` affects training-time entropy and commitment losses only; it does not zero quantized outputs or indices.
- For sequence LFQ, use boolean shape `(batch, seq)`.
- For image/video LFQ, mask shape must match the flattened token structure used internally. Start with simple batch/token masks and verify a tiny forward before using complex spatial masks.
- `frac_per_sample_entropy < 1` randomly samples tokens for per-sample entropy, so tiny batches can show variance.

Fix pattern:

```python
lfq.train()
mask = torch.ones(batch, seq, dtype=torch.bool, device=x.device)
mask[:, padded_start:] = False
(ret, breakdown) = lfq(x, mask=mask, return_loss_breakdown=True)
```

Use eval mode or `entropy_loss_weight=0.0` when the task only needs deterministic index/code shape checks.

## LFQ return tuple unpacking mistakes

Symptom:

```text
ValueError: not enough values to unpack
```

or accidentally treating `return_loss_breakdown=True` as three direct outputs.

Fix:

```python
# Standard path
quantized, indices, aux_loss = lfq(x)

# With breakdown
(ret, breakdown) = lfq(x, return_loss_breakdown=True)
quantized, indices, aux_loss = ret
print(breakdown.per_sample_entropy, breakdown.batch_entropy, breakdown.commitment)
```

The namedtuple return behaves like a tuple, but the nested breakdown changes the outer structure.

## ResidualLFQ reconstruction mismatch

Symptoms:

- `get_output_from_indices(indices)` does not match a training-time output.
- Indices contain `-1`.

Facts and fixes:

- Set the module to eval mode before checking exact reconstruction. Training-time dropout and stochastic gradients can make expectations less direct.
- `-1` indices are used for dropped quantizers when `quantize_dropout=True`. Keep them; reconstruction treats them as zeroed later residual codes.
- If `dim != log2(codebook_size)`, the residual module uses learned projections. Reconstruct with the same module instance and weights.

## GroupedResidualLFQ group errors

Symptom:

```text
AssertionError
```

Likely causes:

- `dim` is not divisible by `groups`.
- In image mode, input channels do not equal `dim`.
- In sequence mode, the last axis does not equal `dim`.

Fix:

```python
model = GroupedResidualLFQ(dim=32, groups=4, codebook_size=256, num_quantizers=2)
x = torch.randn(batch, seq, 32)

image_model = GroupedResidualLFQ(
    dim=32,
    groups=4,
    accept_image_fmap=True,
    codebook_size=256,
    num_quantizers=2,
)
image = torch.randn(batch, 32, height, width)
```

Expect group-first indices, not batch-first group indices.

## LatentQuantize layout mismatch

Symptom:

```text
AssertionError: expected dimension of ... but found dimension of ...
```

Cause:

- LatentQuantize rearranges inputs as `(batch, dim, ...) -> (batch, ..., dim)`. It does not use LFQ's rank-3 `(batch, seq, dim)` convention.

Fix:

```python
# If source sequence is batch, seq, dim:
x_bsd = torch.randn(batch, seq, dim)
x_bds = x_bsd.transpose(1, 2)
quantized_bds, indices, loss = latent_q(x_bds)
quantized_bsd = quantized_bds.transpose(1, 2)
```

Use `(batch, dim, height, width)` for images and `(batch, dim, time, height, width)` for video.

## LatentQuantize integer `levels` fails without `codebook_dim`

Symptom:

```text
RuntimeError
```

during construction with `levels=5`.

Cause:

- A scalar `levels` value must be repeated across a known number of codebook dimensions, but `codebook_dim` defaults to `-1`.

Fix:

```python
latent_q = LatentQuantize(levels=5, dim=6, codebook_dim=3, num_codebooks=2)
```

If levels differ by latent dimension, pass a list instead:

```python
latent_q = LatentQuantize(levels=[5, 5, 8], dim=16)
```

## LatentQuantize `optimize_values` and in-place optimizer

Symptoms:

- Values unexpectedly appear in `parameters()`.
- An in-place codebook optimizer branch raises an attribute error in some package versions.

Facts:

- `optimize_values=True` stores `values_per_latent` as learnable parameters.
- `optimize_values=False` stores fixed tensors.
- The inspected implementation accepts `in_place_codebook_optimizer`, but its forward branch references an `optimize_values` attribute that is not set in the constructor. Avoid this branch unless your installed version has fixed it.

Safer choices:

```python
# Learn values through normal optimizer membership
latent_q = LatentQuantize(levels=[5, 5, 8], dim=16, optimize_values=True)
optimizer = torch.optim.AdamW(latent_q.parameters(), lr=1e-3)

# Fixed values
latent_q_fixed = LatentQuantize(levels=[5, 5, 8], dim=16, optimize_values=False)
```

## LatentQuantize indices-to-codes shape mismatch

Symptoms:

- `indices_to_codes(indices)` returns a channel-first tensor and the caller expected sequence-last.
- Multi-codebook indices are missing the final `num_codebooks` axis.

Fix:

- For multi-codebook setups, keep indices shape `(..., num_codebooks)`.
- `indices_to_codes` returns `(batch, dim, ...)`. Transpose it if the surrounding model uses `(batch, seq, dim)`.
- Use the same `LatentQuantize` instance for roundtrips so projection weights match.

## BinaryMapper logits have wrong final dimension

Symptom:

```text
AssertionError: logits must have a last dimension of ...
```

Fix:

- Construct `BinaryMapper(bits=k)` where `k == logits.shape[-1]`.
- The one-hot output has final size `2 ** k`; plan memory accordingly.

## BinaryMapper auxiliary loss shape surprises

Facts:

- `calc_aux_loss` defaults to training mode.
- `reduce_aux_kl_loss=True` returns a scalar mean.
- `reduce_aux_kl_loss=False` returns one loss per leading position.

Fix:

```python
one_hot, indices, aux = mapper(
    logits,
    return_indices=True,
    calc_aux_loss=True,
    reduce_aux_kl_loss=False,
)
assert aux.shape == logits.shape[:-1]
```

Use `deterministic=True` or `deterministic_on_eval=True` for reproducible eval checks.

## EvoLFQ construction fails

Symptoms:

```text
AssertionError: either lfq instance or dim / codebook_size must be supplied to EvoLFQ
AssertionError: pop_size must be greater than elitism_count
```

Fix:

```python
model = EvoLFQ(
    encoder=encoder,
    decoder=decoder,
    codebook_size=256,
    num_codebooks=2,
    dim=16,
    pop_size=8,
    elitism_count=1,
)
```

If you pass a prebuilt `lfq=LFQ(...)`, ensure the encoder output shape matches that LFQ's expected `dim`.

## EvoLFQ encoder/decoder shape mismatch

Symptoms:

- Decoder linear layer dimension error.
- Reconstructed tensor has an unexpected shape.
- `decode_bits` fails for multi-codebook bits.

Facts:

- Encoder output `(batch, dim)` is temporarily treated as one LFQ token and then squeezed back to `(batch, dim)` before the decoder.
- Encoder output `(batch, seq, dim)` stays sequence-shaped; the decoder must accept quantized sequence latents.
- For `num_codebooks > 1`, bit tensors passed to `decode_bits` can be flat `(..., codebook_dim * num_codebooks)` or grouped as `(..., num_codebooks, codebook_dim)` depending on the workflow. Test with a small population before a long evolve loop.

Fix checklist:

1. Print `encoder(x).shape`.
2. Check `lfq.dim` and `lfq.num_codebooks`.
3. Run one forward pass: `reconstructed, indices, aux = model(x)`.
4. Run `model.encode(x)` and `model.decode_bits(bits[:1])` on tiny data before calling `evolve`.
5. Keep `pop_size`, `generations`, and `batch_size` small for debugging.

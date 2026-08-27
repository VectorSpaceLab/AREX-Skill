# Retrieval Metrics

OpenCLIP validation computes paired retrieval metrics from already-generated feature tensors. The metric helper does not run model inference; prepare normalized image/audio and text features first.

## API

Use `open_clip_train.metrics.get_clip_metrics`:

```python
metrics = get_clip_metrics(
    image_features=image_features,
    text_features=text_features,
    logit_scale=logit_scale,
    image_key="image",
    text_key="text",
    retrieval_chunk_size=4096,
    retrieval_device=None,
    retrieval_dtype=torch.float32,
)
```

Despite the parameter name `image_features`, the training loop passes the task primary modality features. For CLAP-like paired validation this may use `image_key="audio"` and produce keys such as `audio_to_text_R@1`.

## Inputs

- `image_features` and `text_features` must be 2D tensors with matching shape `[num_items, feature_dim]`, or lists/iterables of 2D tensors that concatenate to matching shapes.
- All feature chunks must share the same feature dimension.
- `logit_scale` may be a scalar tensor or compatible scalar value.
- Empty inputs return empty rank arrays internally; normal validation should still avoid reporting retrieval metrics for zero samples.

The helper reports:

- `{image_key}_to_{text_key}_mean_rank`
- `{image_key}_to_{text_key}_median_rank`
- `{image_key}_to_{text_key}_R@1`, `R@5`, `R@10`
- `{text_key}_to_{image_key}_mean_rank`
- `{text_key}_to_{image_key}_median_rank`
- `{text_key}_to_{image_key}_R@1`, `R@5`, `R@10`

Ranks are zero-based internally and reported as one-based mean/median rank.

## Chunking

`DEFAULT_RETRIEVAL_CHUNK_SIZE` is `4096`.

- `retrieval_chunk_size > 0` limits both target-score and candidate-score matrix chunks.
- `retrieval_chunk_size=None` or `<= 0` resolves to one full matrix block over all items.
- Smaller chunks reduce peak matrix memory but increase loop overhead.
- The training validation path stores feature chunks on CPU, then sets `retrieval_device=device` only when chunking is active.

When users hit OOM in validation retrieval:

1. Reduce `--val-retrieval-chunk-size` first.
2. Keep `--val-retrieval-precision fp32` for stable ranking unless memory forces `model` precision.
3. Move retrieval to CPU only if GPU memory is the bottleneck and runtime is acceptable.
4. Confirm feature tensors are not accidentally kept with gradients; validation should use inference/no-grad paths.

## Precision and Device

`retrieval_dtype` accepts:

- `torch.float32` or the string-equivalent CLI path `--val-retrieval-precision fp32`.
- `"model"`, which keeps the feature dtype selected by the model/precision path.
- A concrete `torch.dtype`.

Unsupported dtype strings raise `ValueError`.

`retrieval_device` accepts `None`, a device string, or a `torch.device`. If omitted, the first non-empty image feature tensor's device is used. The helper casts each chunk to the resolved retrieval device and dtype before matrix multiplication.

## Tie Handling

OpenCLIP ranks use deterministic tie-breaking:

- A candidate with a strictly greater score ranks ahead.
- A candidate with an equal score and lower paired index also ranks ahead.

This makes chunked metrics match the full-matrix reference implementation even when features are identical or heavily quantized.

## Validation Loop Integration

In the task-era validation loop:

- Paired outputs expose `task.primary_key + "_features"` and `text_features`.
- Generative-only validation may report only caption/generative loss and skip retrieval metrics.
- Features are appended to CPU lists before metric calculation to reduce device memory pressure.
- `logit_scale` is moved to CPU before being passed into `get_clip_metrics`, then copied to the retrieval device internally.

Route feature generation/preprocessing questions to `../model-inference/SKILL.md` or `../audio-clap/SKILL.md`; keep this reference focused on metric calculation and memory trade-offs.

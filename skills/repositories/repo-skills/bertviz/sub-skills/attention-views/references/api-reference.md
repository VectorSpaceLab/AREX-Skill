# API reference

## Functions

### `bertviz.head_view.head_view`
```python
head_view(
    attention=None,
    tokens=None,
    sentence_b_start=None,
    prettify_tokens=True,
    layer=None,
    heads=None,
    encoder_attention=None,
    decoder_attention=None,
    cross_attention=None,
    encoder_tokens=None,
    decoder_tokens=None,
    include_layers=None,
    html_action='view'
)
```

### `bertviz.model_view.model_view`
```python
model_view(
    attention=None,
    tokens=None,
    sentence_b_start=None,
    prettify_tokens=True,
    display_mode='dark',
    encoder_attention=None,
    decoder_attention=None,
    cross_attention=None,
    encoder_tokens=None,
    decoder_tokens=None,
    include_layers=None,
    include_heads=None,
    html_action='view'
)
```

### `bertviz.util.format_attention`
```python
format_attention(attention, layers=None, heads=None)
```

### Related helpers
- `bertviz.util.format_special_chars(tokens)` strips `Ġ`, `▁`, and `</w>` for display.
- `bertviz.util.num_layers(attention)` returns the number of layers.
- `bertviz.util.num_heads(attention)` reads the number of heads from the first layer.

## Attention layout contracts

BertViz expects a list of per-layer tensors, not a single stacked tensor.

### Self-attention
- Each layer tensor shape: `(1, num_heads, sequence_length, sequence_length)`
- `tokens` length must equal `sequence_length`

### Encoder-decoder attention
- `encoder_attention`: `(1, num_heads, encoder_sequence_length, encoder_sequence_length)`
- `decoder_attention`: `(1, num_heads, decoder_sequence_length, decoder_sequence_length)`
- `cross_attention`: `(1, num_heads, decoder_sequence_length, encoder_sequence_length)`
- `encoder_tokens` length must equal `encoder_sequence_length`
- `decoder_tokens` length must equal `decoder_sequence_length`

### `format_attention`
- Accepts the per-layer attention list plus optional zero-indexed `layers` and `heads` selections.
- Requires each selected layer tensor to be 4D.
- Squeezes the batch dimension from each layer, optionally filters heads, and stacks the result.
- The returned tensor has shape `(selected_layers, selected_heads, query_length, key_length)` after the batch dimension is removed.

## Parameter behavior

### Self-attention mode
- `attention` plus `tokens` is the standard path.
- `sentence_b_start` enables the sentence-pair dropdown and slices tokens into A/B spans.
- `prettify_tokens=True` removes common wordpiece markers after validation.
- `head_view` uses `layer` and `heads` as initial selections; it does **not** expose `include_heads`.
- `model_view` uses `include_layers` and `include_heads` to filter the rendered grid.

### Encoder-decoder mode
- Provide `encoder_attention`, `decoder_attention`, or `cross_attention` in any combination.
- When multiple blocks are supplied, the UI adds an attention dropdown.
- `cross_attention` always maps decoder tokens on the left to encoder tokens on the right.

### Display and export
- `display_mode` accepts `dark` or `light` in `model_view`.
- `html_action='view'` displays in notebook contexts.
- `html_action='return'` returns an `IPython.display.HTML` object whose `.data` contains the HTML source.

## Validation behaviors

- Missing `tokens` for self-attention raises `ValueError("'tokens' is required")`.
- Mixing self-attention arguments with encoder-decoder arguments raises a conflict error.
- Missing `encoder_tokens`, `decoder_tokens`, or both raises a mode-specific `ValueError`.
- `layer` must be present in `include_layers` when `layer` is supplied.
- Token/attention length mismatches raise a shape error before rendering.
- Invalid `html_action` raises a `ValueError`; only `view` and `return` are supported.
- A non-4D attention tensor triggers the dimensionality error from `format_attention`, which usually means `output_attentions=True` was omitted or the input is not a Hugging Face-style attention tuple.

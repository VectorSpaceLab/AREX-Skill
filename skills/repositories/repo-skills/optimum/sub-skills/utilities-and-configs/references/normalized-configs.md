# Normalized configs

Optimum normalized configs wrap heterogeneous Transformers-style config objects so exporter, dummy-input, and optimization helpers can use stable names such as `hidden_size`, `num_attention_heads`, and `image_size` even when a model family stores those values under different attributes.

## Base contract

`NormalizedConfig(config, allow_new=False, **kwargs)` stores the original `config` and lets callers access normalized attributes.

Resolution behavior:

1. Attribute access is uppercased and looked up on the normalized class, for example `normalized.hidden_size` uses class attribute `HIDDEN_SIZE`.
2. The mapped value can be a nested path such as `text_config.hidden_size`; each path component is resolved on the wrapped config.
3. If the direct attribute is absent, Optimum falls back to the wrapped config's `attribute_map` if present.
4. If the attribute still cannot be found, `AttributeError` is raised.
5. `has_attribute(name)` returns a boolean by attempting the same lookup.

`with_args(allow_new=False, **kwargs)` returns a partial constructor that overrides the class mapping without defining a new class. Keyword names are normalized attribute names; values are source attribute names or dotted paths.

## Built-in normalized classes

| Class | Typical fields |
| --- | --- |
| `NormalizedTextConfig` | `vocab_size`, `hidden_size`, `num_layers`, `num_attention_heads`, `eos_token_id` |
| `NormalizedTextConfigWithGQA` | Text fields plus `num_key_value_heads` for grouped-query attention models |
| `NormalizedSeq2SeqConfig` | Text fields plus encoder/decoder layer and attention-head aliases |
| `NormalizedVisionConfig` | `image_size`, `num_channels`, `input_size` |
| `NormalizedSegformerConfig` | Vision fields plus list-to-zero handling for `hidden_sizes`/heads where downstream optimizers infer sizes |
| `NormalizedTextAndVisionConfig` | Dispatches text and vision fields through configured nested subconfigs |
| `NormalizedEncoderDecoderConfig` | Delegates to configured encoder/decoder normalized config classes |
| `NormalizedTimeSeriesForecastingConfig` | `num_input_channels`, `context_length` |

Several family-specific aliases are implemented as `with_args` partials, including BART-like, GPT-2-like, T5-like, MPT, GPT-BigCode, Whisper-like, TrOCR-like, Speech-to-Text-like, Bloom, DistilBERT, GPT-Neo, and Pix2Struct mappings.

## NormalizedConfigManager

`NormalizedConfigManager` maps `config.model_type` strings to normalized config classes.

Use:

```python
from optimum.utils.normalized_config import NormalizedConfigManager

normalized_cls = NormalizedConfigManager.get_normalized_config_class(config.model_type)
normalized = normalized_cls(config)
```

`check_supported_model(model_type)` and `get_normalized_config_class(model_type)` raise `KeyError` for unsupported model types and include the supported model-type list in the error message. The manager covers many common text, seq2seq, GQA, and vision model families, but it is not universal. For unsupported or private model types, use `NormalizedConfig.with_args` when the required fields are known.

## Difficult case: nonstandard exporter config

If an exporter needs dummy inputs for a nonstandard config, do not mutate the model config. Build a normalized wrapper that translates fields:

```python
from types import SimpleNamespace
from optimum.utils.normalized_config import NormalizedTextConfig

raw = SimpleNamespace(
    token_count=32000,
    model_width=4096,
    depth=32,
    attention_heads=32,
    eos=2,
)
NormalizedPrivateText = NormalizedTextConfig.with_args(
    vocab_size="token_count",
    hidden_size="model_width",
    num_layers="depth",
    num_attention_heads="attention_heads",
    eos_token_id="eos",
)
normalized = NormalizedPrivateText(raw)
assert normalized.hidden_size == 4096
```

For nested configs:

```python
NormalizedNested = NormalizedTextConfig.with_args(
    hidden_size="decoder.hidden_size",
    num_attention_heads="decoder.num_heads",
    num_layers="decoder.num_layers",
    vocab_size="tokenizer.vocab_size",
    eos_token_id="tokenizer.eos_token_id",
)
```

If a downstream helper needs an extra field not present on the normalized class, pass `allow_new=True`:

```python
NormalizedWithExtra = NormalizedTextConfig.with_args(
    allow_new=True,
    hidden_size="width",
    num_attention_heads="heads",
    num_layers="layers",
    vocab_size="vocab",
    eos_token_id="eos",
    rotary_dim="rotary_dim",
)
```

Use `allow_new=True` sparingly: it makes the wrapper accept arbitrary names, so typos become easier to miss.

## Integration with dummy generators

Dummy generators read normalized fields directly:

- Text generators require `vocab_size`; cache generators require `num_layers`, `num_attention_heads`, and `hidden_size`.
- Seq2seq cache generators require encoder/decoder attention-head and layer fields.
- Vision generators prefer `num_channels`, `image_size`, or `input_size` from the normalized config over explicit constructor dimensions.
- Audio and diffusion-style generators may rely on family-specific fields such as `feature_size`, projection dimensions, or nested subconfig values.

Before generating inputs, check the minimum fields:

```python
for field in ["vocab_size", "hidden_size", "num_layers", "num_attention_heads"]:
    if not normalized.has_attribute(field):
        raise ValueError(f"missing normalized field: {field}")
```

## Failure patterns

- `KeyError` from `NormalizedConfigManager`: the model type is not in the built-in map; use `with_args` or route to backend-specific exporter guidance if adding a public mapping.
- `AttributeError` from normalized access: the mapped source field is absent, a dotted path is wrong, or the wrapped config has no useful `attribute_map` fallback.
- Shape mismatch from dummy inputs: the normalized config reported a different image size/channel count than the constructor knobs.
- Cache layout mismatch: a specialized attention cache generator is needed for multi-query/GQA/family-specific layouts.

# Dummy input generators

Optimum dummy input generators create local tensors/arrays for tracing, exporter config probes, shape checks, and small API smokes. They do not download models or datasets; they consume an already available normalized config plus explicit shape knobs.

## Base contract

`DummyInputGenerator` exposes:

- `SUPPORTED_INPUT_NAMES`: input-name prefixes handled by a subclass.
- `supports_input(input_name)`: returns true when `input_name` starts with one of those prefixes.
- `generate(input_name, framework="pt", int_dtype="int64", float_dtype="fp32")`: returns a PyTorch tensor for `framework="pt"` or a NumPy array for `framework="np"`.
- Helpers: `random_int_tensor`, `random_mask_tensor`, `random_float_tensor`, `constant_tensor`, `concat_inputs`, and `pad_input_on_dim`.

Shape defaults live in `DEFAULT_DUMMY_SHAPES`: `batch_size=2`, `sequence_length=16`, `num_choices=4`, image `width=64`, `height=64`, `num_channels=3`, point inputs `point_batch_size=3`, `nb_points_per_image=2`, `visual_seq_length=16`, audio `feature_size=80`, `nb_max_frames=3000`, and `audio_sequence_length=16000`.

Dtype strings are mapped by `DTYPE_MAPPER`. Integer strings include `int64`, `int32`, `int8`, and `bool`. Float strings include `fp32`, `fp16`, and PyTorch-only `bf16`. Do not request `bf16` with `framework="np"`.

## Core subclasses

| Subclass | Supported input names | Key shape/behavior notes |
| --- | --- | --- |
| `DummyTextInputGenerator` | `input_ids`, `attention_mask`, `encoder_attention_mask`, `global_attention_mask`, `token_type_ids`, `position_ids` | Uses `normalized_config.vocab_size`. Regular tasks produce `(batch_size, sequence_length)`; `task="multiple-choice"` produces `(batch_size, num_choices, sequence_length)`. Masks are padded according to `padding_side`. |
| `LongformerDummyTextInputGenerator` | `input_ids`, `attention_mask`, `token_type_ids`, `global_attention_mask` | Specializes Longformer-style global attention by returning an all-zero `global_attention_mask`. |
| `DummyXPathSeqInputGenerator` | `xpath_tags_seq`, `xpath_subs_seq` | Produces `(batch_size, sequence_length, max_depth)` using markup-style normalized config fields. |
| `DummyDecoderTextInputGenerator` | `decoder_input_ids`, `decoder_attention_mask` | Decoder-side version of the text generator. |
| `DummySeq2SeqDecoderTextInputGenerator` | `decoder_input_ids`, `decoder_attention_mask`, `encoder_outputs`, `encoder_hidden_states` | For encoder outputs, returns a tuple whose first element is `(batch_size, sequence_length, hidden_size)`. |
| `DummyPastKeyValuesGenerator` | `past_key_values` | Produces a list with one `(key, value)` tuple per layer. Each tensor has shape `(batch_size, num_attention_heads, sequence_length, hidden_size // num_attention_heads)`. |
| `DummySeq2SeqPastKeyValuesGenerator` | `past_key_values`, `cache_position` | Produces per-decoder-layer tuples `(decoder_key, decoder_value, encoder_key, encoder_value)` and a one-element `cache_position`. Accepts `encoder_sequence_length`. |
| PKV specializations | model-specific `past_key_values` | Use specialized classes such as `GPTBigCodeDummyPastKeyValuesGenerator`, `BloomDummyPastKeyValuesGenerator`, `DeepSeekV3DummyPastKeyValuesGenerator`, `MultiQueryPastKeyValuesGenerator`, `FalconDummyPastKeyValuesGenerator`, `MistralDummyPastKeyValuesGenerator`, `GemmaDummyPastKeyValuesGenerator`, `T5DummySeq2SeqPastKeyValuesGenerator`, or `DummyVisionEncoderDecoderPastKeyValuesGenerator` when the architecture has nonstandard cache layout. |
| `DummyBboxInputGenerator` | `bbox` | Produces `(batch_size, sequence_length, 4)` integer bounding boxes. |
| `DummyVisionInputGenerator` | `pixel_values`, `pixel_mask`, `sample`, `latent_sample`, `visual_embeds`, `visual_token_type_ids`, `visual_attention_mask` | Prefers `normalized_config.num_channels`, `image_size`, or `input_size` over constructor `height`/`width`/`num_channels`. `pixel_values`/`sample`/`latent_sample` use `(batch_size, channels, height, width)`; `pixel_mask` uses `(batch_size, height, width)`; visual embeddings use `(batch_size, visual_seq_length, visual_embedding_dim)`. |
| `DummyAudioInputGenerator` | `input_features`, `input_values` | `input_values` uses `(batch_size, audio_sequence_length)` waveform shape. `input_features` uses `(batch_size, feature_size, nb_max_frames)`. Audio-specific subclasses cover AST/MCTCT/Speech2Text and related layouts. |
| `DummyLabelsGenerator` | `labels`, `start_positions`, `end_positions` | Produces `(batch_size,)` or `(batch_size, sequence_length)` integer labels. Set `num_labels` explicitly for classification labels; leaving it absent can make integer generation invalid. |
| `DummyPointsGenerator` | `input_points`, `input_labels` | Produces point coordinates `(batch_size, point_batch_size, nb_points_per_image, 2)` and labels `(batch_size, point_batch_size, nb_points_per_image)`. |
| `DummyTimestepInputGenerator` and diffusion/transformer variants | `timestep`, `text_embeds`, `time_ids`, `timestep_cond`, `hidden_states`, diffusion text/vision names | Use for Diffusers-style models only after confirming the required normalized config fields exist. Missing projection dimensions raise a clear `ValueError`. |
| `DummyPix2StructInputGenerator`, `DummyVisionEmbeddingsGenerator`, `DummyEncodecInputGenerator`, `DummyPatchTSTInputGenerator`, `DummyIntGenerator` | model-family-specific names | Use only when the exporter config or model signature expects those names. |

## Custom/nonstandard config workflow

When a config has the right semantics but different attribute names, customize the normalized mapping first:

```python
from types import SimpleNamespace
from optimum.utils.normalized_config import NormalizedTextConfig
from optimum.utils.input_generators import DummyTextInputGenerator

raw_config = SimpleNamespace(
    vocab=128,
    width=32,
    layers=2,
    heads=4,
    eos=2,
)
NormalizedTiny = NormalizedTextConfig.with_args(
    vocab_size="vocab",
    hidden_size="width",
    num_layers="layers",
    num_attention_heads="heads",
    eos_token_id="eos",
)
normalized = NormalizedTiny(raw_config)
generator = DummyTextInputGenerator(
    task="text-classification",
    normalized_config=normalized,
    batch_size=1,
    sequence_length=8,
)
inputs = {
    name: generator.generate(name, framework="pt")
    for name in ["input_ids", "attention_mask"]
}
```

Use `allow_new=True` in `with_args` only when a generator or downstream helper needs a normalized attribute that the base normalized class does not define.

## Practical rules

- Choose the subclass by model signature input name, not by task label alone.
- For shape tests, assert both shape and dtype. Shape-only tests can hide NumPy/PyTorch dtype mismatches.
- For vision generators, remember that normalized config image fields override constructor image dimensions.
- For cache generators, verify that `hidden_size` is divisible by the effective number of attention heads.
- For labels, pass `num_labels` for classification and `sequence_length` when token-level labels are expected.
- Use `framework="np"` when PyTorch is unavailable or when validating NumPy-exporter code paths.

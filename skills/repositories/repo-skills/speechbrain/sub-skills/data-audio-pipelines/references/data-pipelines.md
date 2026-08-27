# Data pipelines, datasets, encoders, and tokenizers

## Verified key signatures

```python
speechbrain.dataio.dataset.DynamicItemDataset.from_json(json_path, replacements={}, dynamic_items=[], output_keys=[])
speechbrain.utils.data_pipeline.DataPipeline(static_data_keys, dynamic_items=None, output_keys=None)
DataPipeline.add_dynamic_item(func, takes=None, provides=None)
DataPipeline.set_output_keys(keys)
speechbrain.utils.data_pipeline.takes(*argkeys)
speechbrain.utils.data_pipeline.provides(*output_keys)
speechbrain.tokenizers.SentencePiece.SentencePiece(model_dir, vocab_size, annotation_train=None, annotation_read=None, model_type="unigram", char_format_input=False, ..., text_file=None, ...)
```

## Dynamic item pattern

```python
import speechbrain as sb

train = sb.dataio.dataset.DynamicItemDataset.from_json(
    json_path="train.json",
    replacements={"data_root": "/path/to/audio"},
)

@sb.utils.data_pipeline.takes("wav")
@sb.utils.data_pipeline.provides("sig")
def audio_pipeline(wav):
    return sb.dataio.dataio.read_audio(wav)

@sb.utils.data_pipeline.takes("words")
@sb.utils.data_pipeline.provides("word_list")
def text_pipeline(words):
    return words.split()

sb.dataio.dataset.add_dynamic_item([train], audio_pipeline)
sb.dataio.dataset.add_dynamic_item([train], text_pipeline)
sb.dataio.dataset.set_output_keys([train], ["id", "sig", "word_list"])
```

Dynamic items are lazy. A function may not run if none of its provided keys are requested by `set_output_keys` or `compute_specific`.

## `DataPipeline` direct pattern

```python
from speechbrain.utils.data_pipeline import DataPipeline

pipeline = DataPipeline(["text"])
pipeline.add_dynamic_item(lambda x: x.lower(), takes=["text"], provides="lower")
pipeline.add_dynamic_item(lambda x: x[::-1], takes="lower", provides="reversed")
pipeline.set_output_keys(["reversed"])
assert pipeline({"text": "Speech"})["reversed"] == "hceeps"
```

Use `compute_specific(["key"], data)` to compute selected keys during debugging.

## Encoders

Common encoder families:

- `CategoricalEncoder` for speaker/class labels.
- `TextEncoder` for token sequences with BOS/EOS support.
- `CTCTextEncoder` for CTC labels and blank index handling.
- `SentencePiece` tokenizer wrapper for BPE/unigram tokenization from CSV/JSON/text input.

Recipe pattern:

1. Create encoder.
2. Insert blank/BOS/EOS if needed.
3. Update encoder from train/valid datasets or a manifest field.
4. Add dynamic item that yields both raw list and encoded tensor.
5. Set output keys to include encoded tensors used by the `Brain`.

## Manifests and replacements

`DynamicItemDataset.from_json` can replace placeholder roots:

```python
DynamicItemDataset.from_json(
    "manifest.json",
    replacements={"data_root": "/mnt/dataset"},
)
```

Keep manifests portable by storing relative or placeholder paths rather than absolute machine paths. Put environment-specific roots in overrides.

## Common validation checks

- The static manifest contains every key listed by `@takes`.
- Every key consumed by the `Brain` appears in `set_output_keys`.
- Encoders are fitted before use and have expected vocabulary sizes.
- Length tensors represent relative lengths in `[0, 1]`.
- Multi-output generators `yield` outputs in the same order as `@provides`.

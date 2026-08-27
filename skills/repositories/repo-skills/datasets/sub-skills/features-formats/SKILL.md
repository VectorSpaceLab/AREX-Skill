---
name: features-formats
description: "Define, validate, cast, decode, and troubleshoot Hugging Face
  Datasets feature schemas and supported file formats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Features and Formats

Use this sub-skill when a task is about dataset schemas, feature dtypes, label encodings, nested structures, media/document/3D decoding, local file format support, or errors caused by feature inference and casting.

## Route the Work

- Read `references/schema-and-features.md` to design or repair `Features` objects, choose between `Value`, `ClassLabel`, `List`, `Sequence`, `LargeList`, `Array2D`-`Array5D`, `Translation`, `TranslationVariableLanguages`, `Json`, and use `cast`/`cast_column` safely.
- Read `references/format-loaders.md` to choose a loader or feature for CSV/JSON/Parquet/text/table formats, folder-based media datasets, and optional media decoders such as `Audio`, `Image`, `Video`, `Pdf`, `Nifti`, and `Mesh`.
- Read `references/troubleshooting.md` when schemas fail to cast, labels encode incorrectly, JSON has mixed/null values, media decoding imports fail, folder metadata does not align, or format inference chooses the wrong builder.
- Run `scripts/feature_schema_smoke.py --help` when you need a local, self-contained schema validation helper. Use `--case object-detection` or `--case messages` for examples that catch nested list/object mismatches without requiring media extras.

## Quick Decisions

- Prefer explicit `features=Features(...)` at load time when raw files contain nullable, mixed, nested, or ambiguous values; prefer `dataset.cast(...)` when the table is already loaded and only the declared schema needs changing.
- Use `dataset.cast_column("column", Feature(...))` for one column, especially path/bytes columns that should become `Audio`, `Image`, `Video`, `Pdf`, `Nifti`, or `Mesh`.
- Use `decode=False` for minimal environments, metadata inspection, remote/archive path validation, or workflows that only need path/bytes; enable decoding only after installing the required optional dependency.
- Route data loading mechanics, split patterns, streaming, and Hub/local path questions to `../loading-local-hub/SKILL.md`; route `map`, transforms, formatting for Torch/NumPy/Pandas, and streaming iteration to `../processing-streaming/SKILL.md`; route push-to-Hub, dataset cards, cache cleanup, and CLI publishing to `../sharing-cli-cache/SKILL.md`.

## Safe Minimal Patterns

```python
from datasets import Dataset, Features, Value, ClassLabel, List

features = Features({
    "text": Value("string"),
    "label": ClassLabel(names=["negative", "positive"]),
    "tokens": List(Value("string")),
})
ds = Dataset.from_dict({"text": ["ok"], "label": ["positive"], "tokens": [["o", "k"]]}, features=features)
```

```python
from datasets import Dataset, Audio

ds = Dataset.from_dict({"audio": ["sample.wav"]})
ds = ds.cast_column("audio", Audio(sampling_rate=16_000, decode=False))
```

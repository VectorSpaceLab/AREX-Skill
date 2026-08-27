# VLMEvalKit benchmark data formats

This reference distills the benchmark data contracts from `docs/en/Development.md`, `docs/en/ConfigSystem.md`, and dataset base classes. It is meant for authoring and validation; full evaluation runs route to `../evaluation/SKILL.md`.

## Core TSV contract

VLMEvalKit normally represents image/text benchmarks as one TSV file named `<DatasetName>.tsv`. Official classes download or prepare this file under `LMUData`; unsupported custom datasets are also discovered from `LMUData/<DatasetName>.tsv`.

| Column | Use | Notes |
| --- | --- | --- |
| `index` | Stable sample id | Required. Should be unique. Base classes normalize integer-like ids. Circular MCQ variants may use grouped ids such as `g_index`. |
| `question` | Prompt text or prompt template | Required for custom fallback. Long-context/image-token datasets often embed `<image token>` / `<image>` markers in this text. |
| `image` | Base64 image payload | Use for embedded images. May be a string or a JSON-like list for multi-image rows. Some datasets use short references to another row's image to save space. |
| `image_path` | Image file reference(s) | Use when images are stored separately. Single image can be a string; multi-image rows should store a JSON-encoded list such as `["doc/page1.png", "doc/page2.png"]`. |
| `A`, `B`, ... | Multiple-choice options | Include uppercase option columns for MCQ datasets. `ImageMCQDataset` and MCQ helpers scan uppercase letters. |
| `answer` | Ground-truth answer | Required for local metrics. Test-only splits may omit it; evaluators must handle official-submission or no-answer cases explicitly. |
| `hint` | Optional prompt hint | `ImageMCQDataset.build_prompt` prepends it when present and non-null. |
| `category`, `l2-category`, `split` | Grouped reporting | `report_acc` groups by `split`, then optionally by `l2-category` and `category`. |
| `question_id`, task-specific metadata | Converter/evaluator joins | Keep source ids, task names, evidence pages, document ids, and raw metadata when evaluators or regeneration need them. JSON-encode structured values. |

Minimum custom image MCQ TSV:

```tsv
index	question	image_path	A	B	answer	category	split
0	What color is the object?	examples/0.png	red	blue	A	color	dev
```

Minimum custom text MCQ TSV:

```tsv
index	question	A	B	answer
0	Which option is correct?	option one	option two	B
```

Minimum custom VQA TSV:

```tsv
index	question	image_path	answer
0	Describe the figure.	examples/figure.png	A line chart.
```

## Image storage rules

- If the row has `image`, `ImageBaseDataset.dump_image` decodes it under `LMUData/images/<dataset-root>/` and returns local paths.
- If the row has no `image`, it must have `image_path`. Paths may be absolute, but portable TSVs should prefer relative paths under the dataset image root.
- Relative `image_path` values are resolved under `LMUData/images/<dataset-root>/`, where `<dataset-root>` is usually the dataset name after `img_root_map(dataset)`.
- Multi-image rows should JSON-encode `image_path` lists. Base helpers use `toliststr`, so JSON strings are preferred over Python repr strings.
- If both `image` and `image_path` exist, `image_path` controls output file names for decoded embedded images.

## Multimodal message format

`build_prompt(line)` returns an interleaved list of dictionaries. Valid authoring targets are:

```python
[
    dict(type='image', value='relative/or/local/image.png'),
    dict(type='text', value='Question text or instruction'),
]
```

Video-aware paths may also return:

```python
[
    dict(type='video', value='relative/or/local/video.mp4'),
    dict(type='text', value='Question text'),
]
```

For long-context document/image benchmarks, split text around `<image token>` / `<image>` markers and insert `dict(type='image', value=...)` in the same order as `image_path`.

## Video metadata contract

`VideoBaseDataset` requires a subclass to implement `prepare_dataset(dataset)`, `build_prompt(idx)`, and `evaluate(eval_file, **judge_kwargs)`. `prepare_dataset` returns:

```python
{
    'root': '<directory-containing-video-files>',
    'data_file': '<metadata.tsv>',
}
```

The loaded metadata must include:

| Column | Use |
| --- | --- |
| `index` | Optional; if absent it is generated from row order. |
| `question` | Required prompt/question. |
| `video` | Required video id or relative video path. Many classes expect `<root>/<video>.mp4`, but subclass code can override this. |
| `answer`, `A`/`B`/... | Required when local evaluation needs MCQ or VQA ground truth. |
| `subtitle`, `audio`, task metadata | Optional; only include if the dataset class consumes it. |

Frame extraction presets must set exactly one of `nframe` or `fps`. If both are positive, `VideoBaseDataset` raises `ValueError`; if neither is positive, it passes the video file directly and disables frame splitting.

## One-off dataset configuration

For custom data without editing package registries, create a config JSON with a `data` entry. Use official or reusable class names from `vlmeval/dataset/__init__.py`.

```json
{
  "data": {
    "MyBench": {
      "class": "ImageMCQDataset",
      "dataset": "MyBench"
    },
    "MyVideoBench_8frame": {
      "class": "MyVideoDataset",
      "dataset": "MyVideoBench",
      "nframe": 8,
      "pack": false
    }
  }
}
```

For a one-off TSV in `LMUData`, `build_dataset('MyBench')` falls back as follows:

1. Missing `LMUData/MyBench.tsv` -> returns `None` with a warning.
2. Missing `question` column -> returns `None` with a warning.
3. Has `A` and `B` plus `image` or `image_path` -> `CustomMCQDataset`.
4. Has `A` and `B` without image columns -> `CustomTextMCQDataset`.
5. Otherwise -> `CustomVQADataset`.

## Cache and data environment variables

| Variable | Meaning |
| --- | --- |
| `LMUData` | Root for TSVs, downloaded metadata, and `images/` cache. Defaults to the user's home `LMUData` when unset. |
| `FORCE_LOCAL` | Forces regeneration of localized TSVs for files larger than 1 GB. |
| `LONGDOCURL_TSV_ROOT` | Directory containing or receiving `LongDocURL.tsv`. |
| `LONGDOCURL_IMAGE_ROOT` | Directory containing LongDocURL `pdf_pngs` images. |
| `LONGDOCURL_JSONL` | Optional local LongDocURL source JSONL used by the dataset class. |
| `MMLB_TSV_ROOT` | Directory containing `MMLongBench_*.tsv`. |
| `MMLB_IMAGE_ROOT` | Optional image root for MMLongBench image files. |
| `MEMLENS_TSV_ROOT` | Directory containing `MemLens_*.tsv`. |
| `MEMLENS_IMAGE_ROOT` | Optional image root for MemLens images. |
| `VLMEVALKIT_USE_MODELSCOPE` | When set to `1` or `True`, selected dataset download helpers use ModelScope paths instead of Hugging Face/OpenCompass paths. |

## Local validation probes

Use these checks before any model inference:

```bash
python - <<'PY'
import pandas as pd
p = 'MyBench.tsv'
df = pd.read_csv(p, sep='\t')
print(df.columns.tolist())
assert 'index' in df and 'question' in df
assert df['index'].is_unique
print(df.head(1).to_dict('records')[0])
PY
```

```bash
python - <<'PY'
from vlmeval.dataset import DATASET_MODALITY, DATASET_TYPE, build_dataset
name = 'MyBench'
ds = build_dataset(name)
print(type(ds).__name__ if ds is not None else None)
print(DATASET_TYPE(name), DATASET_MODALITY(name))
if ds is not None:
    print(len(ds), ds.build_prompt(0))
PY
```

Do not treat these probes as a full evaluation. They only prove schema loading and prompt construction.

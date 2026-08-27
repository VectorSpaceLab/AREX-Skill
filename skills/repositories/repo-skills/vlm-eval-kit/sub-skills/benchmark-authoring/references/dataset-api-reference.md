# Dataset API reference for benchmark authoring

This reference covers the VLMEvalKit dataset APIs used when adding image, text, video, custom TSV, and MCQ benchmark support.

## Which base class to use

| Need | Preferred base | Why |
| --- | --- | --- |
| Image VQA/open-ended benchmark | `ImageBaseDataset` or an existing VQA subclass | Handles TSV download/cache, base64 decoding, `image_path` resolution, and default image+text prompt. |
| Image multiple-choice benchmark | `ImageMCQDataset` | Adds option prompt construction and MCQ evaluation flow with exact matching or optional LLM judge. |
| Text-only benchmark | `TextBaseDataset` or `TextMCQDataset` | Avoids image handling and returns text-only multimodal messages. |
| Video benchmark | `VideoBaseDataset` or an existing video subclass | Handles video metadata loading, frame extraction controls, `pack`, `nframe`, and `fps`. |
| Local one-off TSV | `CustomMCQDataset`, `CustomTextMCQDataset`, or `CustomVQADataset` through `build_dataset` fallback | Lets users validate data without package registry edits. |
| Aggregate of registered datasets | `ConcatDataset` / `ConcatVideoDataset` | Combines supported datasets while preserving underlying prompts and per-dataset evaluation. |

## Base-class contracts

### `ImageBaseDataset`

Key class attributes:

- `MODALITY = 'IMAGE'`
- `TYPE`: set in subclasses when the task kind matters, commonly `'MCQ'`, `'VQA'`, or `'Y/N'`.
- `DATASET_URL`: `{dataset_name: url_or_filename}` for supported dataset names.
- `DATASET_MD5`: optional `{dataset_name: md5}`.
- `DEFAULT_JUDGE`: default evaluator model name for judge-based metrics.

Key methods:

- `supported_datasets(cls)`: returns `list(cls.DATASET_URL)` unless overridden.
- `load_data(self, dataset)`: returns a `pandas.DataFrame` for the TSV. Default calls `prepare_tsv`.
- `prepare_tsv(self, url, file_md5=None)`: resolves/downloads `<dataset>.tsv` under `LMUData` and localizes very large TSVs when needed.
- `dump_image(self, line)`: decodes `image` payloads or resolves `image_path` entries; returns one or more image paths.
- `build_prompt(self, line)`: default returns image messages followed by `dict(type='text', value=question)`.
- `evaluate(self, eval_file, **judge_kwargs)`: abstract; return a `dict` or `pandas.DataFrame` and dump any detailed intermediates.

Minimal image VQA subclass:

```python
from vlmeval.dataset.image_base import ImageBaseDataset
from vlmeval.smp import load

class MyImageVQADataset(ImageBaseDataset):
    TYPE = 'VQA'
    DATASET_URL = {'MyImageVQA': ''}  # empty means MyImageVQA.tsv under LMUData
    DATASET_MD5 = {}

    def evaluate(self, eval_file, **judge_kwargs):
        data = load(eval_file)
        # Compute metrics from data['prediction'] and data['answer'].
        return {'overall': 0.0}
```

### `TextBaseDataset`

`TextBaseDataset` mirrors the TSV/cache flow but `dump_image` returns `[]` and default `build_prompt` returns only:

```python
[dict(type='text', value=line['question'])]
```

Use it for text-only MCQ/VQA tasks where image fallback would be misleading.

### `VideoBaseDataset`

Constructor arguments:

- `dataset`: canonical dataset name.
- `pack`: when true, `__getitem__` returns all rows for one video; when false, it returns one row.
- `nframe`: fixed number of frames to sample. Mutually exclusive with `fps`.
- `fps`: sampling rate. Mutually exclusive with `nframe`.

Required methods:

```python
def prepare_dataset(self, dataset):
    return {'root': '<video-root>', 'data_file': '<metadata.tsv>'}

def build_prompt(self, idx):
    ...

def evaluate(self, eval_file, **judge_kwargs):
    ...
```

`VideoBaseDataset` checks that metadata has `question` and `video`; it creates frame caches under `LMUData/images/<dataset>/` when frame splitting is enabled. If both `fps > 0` and `nframe > 0`, it raises `ValueError('fps and nframe should not be set at the same time')`.

## Prompt construction patterns

Default image prompt:

```python
msgs = [dict(type='image', value=path) for path in image_paths]
msgs.append(dict(type='text', value=question))
return msgs
```

Default MCQ prompt, as used by `ImageMCQDataset`, builds:

```text
Hint: <hint if present>
Question: <question>
Options:
A. <A>
B. <B>
...
Please select the correct answer from the options above.
```

Interleaved long-context prompt:

```python
import re
from vlmeval.smp import toliststr

parts = re.split(r'(<image token>|<image>)', str(line['question']))
images = toliststr(line['image_path'])
msgs, image_idx = [], 0
for part in parts:
    if part in {'<image token>', '<image>'}:
        msgs.append(dict(type='image', value=images[image_idx]))
        image_idx += 1
    elif part:
        msgs.append(dict(type='text', value=part))
assert image_idx == len(images)
return msgs
```

Video direct-input prompt:

```python
video_path = self.resolve_video(line['video'])
return [
    dict(type='video', value=video_path),
    dict(type='text', value=line['question']),
]
```

Use model-side custom prompt hooks only when adapting a model wrapper; that belongs in `../model-development/SKILL.md`.

## Registry and dataset construction

`vlmeval/dataset/__init__.py` builds these registry lists:

- `IMAGE_DATASET`
- `VIDEO_DATASET`
- `TEXT_DATASET`
- `CUSTOM_DATASET`
- `DATASET_COLLECTION`
- `DATASET_CLASSES = IMAGE_DATASET + VIDEO_DATASET + TEXT_DATASET + CUSTOM_DATASET + DATASET_COLLECTION`
- `SUPPORTED_DATASETS` from each class's `supported_datasets()`

`build_dataset(dataset_name, **kwargs)` logic:

1. If `dataset_name` is in `supported_video_datasets`, instantiate that video preset.
2. Else find a class whose `supported_datasets()` contains the name and instantiate `cls(dataset=dataset_name, **kwargs)`.
3. Else load `LMUData/<dataset_name>.tsv` and infer a custom class.

When adding a reusable in-package dataset class, import it in `vlmeval/dataset/__init__.py` and add it to the appropriate registry list. When adding a reusable video preset, add a `functools.partial` in `vlmeval/dataset/video_dataset_config.py` and update `supported_video_datasets` through its dataset group list.

## `DATASET_TYPE` and `DATASET_MODALITY`

- `DATASET_TYPE(name)` returns a registered class `TYPE` when available.
- Unknown names containing `openended` become `'VQA'`; otherwise unknown names default to `'MCQ'` with a warning.
- `DATASET_MODALITY(name)` returns a registered class `MODALITY` when available.
- Unknown names containing `VIDEO` become `'VIDEO'`, containing `IMAGE` become `'IMAGE'`, otherwise default to `'IMAGE'` with a warning.

Name custom datasets clearly if relying on fallback. For example, `MyVideoBench` helps modality inference; `MyOpenEndedImageBench` helps type inference.

## Concat datasets

`ConcatDataset.DATASET_SETS` maps a combined name to supported image dataset names. It:

- Instantiates each member through `build_dataset`.
- Requires all member `TYPE` and `MODALITY` values to match.
- Adds `SUB_DATASET` and `original_index` columns.
- Delegates `build_prompt` and `evaluate` back to each member dataset.

Do not use `ConcatDataset` to combine incompatible modalities or task types.

## Evaluation helper flow

### Judge construction

`build_judge(**judge_kwargs)` creates a judge model wrapper. Important kwargs and env behavior:

- `model`: judge model alias or backend model string.
- `nproc`: stripped before constructing the judge.
- `LOCAL_LLM`: when set, overrides the selected judge model version.
- Provider/API setup is environment-dependent; do not claim live judge success from import-only checks.

### Exact matching vs LLM judge

`ImageMCQDataset.evaluate_heuristic` uses:

- `model='exact_matching'`: `model = None`; only deterministic answer extraction is used.
- Any other `model`: calls `build_judge`; if `.working()` is false, it warns and falls back to exact matching.

For new MCQ datasets, default to exact matching unless the benchmark specification requires semantic matching.

### MCQ helpers

`vlmeval/dataset/utils/multiple_choice.py` provides:

- `build_choices(item)`: collect uppercase option columns.
- `prefetch_answer(item)`: deterministic option extraction from `prediction`.
- `extract_answer_from_item(model, item, dataset_name=None)`: deterministic extraction first; optional judge prompt if needed; returns `{opt, log}`.
- `mcq_vanilla_eval(model, data, meta, nproc, result_file, dataset_name=None)`: row-wise MCQ evaluation.
- `mcq_circular_eval(model, data, meta, nproc, result_file, dataset_name=None)`: grouped/circular MCQ evaluation.
- `report_acc(df)`: overall and optional `split`, `l2-category`, `category` accuracy table.

Minimal MCQ evaluator shape:

```python
from vlmeval.dataset.utils import build_judge
from vlmeval.dataset.utils.multiple_choice import mcq_vanilla_eval, report_acc
from vlmeval.smp import dump, get_intermediate_file_path, load

class MyMCQ(ImageMCQDataset):
    DATASET_URL = {'MyMCQ': ''}
    DATASET_MD5 = {}

    def evaluate(self, eval_file, **judge_kwargs):
        nproc = judge_kwargs.pop('nproc', 4)
        model_name = judge_kwargs.get('model', 'exact_matching')
        model = None if model_name == 'exact_matching' else build_judge(**judge_kwargs)
        result_file = get_intermediate_file_path(eval_file, f'_{model_name}_result', 'pkl')
        data = load(eval_file).sort_values(by='index')
        data['prediction'] = [str(x) for x in data['prediction']]
        scored = mcq_vanilla_eval(model, data, self.data, nproc, result_file, self.dataset_name)
        acc = report_acc(scored)
        dump(acc, get_intermediate_file_path(eval_file, '_acc', 'csv'))
        return acc
```

## Video preset patterns

`vlmeval/dataset/video_dataset_config.py` uses `functools.partial`:

```python
from functools import partial

my_video_dataset = {
    'MyVideoBench_8frame_nopack': partial(MyVideoBench, dataset='MyVideoBench', nframe=8, pack=False),
    'MyVideoBench_1fps_pack': partial(MyVideoBench, dataset='MyVideoBench', fps=1.0, pack=True),
}
```

Common preset dimensions:

- `nframe`: fixed frames such as 8, 16, 32, 64, 128, or dataset-specific counts.
- `fps`: sampling rates such as 0.5, 1.0, or 2.0.
- `pack`: per-video grouping for models/evaluators that consume all rows for one video together.
- Subtitle flags: `use_subtitle`, `with_subtitle`, `subtitle_interleave`, or dataset-specific names.
- Audio flags: `use_audio`, `audio_only`, or dataset-specific names.

Always instantiate a tiny local metadata fixture or import-level preset check before launching a large video job.

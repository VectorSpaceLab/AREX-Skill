# Dataset Customization

OpenCompass supports built-in dataset configs and local/custom datasets. For agent-authored configs, prefer built-in configs when possible; use `CustomDataset` for local JSONL/CSV data and a dedicated dataset class only when loading, postprocessing, or evaluation behavior cannot be expressed with existing components.

## Local JSONL/CSV with CustomDataset

`CustomDataset` loads `.jsonl` and `.csv` files and returns a Hugging Face `Dataset`. It accepts:

- `path`: file path or directory path after OpenCompass data-path resolution.
- `file_name`: optional file name appended to `path`.
- `local_mode`: optional flag passed to data-path resolution.

JSONL example:

```json
{"problem": "What is the capital of France?", "answer": "Paris"}
{"problem": "2 + 2 = ?", "answer": "4"}
```

CSV example:

```csv
problem,answer
"What is the capital of France?","Paris"
"2 + 2 = ?","4"
```

Config example:

```python
from opencompass.datasets import CustomDataset
from opencompass.openicl.icl_prompt_template import PromptTemplate
from opencompass.openicl.icl_retriever import ZeroRetriever
from opencompass.openicl.icl_inferencer import GenInferencer
from opencompass.openicl.icl_evaluator import AccEvaluator

reader_cfg = dict(input_columns=['problem'], output_column='answer')

infer_cfg = dict(
    prompt_template=dict(
        type=PromptTemplate,
        template=dict(round=[dict(role='HUMAN', prompt='{problem}')]),
    ),
    retriever=dict(type=ZeroRetriever),
    inferencer=dict(type=GenInferencer),
)

eval_cfg = dict(evaluator=dict(type=AccEvaluator), pred_role='BOT')

datasets = [
    dict(
        type=CustomDataset,
        abbr='local-qa-smoke',
        path='data/local_qa.jsonl',
        reader_cfg=reader_cfg,
        infer_cfg=infer_cfg,
        eval_cfg=eval_cfg,
    )
]
```

Column rules:

- Every `reader_cfg.input_columns` entry should be present in each JSONL object or CSV header.
- `reader_cfg.output_column` should be present when the evaluator needs references.
- Prompt placeholders such as `{problem}` should match input columns or fields available to the prompt template.
- Use `file_name` when `path` is a directory: `path='data/local_qa', file_name='dev.jsonl'`.

## Local JSONL QA with GenericLLMEvaluator

Use LLM-as-judge only when rule-based metrics are not sufficient. The evaluator needs a judge model config. Keep the dataset config focused on data wiring and route detailed model-backend choices to `model-backends`.

```python
from mmengine.config import read_base
from opencompass.datasets import CustomDataset, generic_llmjudge_postprocess
from opencompass.evaluator import GenericLLMEvaluator
from opencompass.openicl.icl_prompt_template import PromptTemplate
from opencompass.openicl.icl_retriever import ZeroRetriever
from opencompass.openicl.icl_inferencer import GenInferencer

with read_base():
    from opencompass.configs.models.qwen2_5.lmdeploy_qwen2_5_14b_instruct import models as judge_models

JUDGE_TEMPLATE = """
Question: {problem}
Reference answer: {answer}
Model response: {prediction}
Return A if the response is correct, otherwise return B.
""".strip()

reader_cfg = dict(input_columns=['problem'], output_column='answer')

infer_cfg = dict(
    prompt_template=dict(
        type=PromptTemplate,
        template=dict(round=[dict(role='HUMAN', prompt='{problem}')]),
    ),
    retriever=dict(type=ZeroRetriever),
    inferencer=dict(type=GenInferencer),
)

eval_cfg = dict(
    evaluator=dict(
        type=GenericLLMEvaluator,
        prompt_template=dict(
            type=PromptTemplate,
            template=dict(round=[dict(role='HUMAN', prompt=JUDGE_TEMPLATE)]),
        ),
        dataset_cfg=dict(
            type=CustomDataset,
            path='data/local_qa.jsonl',
            reader_cfg=reader_cfg,
        ),
        judge_cfg=judge_models[0],
        dict_postprocessor=dict(type=generic_llmjudge_postprocess),
    ),
    pred_role='BOT',
)

datasets = [
    dict(
        type=CustomDataset,
        abbr='local-qa-judge',
        path='data/local_qa.jsonl',
        reader_cfg=reader_cfg,
        infer_cfg=infer_cfg,
        eval_cfg=eval_cfg,
    )
]
```

Validation command before a real run:

```bash
python -m py_compile local_qa_eval.py
opencompass local_qa_eval.py --dry-run --debug
```

If the judge model config imports optional backends, dry-run may still require those optional packages.

## Auto-Building Custom Dataset Configs

OpenCompass includes helper logic that can infer a custom dataset config from a sample local file. The inferred metadata uses these conventions:

- If the file has an `answer` column, that becomes `output_column`; otherwise `output_column` is `None`.
- All non-`answer` fields become `input_columns` by default.
- Consecutive uppercase columns `A`, `B`, `C`, ... are treated as multiple-choice options.
- The file stem becomes `abbr` unless overridden.
- Default data type is `mcq` when options exist, otherwise `qa`; default inference method is `gen`.
- A sidecar `<file>.meta.json` can override inferred metadata.

This is useful for quick local experiments, but explicit configs are clearer for reusable evaluations.

## Dedicated Dataset Class

Create a dataset class when local JSONL/CSV is not enough. The class should subclass `BaseDataset` and implement a static `load` method returning `datasets.Dataset` or `datasets.DatasetDict`.

```python
import datasets
from opencompass.datasets.base import BaseDataset
from opencompass.registry import LOAD_DATASET

@LOAD_DATASET.register_module()
class MyDataset(BaseDataset):
    @staticmethod
    def load(path, name=None, **kwargs):
        rows = [{'question': '...', 'answer': '...'}]
        return datasets.Dataset.from_list(rows)
```

A config then imports the dataset class and uses the same `reader_cfg`, `infer_cfg`, and `eval_cfg` pattern:

```python
from opencompass.datasets import MyDataset

datasets = [
    dict(
        type=MyDataset,
        abbr='my-dataset',
        path='opencompass/my-dataset',
        reader_cfg=reader_cfg,
        infer_cfg=infer_cfg,
        eval_cfg=eval_cfg,
    )
]
```

## Dataset Source Mapping

For reusable built-in-style datasets, map logical dataset names to source locations in `DATASETS_MAPPING`. A mapping entry can include:

```python
DATASETS_MAPPING['opencompass/my-dataset'] = {
    'ms_id': 'opencompass/my-dataset',
    'hf_id': 'opencompass/my-dataset',
    'local': './data/my-dataset',
}
```

Guidance:

- The dataset config `path` should match the mapping key, for example `path='opencompass/my-dataset'`.
- `hf_id` is the Hugging Face dataset id.
- `ms_id` is the ModelScope dataset id.
- `local` is the fallback local data location used by OpenCompass data-path resolution.
- Dataset loaders that support multiple sources commonly branch on `os.environ['DATASET_SOURCE'] == 'ModelScope'`; otherwise they use OSS/HF/local behavior depending on the loader.
- For a public reusable dataset, also add dataset-index metadata in the source repository. For local private evaluations, a standalone `CustomDataset` config is usually enough.

## Multiple Evaluation Repeats

`BaseDataset` supports repeated evaluation through `n` and G-Pass@k through `k`:

```python
datasets = [
    dict(
        type=CustomDataset,
        abbr='local-qa-repeat',
        path='data/local_qa.jsonl',
        n=12,
        k=[2, 4],
        reader_cfg=reader_cfg,
        infer_cfg=infer_cfg,
        eval_cfg=eval_cfg,
    )
]
```

`max(k)` must be less than or equal to `n`.

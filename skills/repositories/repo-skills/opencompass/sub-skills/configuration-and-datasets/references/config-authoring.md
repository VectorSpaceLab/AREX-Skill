# Config Authoring

OpenCompass configs are Python files parsed by MMEngine. A runnable evaluation config normally defines top-level `datasets` and `models`; it may also define `summarizer`, runner/partitioner settings, or other advanced variables consumed by the CLI.

## Required Shape

```python
from mmengine.config import read_base

with read_base():
    from opencompass.configs.datasets.gsm8k.gsm8k_gen import gsm8k_datasets
    from opencompass.configs.models.hf_internlm.hf_internlm2_chat_7b import models as internlm2_models

datasets = [*gsm8k_datasets]
models = [*internlm2_models]
```

Important rules:

- Use `with read_base():` around imports from config modules. This is the supported inheritance style for OpenCompass/MMEngine Python configs.
- Imported dataset variables are usually named like `<dataset>_datasets` and contain a list of dataset dicts.
- Imported model configs usually expose `models`; alias them when combining multiple model files to avoid overwriting.
- Keep `datasets` and `models` as lists. Use list unpacking or `+=` to combine imports.
- If a config imports classes directly, imports must resolve in the runtime environment before `Config.fromfile` or `opencompass --dry-run` can load it.

## Combine Multiple Datasets and Models

```python
from mmengine.config import read_base

with read_base():
    from opencompass.configs.datasets.mmlu.mmlu_gen import mmlu_datasets
    from opencompass.configs.datasets.gsm8k.gsm8k_gen import gsm8k_datasets
    from opencompass.configs.models.hf_internlm.hf_internlm2_chat_7b import models as internlm2_chat_7b
    from opencompass.configs.models.hf_internlm.hf_internlm2_7b import models as internlm2_base_7b

datasets = []
datasets += mmlu_datasets
datasets += gsm8k_datasets

models = []
models += internlm2_chat_7b
models += internlm2_base_7b
```

Validate before an expensive run:

```bash
python -m py_compile my_eval.py
opencompass my_eval.py --dry-run --debug
```

`py_compile` catches Python syntax only. `opencompass --dry-run` exercises OpenCompass config parsing and task construction, but it does not verify real model inference.

## Dataset Config Anatomy

A dataset entry typically has this structure:

```python
from opencompass.datasets import HFDataset
from opencompass.openicl.icl_prompt_template import PromptTemplate
from opencompass.openicl.icl_retriever import ZeroRetriever
from opencompass.openicl.icl_inferencer import GenInferencer, PPLInferencer
from opencompass.openicl.icl_evaluator import AccEvaluator

reader_cfg = dict(
    input_columns=['question'],
    output_column='answer',
    test_split='validation',
)

infer_cfg = dict(
    prompt_template=dict(
        type=PromptTemplate,
        template=dict(round=[dict(role='HUMAN', prompt='{question}')]),
    ),
    retriever=dict(type=ZeroRetriever),
    inferencer=dict(type=GenInferencer),
)

eval_cfg = dict(evaluator=dict(type=AccEvaluator), pred_role='BOT')

datasets = [
    dict(
        abbr='my-qa-dev',
        type=HFDataset,
        path='my-org/my-dataset',
        reader_cfg=reader_cfg,
        infer_cfg=infer_cfg,
        eval_cfg=eval_cfg,
    )
]
```

Key fields:

- `abbr`: result-table and output identifier. Set it explicitly when comparing configs or summarizer output matters.
- `type`: dataset class or registry target, such as `HFDataset` or `CustomDataset`.
- `path`, `name`, `data_files`, `split`, `file_name`: loader-specific dataset location arguments.
- `reader_cfg.input_columns`: columns passed into prompt templates.
- `reader_cfg.output_column`: reference-answer column used by evaluators. Use `None` only for datasets without references.
- `infer_cfg.prompt_template`: prompt construction config.
- `infer_cfg.retriever`: in-context example retrieval; `ZeroRetriever` means no examples.
- `infer_cfg.inferencer`: `GenInferencer` for generation or `PPLInferencer` for perplexity/choice scoring.
- `eval_cfg.evaluator`: metric/evaluator config.
- `eval_cfg.pred_role`: often `BOT` for generation-style outputs.

## Generation vs PPL Dataset Configs

Use generation (`*_gen.py`, `GenInferencer`) when the model should produce free text or an answer string:

```python
infer_cfg = dict(
    prompt_template=dict(type=PromptTemplate, template=dict(round=[
        dict(role='HUMAN', prompt='Question: {question}\nAnswer:'),
    ])),
    retriever=dict(type=ZeroRetriever),
    inferencer=dict(type=GenInferencer),
)
```

Use perplexity (`*_ppl.py`, `PPLInferencer`) for multiple-choice scoring where every candidate answer has a prompt alternative:

```python
infer_cfg = dict(
    prompt_template=dict(
        type=PromptTemplate,
        template={
            'A': 'Question: {question}\nA. {A}\nB. {B}\nAnswer: A',
            'B': 'Question: {question}\nA. {A}\nB. {B}\nAnswer: B',
        },
    ),
    retriever=dict(type=ZeroRetriever),
    inferencer=dict(type=PPLInferencer),
)
```

Choose the config file suffix (`gen`, `ppl`, `llmjudge`, `cascade`, etc.) based on evaluation mechanics, not just dataset name.

## Summarizer Dataset Abbreviations

Summarizers commonly use dataset abbreviations derived from dataset configs. If a config comparison shows `abbr` changes, result tables and reuse paths may change even when dataset content is similar. When a summarizer filters datasets, confirm its `dataset_abbrs` matches the final dataset entries.

```python
summarizer = dict(
    type='DefaultSummarizer',
    dataset_abbrs=['mmlu', 'gsm8k'],
)
```

Keep summarizer details minimal in config authoring; route detailed result summarization and launch behavior to `evaluation-workflows`.

## Validation Checklist

1. `python -m py_compile my_eval.py` succeeds.
2. `opencompass my_eval.py --dry-run --debug` loads imports and expands tasks.
3. `scripts/compare_config_keys.py baseline.py my_eval.py --show datasets,models` shows expected dataset/model abbreviations.
4. Every prompt placeholder, such as `{question}`, exists in `reader_cfg.input_columns` or the dataset rows.
5. Every evaluator reference field exists as `reader_cfg.output_column` unless intentionally reference-free.

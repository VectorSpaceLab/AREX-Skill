# UniMC, UniEX, and Ubert Programmatic Pipelines

These surfaces are public Fengshen pipeline-style APIs, but they are not reliable `fengshen-pipeline` console routes. Use them from Python with their own parser helper methods.

## Route summary

| Surface | Import | Parser helper | Initialization | Run methods |
|---|---|---|---|---|
| UniMC | `from fengshen.pipelines.multiplechoice import UniMCPipelines` | `UniMCPipelines.pipelines_args(parser)` | `UniMCPipelines(args, model_path=...)` | `train(train_data, dev_data)`, `predict(test_data, cuda=True, process=True)` |
| UniEX | `from fengshen.pipelines.information_extraction import UniEXPipelines` | `UniEXPipelines.pipelines_args(parser)` | `UniEXPipelines(args)` with `args.pretrained_model_path` set | `fit(train_data, dev_data, test_data=[])`, `predict(test_data, cuda=True)` |
| Ubert | `from fengshen import UbertPipelines` | `UbertPipelines.pipelines_args(parser)` | `UbertPipelines(args)` with `args.pretrained_model_path` set | `fit(train_data, dev_data)`, `predict(predict_data, cuda=True)` |

All three may download a pretrained model/tokenizer during initialization unless `pretrained_model_path` or `model_path` points to a local/cached model directory.

## UniMC: unified multiple choice

Minimal parser and model setup:

```python
import argparse
from fengshen.pipelines.multiplechoice import UniMCPipelines

parser = argparse.ArgumentParser('UniMC')
parser = UniMCPipelines.pipelines_args(parser)
args = parser.parse_args([])
args.language = 'chinese'          # or 'english'
args.learning_rate = 2e-5
args.max_length = 512
args.max_epochs = 3
args.batchsize = 8
args.default_root_dir = './'
model = UniMCPipelines(args, model_path='MODEL_OR_LOCAL_DIR')
```

Expected item schema:

```json
{
  "texta": "it 's just incredibly dull .",
  "textb": "",
  "question": "What is sentiment of follow review?",
  "choice": ["it's great", "it's terrible"],
  "answer": "",
  "label": 0,
  "id": 19
}
```

Special `task_type` values trigger built-in choice rewriting:

- `语义匹配`: creates two choices roughly meaning “cannot be understood as ...” and “can be understood as ...”.
- `自然语言推理`: creates contradiction/neutral/entailment-style choices.

Use UniMC when the task can be expressed as choosing among textual options. Do not send UniMC data through `fengshen-pipeline multiplechoice ...`; the class does not expose the console-required method names.

## UniEX: unified information extraction

Setup shape:

```python
import argparse
from fengshen.pipelines.information_extraction import UniEXPipelines

parser = argparse.ArgumentParser('UniEX')
parser = UniEXPipelines.pipelines_args(parser)
args = parser.parse_args([])
args.pretrained_model_path = 'MODEL_OR_LOCAL_DIR'
args.threshold_index = 0.5
args.threshold_entity = 0.5
args.threshold_event = 0.5
args.threshold_relation = 0.5
model = UniEXPipelines(args)
```

Supported task families include entity recognition, relation extraction, event extraction, coreference, and extractive MRC.

Minimal entity-recognition item:

```json
{
  "task_type": "实体识别",
  "text": "彭小军认为，国内银行现在走的是台湾的发卡模式。",
  "entity_list": [],
  "choice": ["姓名", "地址", "组织机构", "公司"],
  "id": 0
}
```

Relation and coreference items use `spo_list`; event items use `event_list`; extractive MRC uses a question-like entry in `choice`. Keep `choice` singular for UniEX. Do not confuse it with Ubert's `choices` list.

## Ubert: unified NLU route

Ubert is exported from the package top level:

```python
import argparse
from fengshen import UbertPipelines

parser = argparse.ArgumentParser('Ubert')
parser = UbertPipelines.pipelines_args(parser)
args = parser.parse_args([])
args.pretrained_model_path = 'MODEL_OR_LOCAL_DIR'
args.batchsize = 8
args.max_length = 128
model = UbertPipelines(args)
```

Ubert item schema uses `choices` plural:

```json
{
  "task_type": "抽取任务",
  "subtask_type": "实体识别",
  "text": "这也让很多业主据此认为，雅清苑是政府公务员挤对了国家的经适房政策。",
  "choices": [
    {"entity_type": "小区名字"},
    {"entity_type": "岗位职责"}
  ],
  "id": 0
}
```

For classification, each choice can carry a `label` field where `1` marks the correct label in training data:

```json
{
  "task_type": "分类任务",
  "subtask_type": "文本分类",
  "text": "7000亿美元救市方案将成期市毒药",
  "choices": [
    {"entity_type": "一则股票新闻", "label": 1, "entity_list": []},
    {"entity_type": "一则教育新闻", "label": 0, "entity_list": []}
  ],
  "id": 0
}
```

## Shared argument families

- `--pretrained_model_path` / `model_path`: model id or local model directory.
- `--load_checkpoints_path`: optional fine-tuned checkpoint.
- `--train`: boolean flag used by examples to decide whether to call training.
- `--batchsize`, `--max_length`, `--learning_rate`, `--max_epochs`: data/training sizes and optimizer defaults.
- Checkpoint and Trainer flags are added by Fengshen helpers and PyTorch Lightning; route detailed resource or distributed-training interpretation to `data-training`.

## Misuse checklist

- Unknown console route: these classes are programmatic; do not force them through `fengshen-pipeline`.
- Model download not allowed: set local model paths and offline cache before class initialization.
- UniEX uses `choice`; Ubert uses `choices`.
- UniMC expects multiple-choice-style fields `texta`, `textb`, `question`, `choice`, `label`, and `id`.
- `cuda=True` moves models to GPU. Pass `cuda=False` for CPU-only prediction when the model size permits it.

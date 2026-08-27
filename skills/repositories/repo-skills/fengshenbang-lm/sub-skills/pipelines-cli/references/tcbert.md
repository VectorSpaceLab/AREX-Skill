# TCBert Prompt Classification Pipeline

TCBert is a prompt-based Chinese topic classification route. Use it programmatically, not through `fengshen-pipeline`.

## Import and parser

```python
import argparse
from fengshen.pipelines.tcbert import TCBertPipelines

parser = argparse.ArgumentParser('Topic Classification')
parser = TCBertPipelines.piplines_args(parser)  # misspelled in the package
args = parser.parse_args([])
```

The method name is `piplines_args`, not `pipelines_args`. This spelling is part of the public source; calling the correctly spelled name raises `AttributeError` unless the installed package has been patched.

## Initialization and run shape

```python
pretrained_model_path = 'MODEL_OR_LOCAL_DIR'
args.learning_rate = 2e-5
args.max_length = 512
args.max_epochs = 3
args.batchsize = 1
args.default_root_dir = './'
args.fixed_lablen = 2

prompt = '下面是一则关于{}的新闻：'
prompt_label = {'汽车': '汽车', '科技': '科技'}
model = TCBertPipelines(args, model_path=pretrained_model_path, nlabels=len(prompt_label))
```

Training and prediction methods:

```python
model.train(train_data, dev_data, prompt, prompt_label)
result = model.predict(test_data, prompt, prompt_label, cuda=False)
```

Use `cuda=False` for CPU-only prediction/testing. `cuda=True` moves the model to GPU and requires a compatible CUDA PyTorch environment.

## Data schemas

Training and validation items must contain `content` and `label`:

```json
[
  {"content": "凌云研发的国产两轮电动车怎么样，有什么惊喜？", "label": "科技"}
]
```

Test items contain `content` only:

```json
[
  {"content": "街头偶遇2018款长安CS35，颜值美炸！或售6万起，还买宝骏510？"}
]
```

The prompt must contain exactly the label placeholder used by Python `str.format`, usually `{}`:

```json
"下面是一则关于{}的新闻："
```

`prompt_label` maps dataset labels to label surface forms inserted into the prompt. The mapped values can be shorter or more natural than the raw labels:

```json
{
  "汽车": "汽车",
  "旅游": "旅游",
  "经济生活": "经济生活",
  "房产新闻": "房产"
}
```

## Useful arguments

| Argument | Meaning |
|---|---|
| `--pretrained_model_path` | Model id/local path consumed by examples and parser; the class initializer separately receives `model_path`. |
| `--load_checkpoints_path` | Fine-tuned checkpoint path to load instead of initializing from the pretrained model. |
| `--train` | Boolean flag used by example code to decide whether to call `train`. |
| `--language` | Present in the parser, default `chinese`; TCBert examples are Chinese topic classification. |
| `--fixed_lablen` | Model-specific label length setting; useful when label surface lengths differ. |
| Trainer/checkpoint/model utility flags | Added through Fengshen helpers and PyTorch Lightning; route detailed tuning to `data-training`. |

## Common failure modes

- `AttributeError: type object 'TCBertPipelines' has no attribute 'pipelines_args'`: use `piplines_args`.
- `TypeError` during initialization: pass both `model_path` and `nlabels=len(prompt_label)`.
- Prompt has no `{}` placeholder: labels cannot be inserted into the template.
- Training item missing `content` or `label`: the data model cannot build prompt classification samples.
- Test item includes no `content`: prediction has no text to classify.
- `cuda=True` on a CPU-only environment: pass `cuda=False` or prepare the CUDA backend.
- Running through `fengshen-pipeline tcbert ...`: the generic console contract is not satisfied by TCBert's parser/helper spelling and initializer requirements.

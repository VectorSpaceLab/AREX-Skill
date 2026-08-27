# Workflows: Pipeline Basics

## 1) Canonical install/import smoke

Run the bundled script from anywhere:

```bash
python scripts/check_openprompt_install.py
```

The script runs from a temporary working directory, imports the installed `openprompt` package, does not download models, verifies the published signatures, and runs a tiny fake-wrapper `PromptDataLoader` check.

## 2) Minimal classification quickstart

```python
from openprompt.data_utils import InputExample
from openprompt.plms import load_plm
from openprompt.prompts import ManualTemplate, ManualVerbalizer
from openprompt import PromptDataLoader, PromptForClassification

classes = ["negative", "positive"]
dataset = [
    InputExample(guid=0, text_a="Great film.", label=1),
    InputExample(guid=1, text_a="Bad film.", label=0),
]

plm, tokenizer, model_config, WrapperClass = load_plm("bert", "bert-base-cased")
template = ManualTemplate(tokenizer=tokenizer, text='{"placeholder":"text_a"} It was {"mask"}')
verbalizer = ManualVerbalizer(
    tokenizer=tokenizer,
    classes=classes,
    label_words={"negative": ["bad"], "positive": ["great"]},
)

loader = PromptDataLoader(
    dataset=dataset,
    template=template,
    tokenizer=tokenizer,
    tokenizer_wrapper_class=WrapperClass,
    max_seq_length=128,
    batch_size=2,
)
model = PromptForClassification(plm=plm, template=template, verbalizer=verbalizer)
```

Notes:

- `load_plm()` can hit the network. For offline use, point `model_path` at a local cache or pre-downloaded directory.
- `PromptForClassification(batch)` returns label logits; the surrounding training loop is out of scope for this sub-skill.

## 3) Minimal generation quickstart

```python
from openprompt import PromptDataLoader, PromptForGeneration

# Use a generation-aware template and a cached or local PLM.
loader = PromptDataLoader(
    dataset=dataset,
    template=template,
    tokenizer=tokenizer,
    tokenizer_wrapper_class=WrapperClass,
    batch_size=1,
    teacher_forcing=True,
    predict_eos_token=True,
    decoder_max_length=32,
)

gen_model = PromptForGeneration(plm=plm, template=template, tokenizer=tokenizer)
loss = gen_model(next(iter(loader)))
```

Notes:

- `PromptForGeneration` expects generation-compatible batches and template behavior.
- `teacher_forcing=True` and `predict_eos_token=True` are the key loader flags for the common generation path.

## 4) Offline fake-wrapper smoke

Use this when you only need to validate loader mechanics and batch collation:

```python
from openprompt import PromptDataLoader
from openprompt.data_utils import InputExample

class TinyTemplate:
    def wrap_one_example(self, example):
        return [[{"text": example.text_a, "loss_ids": 0, "shortenable_ids": 0},
                 {"text": "<mask>", "loss_ids": 1, "shortenable_ids": 0}],
                {"guid": example.guid, "label": example.label}]

class TinyWrapper:
    def __init__(self, tokenizer, max_seq_length=8, truncate_method="tail", decoder_max_length=-1, predict_eos_token=False, **kwargs):
        self.tokenizer = tokenizer
        self.max_seq_length = max_seq_length
        self.truncate_method = truncate_method
        self.decoder_max_length = decoder_max_length
        self.predict_eos_token = predict_eos_token

    def tokenize_one_example(self, wrapped_example, teacher_forcing=False):
        return {
            "input_ids": [11, 12],
            "attention_mask": [1, 1],
            "token_type_ids": [0, 0],
            "loss_ids": [0, 1],
        }

loader = PromptDataLoader(
    dataset=[InputExample(guid="demo-0", text_a="hello", label=1)],
    template=TinyTemplate(),
    tokenizer=object(),
    tokenizer_wrapper_class=TinyWrapper,
    max_seq_length=8,
    batch_size=1,
)
```

The important contract is that the fake wrapper returns keys that `InputFeatures` accepts and keeps metadata keys (`guid`, `label`, `tgt_text`) out of the wrapper output.

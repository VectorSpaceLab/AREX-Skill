# Perceptron API Reference

## High-level legacy wrapper

```python
from ltp import LTP
ltp = LTP("LTP/legacy")
output = ltp.pipeline(["他叫汤姆去拿外衣。"], tasks=["cws", "pos", "ner"])
```

Inspected legacy pipeline signature:

```python
pipeline(*args, tasks=None, raw_format=False, parallelism=True, return_dict=True)
```

Default tasks are `cws`, `pos`, and `ner`. Unsupported tasks raise `ValueError`.

## Direct model classes

```python
from ltp_extension.perceptron import CWSModel, POSModel, NERModel
```

| Class | Load | Predict input | Output |
| --- | --- | --- | --- |
| `CWSModel` | `CWSModel.load(path)` or `CWSModel(path)` | raw text string | words |
| `POSModel` | `POSModel.load(path)` or `POSModel(path)` | words | POS tags |
| `NERModel` | `NERModel.load(path)` or `NERModel(path)` | words and POS tags | NER tags/spans depending caller/raw mode |

All three expose `predict`, `batch_predict`, `load`, and `save`. `batch_predict` accepts `parallelism=True` by default.

## CWS customization

`CWSModel` exposes character and feature rule methods:

```python
from ltp_extension.perceptron import CharacterType

cws.enable_type_cut(CharacterType.Roman, CharacterType.Kanji)
cws.enable_type_cut_d(CharacterType.Roman, CharacterType.Kanji)
cws.enable_type_concat(CharacterType.Digit, CharacterType.Roman)
cws.enable_type_concat_d(CharacterType.Digit, CharacterType.Roman)
cws.disable_type_rule(CharacterType.Digit, CharacterType.Roman)
cws.disable_type_rule_d(CharacterType.Digit, CharacterType.Roman)
```

Available `CharacterType` members are `Digit`, `Roman`, `Hiragana`, `Katakana`, `Kanji`, and `Other`.

## Hook and entity utilities

```python
from ltp_extension.algorithms import Hook, get_entities, eisner
hook = Hook()
hook.add_word("长江大桥", 2)
words = hook.hook("我经过长江大桥", ["我", "经过", "长江", "大桥"])
entities = get_entities(["B-Nh", "I-Nh", "O", "S-Ns"])
```

Live inspection confirmed `get_entities` returns `(tag, start, end)` tuples such as `('Nh', 0, 1)`.

## Trainer classes

```python
from ltp_extension.perceptron import Algorithm, ModelType, Trainer, CWSTrainer, POSTrainer, NERTrainer
```

- `Algorithm(algorithm, param=None)` supports documented names `AP`, `Pa`, `PaI`, and `PaII`.
- `ModelType(model_type=None)` has `Auto`, `CWS`, `POS`, and `NER` members.
- Specialized trainers: `CWSTrainer()`, `POSTrainer(labels)`, `NERTrainer(labels)`.
- Generic trainer: `Trainer(model_type=ModelType.Auto, labels=None)`; some built-in signatures may not be introspectable, so prefer examples and explicit keyword-style construction where possible.

Trainer properties/methods include:

```text
epoch, shuffle, verbose, algorithm, eval_threads, compress, ratio, threshold,
load_train_data(path), load_eval_data(path), train(), eval(model)
```

Use the bundled trainer config checker before calling `train()`.

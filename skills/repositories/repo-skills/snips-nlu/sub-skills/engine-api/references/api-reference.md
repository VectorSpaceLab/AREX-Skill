# SnipsNLUEngine API reference

This reference is self-contained for operating Snips NLU's Python engine API.
It assumes the caller already has a valid Snips dataset dict or JSON file.
For dataset construction or resource acquisition, route to
`../dataset-and-resources/SKILL.md`.

## Imports and public entry points

```python
import json

from snips_nlu import SnipsNLUEngine
from snips_nlu.default_configs import CONFIG_EN  # also CONFIG_DE, CONFIG_ES, ...
from snips_nlu.pipeline.configs import NLUEngineConfig
```

Verified engine APIs:

- `SnipsNLUEngine(config=None, **shared)`
- `engine.fit(dataset, force_retrain=True)`
- `engine.parse(text, intents=None, top_n=None)`
- `engine.get_intents(text)`
- `engine.get_slots(text, intent)`
- `engine.persist(path)`
- `SnipsNLUEngine.from_path(path, **shared)`
- `NLUEngineConfig(intent_parsers_configs=None, random_seed=None)`

Important shared keyword arguments accepted through `**shared` include
`random_state`, `resources`, `builtin_entity_parser`, `custom_entity_parser`,
and `bypass_version_check` for loading persisted engines.

## Engine construction

```python
# Let Snips NLU pick the default config from dataset["language"] during fit.
engine = SnipsNLUEngine()

# Use a language-specific default config explicitly.
engine = SnipsNLUEngine(config=CONFIG_EN)

# Make training reproducible when supported by the dependency stack.
engine = SnipsNLUEngine(config=CONFIG_EN, random_state=42)
```

If `config` is `None`, `fit` inspects the dataset language and uses a packaged
language default when available. If no language default exists, it falls back to
a generic `NLUEngineConfig()` with deterministic and probabilistic parsers.

## Fitting

```python
with open("dataset.json", encoding="utf8") as f:
    dataset = json.load(f)

engine = SnipsNLUEngine(random_state=42)
engine.fit(dataset)
```

`fit` validates and normalizes the dataset, loads required language resources,
builds entity parsers when not provided, creates or reuses configured intent
parsers, trains them, and records dataset metadata used for later intent and
slot validation.

`force_retrain` controls parser reuse:

```python
engine.fit(dataset, force_retrain=False)
```

- `True` (default): retrain configured parser sub-units.
- `False`: reuse already-fitted parser sub-units where possible and train only
  missing parts. This is useful only when an engine already contains compatible
  pre-fitted parser objects.

## Parsing text

```python
result = engine.parse("turn on the lights in the kitchen")
```

The default `parse` return shape is a dict:

```json
{
  "input": "turn on the lights in the kitchen",
  "intent": {
    "intentName": "TurnLightOn",
    "probability": 0.87
  },
  "slots": [
    {
      "range": {"start": 26, "end": 33},
      "rawValue": "kitchen",
      "value": {"kind": "Custom", "value": "kitchen"},
      "entity": "room",
      "slotName": "room"
    }
  ]
}
```

Slot fields:

- `range.start` / `range.end`: character offsets in the input.
- `rawValue`: surface substring from the user text.
- `value`: resolved value. Custom entities use `{"kind": "Custom", "value": ...}`;
  builtin entities use their builtin resolution payload.
- `entity`: entity name, for example `room` or `snips/datetime`.
- `slotName`: slot name declared by the training dataset.

## None intent behavior

Snips NLU adds an implicit None intent for utterances that do not match the
training intents. In Python it is represented as `None`; in JSON it appears as
`null`.

```json
{
  "input": "unrelated text",
  "intent": {"intentName": null, "probability": 0.55},
  "slots": []
}
```

When `intentName` is `None`, `get_slots(text, None)` returns `[]`.

## Intent filters

Use intent filters when application context restricts the possible intents:

```python
result = engine.parse(
    "turn on the lights in the kitchen",
    intents=["TurnLightOn", "TurnLightOff"],
)
```

Rules:

- `intents` may be a single string or a list of strings.
- Every provided intent must exist in the fitted dataset; unknown names raise
  `IntentNotFoundError`.
- The None intent is never filtered out and may still be returned.
- Filters can improve classification accuracy because non-contextual intents
  are excluded from the classification scope.

## Top-N parsing

When `top_n` is set, `parse` returns a list of extraction results instead of a
single parsing result:

```python
results = engine.parse("turn on kitchen lights", top_n=3)
```

Each item omits the `input` field:

```json
{
  "intent": {"intentName": "TurnLightOn", "probability": 0.87},
  "slots": []
}
```

Rules:

- The returned list contains at most `top_n` items.
- It may contain fewer items if filters remove intents or `top_n` exceeds the
  total number of known intents plus the None intent.
- With both `intents` and `top_n`, the result is first classified, then filtered
  to requested intents plus None, then truncated.
- Slots are computed per listed intent; None-intent items have empty slots.

## Intent-only classification

```python
intents = engine.get_intents("turn on kitchen lights")
```

Return shape:

```json
[
  {"intentName": "TurnLightOn", "probability": 0.64},
  {"intentName": null, "probability": 0.26},
  {"intentName": "TurnLightOff", "probability": 0.23}
]
```

The list is ordered by decreasing score and has exactly the number of dataset
intents plus one for the None intent. These values are confidence scores in
`[0, 1]`; they are not guaranteed to sum to `1.0`.

## Slot-only extraction

Use `get_slots` when the application already knows the intent:

```python
slots = engine.get_slots("turn on the lounge lights", "TurnLightOn")
```

Return shape is a list of resolved slot dicts. If `intent` is `None`, the
method returns `[]`. If `intent` is not part of the fitted dataset, it raises
`IntentNotFoundError`.

## Required fitted state and input types

- `parse`, `get_intents`, and `get_slots` require a fitted engine; otherwise
  they raise `NotTrained`.
- `parse` and `get_slots` require Python `str` text. Bytes or other non-string
  inputs raise `InvalidInputError`.

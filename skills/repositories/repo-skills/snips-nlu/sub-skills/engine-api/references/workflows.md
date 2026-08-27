# Engine API workflows

These workflows assume `snips-nlu` is importable and language resources needed
by the dataset are available. For dataset authoring and resource setup, route
to `../dataset-and-resources/SKILL.md`.

## Minimal fit and parse

```python
import json
from snips_nlu import SnipsNLUEngine

with open("dataset.json", encoding="utf8") as f:
    dataset = json.load(f)

engine = SnipsNLUEngine(random_state=42)
engine.fit(dataset)

result = engine.parse("What will be the weather in San Francisco next week?")
print(json.dumps(result, ensure_ascii=False, indent=2))
```

Expected control flow:

1. Load a valid Snips dataset dict.
2. Build `SnipsNLUEngine`.
3. Call `fit` before any parsing method.
4. Call `parse`, `get_intents`, or `get_slots`.
5. Treat confidence values as scores, not normalized probabilities.

## Parse with context-specific intent filters

```python
allowed = ["sampleGetWeather", "sampleTurnOnLight"]
result = engine.parse("turn on the light in the kitchen", intents=allowed)
```

Use this when application context rules out some intents. Do not pass arbitrary
user-provided intent names without checking that they exist in the training
dataset; unknown names raise `IntentNotFoundError`. The implicit None intent is
always eligible, even when a filter is provided.

## Return ranked intent hypotheses and slots

```python
ranked = engine.parse(
    "turn on the light in the kitchen",
    intents=["sampleGetWeather", "sampleTurnOnLight"],
    top_n=3,
)
```

When `top_n` is provided, `ranked` is a list. Each item contains:

```python
{
    "intent": {"intentName": "...", "probability": 0.0},
    "slots": [],
}
```

The `input` key appears only in the single-result `parse` shape. The returned
list can be shorter than `top_n`.

## Intent-only then slot-only APIs

```python
intents = engine.get_intents("turn on the light in the kitchen")

best_intent = intents[0]["intentName"]
slots = engine.get_slots("turn on the light in the kitchen", best_intent)
```

Use this pattern when application policy, dialog state, or business rules need
to inspect ranked intents before deciding whether to extract slots. If the
chosen intent is `None`, `get_slots` returns an empty list.

## Persist and reload a fitted engine

```python
from pathlib import Path
from snips_nlu import SnipsNLUEngine

persist_dir = Path("engine_artifact")
engine.persist(persist_dir)  # path must not already exist

loaded = SnipsNLUEngine.from_path(persist_dir)
print(loaded.parse("turn on the kitchen lights"))
```

Persistence is useful when training and serving happen in separate processes or
machines. Persisted artifacts include engine metadata, parser sub-artifacts,
entity parsers, and the required subset of language resources when the engine
is fitted.

## Use byte-array serialization for transport

The engine inherits `to_byte_array` and `from_byte_array` from the processing
unit abstraction:

```python
payload = engine.to_byte_array()
loaded = SnipsNLUEngine.from_byte_array(payload)
```

Use this for in-memory transport or tests. For long-lived model storage, prefer
`persist`/`from_path` so files can be inspected and versioned.

## Reproducible training pattern

```python
seed = 42
engine = SnipsNLUEngine(random_state=seed)
engine.fit(dataset)
```

For reproducibility, keep all of the following fixed:

- the Snips NLU package/model version,
- Python and dependency versions,
- language resources,
- dataset content and ordering,
- `random_state`.

Older dependency stacks can still have nondeterministic behavior; see
`troubleshooting.md`.

## Bundled smoke helper

The bundled helper adapts the package sample into a source-independent command
that accepts an explicit dataset JSON:

```bash
python scripts/snips_nlu_engine_smoke.py \
  --dataset path/to/dataset.json \
  --query "What will be the weather in San Francisco next week?" \
  --intent-filter sampleGetWeather \
  --top-n 2 \
  --persist-dir engine_artifact
```

Behavior:

- loads the dataset JSON from `--dataset`,
- fits `SnipsNLUEngine(random_state=...)`,
- calls `parse`, `get_intents`, and `get_slots` for the top intent when
  applicable,
- optionally persists to a non-existing `--persist-dir` and reloads it,
- prints one JSON report to standard output,
- reports missing resources with a clear resource download/link next step,
- refuses to overwrite an existing persistence directory.

Use the helper as a smoke test, not as a benchmark or final verification suite.
CLI evaluation workflows belong to `../cli-workflows/SKILL.md`.

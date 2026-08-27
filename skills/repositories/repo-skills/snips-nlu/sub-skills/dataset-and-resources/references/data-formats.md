# Snips NLU dataset data formats

Snips NLU accepts two authoring/training representations:

- **YAML authoring documents** are convenient for humans. Each YAML document is either an intent or an entity and can live in its own file or be combined with other documents separated by `---`.
- **JSON datasets** are the programmatic/training format. A JSON dataset is a single object with `language`, `intents`, and `entities` root keys.

Use `Dataset.from_yaml_files(language, filenames)` to convert YAML to JSON. Use `validate_and_format_dataset(dataset)` to validate JSON before passing it to training/API workflows.

## YAML entity documents

A custom entity document has `type: entity`, `name`, optional custom entity knobs, and `values`:

```yaml
---
type: entity
name: city
automatically_extensible: false  # default: true
use_synonyms: true               # default: true
matching_strictness: 0.8         # default: 1.0
values:
  - london
  - [new york, big apple]
  - [paris, city of lights]
```

Rules:

- Scalar values become canonical entity values with no synonyms.
- List values use the first item as the canonical `value`; remaining items are `synonyms`.
- If `type` is present, it must be `entity`; missing `name` is invalid.
- `automatically_extensible` controls whether values outside the explicit list may be extracted in similar contexts.
- `use_synonyms` controls whether synonyms resolve to the canonical value.
- `matching_strictness` is an intended `0.0` to `1.0` numeric knob; `1.0` is strictest.

## YAML intent documents

An intent document has `type: intent`, `name`, optional explicit `slots`, and non-empty `utterances`:

```yaml
---
type: intent
name: searchFlight
slots:
  - name: origin
    entity: city
  - name: destination
    entity: city
  - name: date
    entity: snips/datetime
utterances:
  - find me a flight from [origin](Paris) to [destination](New York)
  - I need a flight leaving [date](this weekend) to [destination](Berlin)
```

Slot annotation syntax is markdown-like:

- `[slot_name:entity](slot text)` gives the slot name, entity type, and example value in one annotation.
- `[slot_name](slot text)` relies on an explicit or inferred mapping from slot name to entity.
- `[slot_name:entity]` or `[slot_name]` omits the text value. Snips NLU will fill omitted values from known entity examples during YAML conversion.
- Different slot names may share the same entity type, for example `origin: city` and `destination: city`.

YAML gotchas:

- If an utterance begins with `[`, quote it as a YAML string: `"[origin] to [destination]"`.
- Multiple documents in the same YAML file must be separated with `---`.
- Missing `]` or missing `)` in an annotated utterance raises an intent format error that includes the faulty utterance.

## Implicit slot mappings and implicit values

The YAML loader completes missing slot/entity information in two stages:

1. If one occurrence says `[weatherLocation:location](Paris)`, later `[weatherLocation]` annotations infer the same `location` entity.
2. If a slot annotation omits the text value, conversion fills it from values known for that entity.

For custom entities, at least one value must exist either in an entity document or in an annotated utterance such as `[city](Paris)` / `[city:location](Paris)`. Built-in entities can obtain generated examples for the selected language, but this depends on the built-in parser/resources being available.

## JSON root schema

A JSON dataset root must contain exactly the operational keys below; additional keys may be ignored by downstream code, but keep authoring datasets simple.

```json
{
  "language": "en",
  "intents": {
    "searchFlight": {
      "utterances": [
        {
          "data": [
            {"text": "find me a flight from "},
            {"text": "Paris", "entity": "city", "slot_name": "origin"},
            {"text": " to "},
            {"text": "New York", "entity": "city", "slot_name": "destination"}
          ]
        }
      ]
    }
  },
  "entities": {
    "city": {
      "data": [
        {"value": "london", "synonyms": []},
        {"value": "new york", "synonyms": ["big apple"]}
      ],
      "use_synonyms": true,
      "automatically_extensible": true,
      "matching_strictness": 1.0
    },
    "snips/datetime": {}
  }
}
```

Root keys:

- `language`: one supported ISO code such as `en`, `fr`, or `pt_br`.
- `intents`: object mapping intent names to intent data.
- `entities`: object mapping entity names to custom entity data or empty built-in entity objects.

Intent data:

- Each intent requires `utterances`, a list.
- Each utterance requires `data`, a list of chunks.
- Every chunk requires `text`.
- A slot chunk must include both `entity` and `slot_name`; providing only one is invalid.

Custom entity data:

- `data`: list of entries with `value` and `synonyms`.
- `value`: canonical value string.
- `synonyms`: list of strings resolving to `value` when `use_synonyms` is true.
- `use_synonyms`: boolean.
- `automatically_extensible`: boolean.
- `matching_strictness`: integer or float; missing values may be filled as `1.0` by backward-compatibility code, but explicit is clearer.

Built-in entity data:

- Built-ins such as `snips/datetime`, `snips/number`, and `snips/temperature` are represented as empty objects in JSON authoring datasets.
- Do not define `data`, `synonyms`, or matching knobs for built-ins; use custom entity names for custom value lists.

## Validation behavior

`validate_and_format_dataset(dataset)` checks types and mandatory keys, rejects unknown languages, verifies custom entity references, formats custom entity values/synonyms, adds variations, and marks the result with `validated: true`.

The formatted return value is not identical to the authoring JSON: custom entities are transformed toward runtime fields such as `utterances` and `capitalize`. Keep a separate authoring file if humans need to edit the dataset later.

Use the bundled validator for a safe check:

```bash
python scripts/validate_snips_dataset.py --dataset dataset.json --explain
```

When YAML is the source, convert first, then validate the generated JSON:

```bash
python scripts/snips_yaml_to_json.py --language en intents.yaml entities.yaml --output dataset.json
python scripts/validate_snips_dataset.py --dataset dataset.json
```

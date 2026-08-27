# Dataset and resources troubleshooting

Use this page when YAML conversion, JSON validation, entity authoring, or local language-resource loading fails. For training/parsing/persistence failures, route to `../engine-api/SKILL.md`. For CLI downloads, links, metrics, or command execution, route to `../cli-workflows/SKILL.md`.

## Invalid YAML `type`

Symptoms:

- `Invalid 'type' value in YAML file ...`
- `Wrong type: 'intent'` while loading an entity.
- `Wrong type: 'entity'` while loading an intent.

Fix:

- Every YAML document must be either `type: intent` or `type: entity`.
- If multiple documents share a file, separate each document with `---`.
- Ensure intent documents have `name` and `utterances`; ensure entity documents have `name` and optional `values`.

## Missing custom entity values during YAML conversion

Symptom:

- `At least one entity value must be provided for entity '...'`

Cause:

- A YAML slot annotation omitted text, for example `[destination]`, and the entity is custom, but no value was available from an entity `values` list or another annotated utterance.

Fix options:

- Add an entity document with at least one value:
  ```yaml
  ---
  type: entity
  name: city
  values:
    - Paris
  ```
- Or add one explicit annotated value in an utterance, for example `[destination:city](Paris)`.
- Built-in entities such as `snips/datetime` do not need custom values, but they may still require the parser/resources for the chosen language.

## Slot annotation mistakes

Symptoms:

- `Missing ending ']' in annotated utterance ...`
- `Missing ending ')' in annotated utterance ...`
- JSON validation says `Expected chunk to have key: 'slot_name'`.
- JSON validation says `Expected entities to have key: 'some_entity'`.

Fix:

- Use one of the valid YAML forms: `[slot:entity](text)`, `[slot](text)`, `[slot:entity]`, or `[slot]`.
- If using `[slot]`, define the mapping in `slots:` or establish it earlier with `[slot:entity]`.
- Do not leave unbalanced brackets or parentheses in annotated utterances.
- Quote an utterance that starts with `[` so YAML treats it as a string.
- In JSON, a slot chunk must have `text`, `entity`, and `slot_name`; a plain text chunk has only `text`.
- In JSON, every non-built-in `entity` referenced by an utterance must appear in the root `entities` object.

## Invalid JSON root keys or object types

Symptoms:

- `Missing key: 'language'`
- `Missing key: 'intents'`
- `Missing key: 'entities'`
- `Invalid type for 'dataset'`, `language`, `intents`, `entities`, `utterances`, or `utterance data`.

Fix:

- The JSON root must be an object with `language` as a string and `intents` / `entities` as objects.
- Each intent value must be an object with `utterances` as a list.
- Each utterance must be an object with `data` as a list.
- Each chunk must be an object with `text`; slot chunks also need both `entity` and `slot_name`.

Run:

```bash
python scripts/validate_snips_dataset.py --dataset dataset.json --explain
```

## Missing or malformed custom entity fields

Symptoms:

- `Expected custom entity to have key: 'use_synonyms'`
- `Expected custom entity to have key: 'automatically_extensible'`
- `Expected custom entity to have key: 'data'`
- `Expected entity entry to have key: 'value'`
- `Expected entity entry to have key: 'synonyms'`

Fix:

- Custom entities need `data`, `use_synonyms`, `automatically_extensible`, and preferably explicit `matching_strictness`.
- Each `data` entry must contain a string `value` and list `synonyms`.
- Avoid empty values or empty synonyms; validation trims and drops them, which can hide authoring mistakes.
- If using a built-in entity, represent it as `{}` instead of a custom entity object.

## Unsupported language or resource names

Symptoms:

- `Unknown language: 'eng'`
- `Language resource '...' not found`
- `Unknown gazetteer for language ...`
- `Unknown word clusters for language ...`

Fix:

- Use supported language codes: `de`, `en`, `es`, `fr`, `it`, `ja`, `ko`, `pt_br`, `pt_pt`.
- Use valid resource names and valid `required_resources` entries for the selected language.
- Do not invent aliases such as `eng` or `pt-br`; use Snips NLU's exact codes.

## Missing language resources

Symptoms:

- Resource loading fails even though the dataset schema is correct.
- Built-in entity conversion or validation fails because parser/resources for a language are unavailable.
- Error text suggests `python -m snips_nlu download <name>`.

Fix:

- Treat this as environment/resource setup, not dataset authoring.
- Route CLI setup commands to `../cli-workflows/SKILL.md`.
- After resources are installed or linked, rerun conversion/validation; do not rewrite custom entities just to mask a missing resource.

## Built-in entity confusion

Symptoms:

- A built-in such as `snips/datetime` is given custom `data` and `synonyms`.
- A misspelled built-in such as `snips/dateTime` behaves like a malformed custom entity.
- A custom entity is named with the `snips/` prefix and then fails validation or parsing unexpectedly.

Fix:

- Use exact lowercase/camel-case built-in identifiers, for example `snips/datetime`, `snips/number`, `snips/temperature`, `snips/amountOfMoney`.
- Built-ins belong in JSON as empty objects: `"snips/datetime": {}`.
- Put domain-specific lists under custom entity names without the `snips/` prefix.
- Remember that built-ins return structured resolved values; custom entities return `kind: Custom` values resolved through custom data and synonyms.

## When validation output looks different from input

`validate_and_format_dataset` returns a formatted runtime structure. It may:

- sort intents/entities;
- add `validated: true`;
- replace custom entity `data` with runtime `utterances`;
- add generated spelling/case/number variations;
- add `capitalize` for custom entities.

Keep an editable authoring JSON or YAML source separately if humans need to maintain the dataset.

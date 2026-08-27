# Resources and entities

Snips NLU separates **custom entities** authored in the dataset from **built-in entities** whose extraction/resolution is provided by Snips NLU parsers and language resources.

## Supported dataset languages

Use the language code in the JSON root `language` key or as the first argument to YAML conversion. Supported codes are:

- `de`
- `en`
- `es`
- `fr`
- `it`
- `ja`
- `ko`
- `pt_br`
- `pt_pt`

Any other code, such as `eng`, is rejected by dataset validation.

## Built-in entity identifiers

Built-in entity names start with `snips/` and are used directly in slots and the JSON `entities` map. Common examples:

- `snips/datetime` for natural-language date/time expressions.
- `snips/number` for numeric expressions.
- `snips/temperature` for temperature expressions.

Broad built-in coverage:

| Built-in identifier | Category | Supported languages |
| --- | --- | --- |
| `snips/amountOfMoney` | grammar | `de`, `en`, `es`, `fr`, `it`, `ja`, `ko`, `pt_br`, `pt_pt` |
| `snips/duration` | grammar | `de`, `en`, `es`, `fr`, `it`, `ja`, `ko`, `pt_br`, `pt_pt` |
| `snips/number` | grammar | `de`, `en`, `es`, `fr`, `it`, `ja`, `ko`, `pt_br`, `pt_pt` |
| `snips/ordinal` | grammar | `de`, `en`, `es`, `fr`, `it`, `ja`, `ko`, `pt_br`, `pt_pt` |
| `snips/temperature` | grammar | `de`, `en`, `es`, `fr`, `it`, `ja`, `ko`, `pt_br`, `pt_pt` |
| `snips/datetime` | grammar | `de`, `en`, `es`, `fr`, `it`, `ja`, `ko`, `pt_br`, `pt_pt` |
| `snips/date`, `snips/time`, `snips/datePeriod`, `snips/timePeriod` | grammar | `en` |
| `snips/percentage` | grammar | `de`, `en`, `es`, `fr`, `it`, `ja`, `pt_br`, `pt_pt` |
| `snips/musicAlbum`, `snips/musicArtist`, `snips/musicTrack` | gazetteer | `de`, `en`, `es`, `fr`, `it`, `ja`, `pt_br`, `pt_pt` |
| `snips/city`, `snips/country`, `snips/region` | gazetteer | `de`, `en`, `es`, `fr`, `it`, `ja`, `pt_br`, `pt_pt` |

Grammar built-ins perform resolution into structured values such as numbers, temperatures, durations, or instants/intervals. Gazetteer built-ins rely on resource lists.

In JSON authoring datasets, represent built-ins as empty objects:

```json
"entities": {
  "snips/datetime": {},
  "snips/number": {}
}
```

Do not add `data`, `synonyms`, `use_synonyms`, `automatically_extensible`, or `matching_strictness` to built-ins; those fields are for custom entities.

## Custom entity behavior

A custom entity is any entity name not recognized as a Snips built-in. It is represented with explicit authoring fields:

```json
"entities": {
  "beverage_type": {
    "data": [
      {"value": "espresso", "synonyms": ["expresso", "espressos"]},
      {"value": "tea", "synonyms": []}
    ],
    "use_synonyms": true,
    "automatically_extensible": true,
    "matching_strictness": 1.0
  }
}
```

Field semantics:

- `data`: examples for the entity. Entries with empty `value` are discarded during validation; avoid relying on that cleanup.
- `value`: canonical value returned when the entity resolves.
- `synonyms`: alternative surface forms for the canonical value.
- `use_synonyms`: if true, synonyms map to the canonical value; if false, synonyms are not used for that mapping.
- `automatically_extensible`: if true, Snips NLU may extract unseen values in similar contexts; if false, it behaves more like a whitelist.
- `matching_strictness`: numeric strictness knob, normally `1.0`; lower values relax matching.

Validation also merges values observed in annotated utterances into custom entity runtime utterances. This means a JSON custom entity can have an empty `data` list if slot chunks in intent utterances provide concrete text values.

## Language resources

`load_resources(name, required_resources=None)` loads local language resources by:

- language/resource name such as `en` when resources are installed in the package data area;
- resource package name such as a language resource package;
- directory path containing a resource `metadata.json` and resource files.

The optional `required_resources` dict can restrict what is loaded. Resource keys include `gazetteers`, `word_clusters`, `stop_words`, `noise`, and `stems`. Unknown requested gazetteers or word clusters raise `ValueError`.

Missing language resources raise a `MissingResource` error that suggests running `python -m snips_nlu download <name>`. Treat that as a setup task: route command construction/execution to `../cli-workflows/SKILL.md` and avoid implicit downloads from this sub-skill.

## Practical choices

- Use built-ins when you need normalized structured values: dates/times, numbers, ordinals, percentages, amounts of money, durations, or temperatures.
- Use custom entities when the values are domain-specific: room names, beverage types, contact names, device names, product names, and similar lists.
- If a value list is finite and invalid values must be filtered out, set `automatically_extensible: false`.
- If the value universe is open-ended, set `automatically_extensible: true` and provide representative examples.
- If authoring YAML with omitted slot text, ensure each custom entity has at least one explicit value somewhere; built-ins can fill generated examples only when the relevant parser/resources are available.

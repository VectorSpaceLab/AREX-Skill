# DeepKE-LLM data formats

Use this reference when preparing, validating, or debugging instruction data for DeepKE-LLM workflows.

## Common instruction record fields

DeepKE-LLM instruction datasets such as IEPile and InstructIE commonly use records with these fields:

| Field | Meaning | Notes |
| --- | --- | --- |
| `task` | Task id such as `NER`, `RE`, `EE`, `EET`, `EEA`, `SPO`, or `KG` | Keep task ids consistent between conversion, training, and evaluation. |
| `source` | Dataset/source name | Useful for mixed datasets and provenance. |
| `instruction` | JSON string or text prompt containing an instruction, schema, and input | DeepKE's source converter serializes a JSON object as a string. |
| `output` | Expected extraction output as a JSON string, object, or list | Present for train/dev records; omitted or replaced with `label` for some test records. |
| `id` | Optional stable identifier | Helpful for test records and multi-schema splits. |

A serialized `instruction` string often contains:

```json
{
  "instruction": "You are an expert in relation extraction...",
  "schema": ["works_for", "lives_in"],
  "input": "Alice works for Acme."
}
```

The `output` should be parseable back into the selected task schema, for example:

```json
{"works_for": [["Alice", "Acme"]], "lives_in": []}
```

## JSONL versus JSON arrays

Most DeepKE-LLM converters write **JSONL**: one JSON object per line. A JSONL file is not a single JSON array. If `json.load()` raises `Extra data`, parse it line by line instead.

Use JSONL for large datasets and model predictions. Use JSON arrays only for small fixtures or when a specific downstream tool requires an array.

## Task-specific label shapes

### NER

Input records may contain:

```json
{"text": "Alice works in Paris.", "entities": [{"text": "Alice", "type": "person"}, {"text": "Paris", "type": "location"}], "schema": ["person", "location"]}
```

Instruction output shape:

```json
{"person": ["Alice"], "location": ["Paris"]}
```

### RE

Input records may contain:

```json
{"text": "Alice works for Acme.", "relations": [{"head": "Alice", "relation": "works_for", "tail": "Acme"}], "schema": ["works_for"]}
```

Instruction output shape:

```json
{"works_for": [["Alice", "Acme"]]}
```

### SPO / KG triples

Input records may contain:

```json
{"text": "Alice works for Acme.", "spo": [{"subject": "Alice", "predicate": "works_for", "object": "Acme"}], "schema": ["works_for"]}
```

Instruction output shape:

```json
{"works_for": [["Alice", "Acme"]]}
```

For open KG construction, preserve any entity type or tail type fields as extra metadata when the downstream evaluator expects them, but do not invent types if the source labels lack them.

### EE / EET / EEA

Event data is schema-sensitive. A compact event record may contain event type, trigger, and arguments. For train records, preserve a task-specific JSON output rather than flattening events into relation triples unless the user explicitly wants that conversion.

## Bundled converter contract

The bundled `convert_ie_instruction.py` is a safe standalone helper for common NER/RE/SPO/KG records. It does not reproduce every negative-sampling and clustering mode from DeepKE's source converter, but it is useful for small or custom data and for validating the instruction shape.

Example:

```bash
python scripts/convert_ie_instruction.py \
  --input sample.jsonl \
  --output instructions.jsonl \
  --task RE \
  --language en \
  --source custom-re \
  --mode train \
  --schema-field schema
```

It accepts input records with:

- `text` or `input` as the source sentence/document.
- `schema` or another field selected by `--schema-field`.
- NER labels under `entities`, `entity`, or `ner`.
- RE/SPO/KG labels under `relations`, `relation`, `spo`, `kg`, or `triples`.
- Existing `output` if `--output-from-field output` is supplied.

It writes JSONL records with `task`, `source`, `instruction`, and, in train mode, `output`.

## CodeKGC prompt files

CodeKGC uses three prompt file concepts:

| Concept | Contents | Validation |
| --- | --- | --- |
| Schema prompt | Python-like class definitions for relation types, entity types, `Triple`, and `Extract` | Class names should be legal identifiers and match allowed labels. |
| ICL examples | Text docstrings followed by `extract = Extract([...])` examples | Keep examples concise and label-balanced. |
| Test example | Target text appended after schema and examples | The model output should be parsed safely, not executed. |

Never execute untrusted code-model output. Treat generated Python-like text as a parse target.

## Data quality checks

1. Parse every line as JSON.
2. Confirm `instruction` contains a task description, schema, and input text.
3. Confirm train records have nonempty `output` values in the expected task schema.
4. Confirm schemas are not too large for the selected model's context window.
5. For mixed-language datasets, verify `--language zh` or `--language en` matches prompt templates.
6. For generated/synthetic data, preserve a provenance flag so it is not mistaken for gold labels.

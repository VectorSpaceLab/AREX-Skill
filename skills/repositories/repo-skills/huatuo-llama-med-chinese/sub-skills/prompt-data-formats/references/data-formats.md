# Data Formats

The assets covered by this sub-skill use three different serialization styles. Do not interchange them without converting deliberately.

## Format summary

| Asset family | Serialization | Required fields | Main use |
| --- | --- | --- | --- |
| Inference examples (`data/infer.json`) | JSON Lines: one JSON object per non-empty line | `instruction`, `input`, `output` | Small held-out prompts with reference answers for manual inference inspection. |
| Supervised tuning examples (`data/llama_data.json`) | JSON Lines: one JSON object per non-empty line | `instruction`, `input`, `output` | Medical instruction-tuning records consumed by JSON dataset loading. |
| Knowledge-tuning sample (`data/knowledge_tuning_data_sample.txt`) | Plain UTF-8 text, one question per line after a header | Header `input`; then question strings | Demonstrates questions used for question-to-knowledge style tuning. |
| Literature examples (`data-literature/liver_cancer.json`) | One JSON array containing objects | `instruction`, `input`, `output`; optional `id` | Literature-grounded Chinese multi-turn dialogue examples. |

## JSONL instruction records

`data/infer.json` and `data/llama_data.json` are JSONL, not a JSON array. Each non-empty line is a complete object:

```json
{"instruction": "麻风病和儿童哮喘的病因是否一致？", "input": "", "output": "不一致，麻风病的病因是麻风分枝杆菌，而儿童哮喘的病因是气候、药物、吸入过敏原等。"}
```

Required fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `instruction` | string | The question or task text inserted into the prompt template. |
| `input` | string | Optional additional context. The bundled medical examples usually use an empty string. |
| `output` | string | Reference answer. During training it is appended as the label; during inference examples it is the golden/reference response. |

Operational notes:

- Empty `input` selects `prompt_no_input` in the `Prompter`.
- Non-empty `input` selects `prompt_input`; use only templates that define that key.
- `output` must not be omitted even for inference example files, because inference scripts print it as the golden answer.
- JSONL files should not begin with `[` or contain commas between records.

## Literature JSON list

The literature asset is a single JSON document containing a list of objects, not JSONL. A representative record shape is:

```json
{
  "instruction": " <user>: 我听说免疫疗法是治疗晚期肝癌的一种很有效的方法，真的吗？ <bot>: 是的，免疫疗法是一种新兴的治疗方法... <user>: 但是，这是否适用于所有的肝癌患者？",
  "input": "",
  "output": "不是所有的肝癌患者都适合进行免疫疗法。根据患者的临床表现和病情，医生会对患者进行评估，从而选择最适合的治疗方案。",
  "id": 748
}
```

Required fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `instruction` | string | A Chinese dialogue context. It should begin with a `<user>:` turn; many records also include earlier `<bot>:` turns. |
| `input` | string | Present for compatibility; the sampled asset uses empty strings. |
| `output` | string | The next bot answer. |
| `id` | integer or string, optional | Optional record identifier. Some records have it and some do not. |

Use `literature_template` for these records unless you intentionally convert the prompt style. Because that template has no `prompt_input`, keep `input` empty or add a validated `prompt_input` variant.

## Knowledge-tuning sample text

The knowledge-tuning sample is a plain text list:

```text
input
多发性大动脉炎要去哪个科室就诊？
请问地尔硫的用法用量是怎么样的？
双氯芬酸钠贴片有哪些副作用？
```

The first line is the header `input`. Each subsequent non-empty line is one Chinese medical question. This file is a demonstration of the first stage of knowledge tuning: mapping a question to knowledge-retrieval parameters or knowledge, not a full `instruction/input/output` supervised-tuning file.

## Converting a JSON list to JSONL

Some tooling expects JSONL even when a source asset is a JSON list. Convert explicitly and preserve UTF-8 Chinese text:

```python
import json
from pathlib import Path

source = Path("liver_cancer.json")
target = Path("liver_cancer.jsonl")
records = json.loads(source.read_text(encoding="utf-8"))
with target.open("w", encoding="utf-8") as out:
    for record in records:
        out.write(json.dumps(record, ensure_ascii=False) + "\n")
```

Before using the converted file as ordinary training JSONL, confirm the selected template supports the record's `input` behavior and dialogue prefix format.

## Common invalid conversions

- Wrapping JSONL instruction records in `[` and `]` without changing the loader.
- Saving a JSON list with one object per line but leaving commas at line ends; this is neither valid JSONL nor a complete JSON list.
- Dropping empty `input` fields. Empty strings are still meaningful because code expects the key to exist.
- Treating benchmark questions as supervised records. Benchmark objects do not include reference answers.
- Replacing `<user>:` and `<bot>:` dialogue markers with Chinese full-width variants unless downstream prompt code is updated to match.

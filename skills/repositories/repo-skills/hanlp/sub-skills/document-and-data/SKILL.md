---
name: document-and-data
description: "Guides HanLP input and output data contracts, Document APIs, task
  keys, annotation schemas, JSON validation, pretty printing, and CoNLL
  conversion."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Document And Data

Use this sub-skill when the task is about HanLP input shapes, output JSON, `hanlp_common.Document`, task keys, annotation spans, pretty printing, CoNLL conversion, or validating a HanLP-like document.

## Read First

- Read `references/data-formats.md` for RESTful/native input shapes and output nesting.
- Read `references/document-api-reference.md` for verified `Document` methods.
- Read `references/annotation-keys.md` for task-key meanings and annotation schema notes.
- Read `references/troubleshooting.md` for malformed JSON, prefix mismatches, missing fields, and conversion issues.
- Run `scripts/document_smoke.py` to test `Document` behavior with a tiny fixture.
- Run `scripts/validate_document_json.py` to lightly validate a saved HanLP-like JSON object.

## Minimal Document Usage

```python
from hanlp_common.document import Document
doc = Document(tok=[["商品", "和", "服务"]], pos=[["NN", "CC", "NN"]])
print(doc.to_json())
print(doc.count_sentences())
print(doc.get_by_prefix("tok"))
```

## Route by Data Task

| User need | Use |
| --- | --- |
| Decide whether input should be raw text, sentence list, or tokenized sentences | `references/data-formats.md` |
| Interpret keys such as `tok/fine`, `pos/ctb`, `ner/msra`, `dep`, `con`, `srl`, `sdp`, `amr` | `references/annotation-keys.md` |
| Convert a `Document` to JSON, pretty text, or CoNLL | `references/document-api-reference.md` |
| Validate a JSON file before downstream processing | `scripts/validate_document_json.py` |

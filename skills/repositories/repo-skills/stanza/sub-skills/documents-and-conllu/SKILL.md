---
name: documents-and-conllu
description: "Manipulate Stanza Documents and CoNLL-U safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---
Use this sub-skill for Stanza document objects and CoNLL-U conversion.

Covers:
- `Document`, `Sentence`, `Token`, `Word`, and `Span`
- sentence comments and metadata (`sent_id`, `doc_id`, `speaker`, `sentiment`, `constituency`)
- entity and coreference fields
- serialization and round-tripping
- CoNLL-U parsing, writing, and validation

Route elsewhere when the task is about:
- pipeline construction, model download, or resource selection: `pipelines-and-resources`
- corpus conversion recipes or training data prep: `training-and-data-prep`
- CoreNLP server or protobuf outputs: `corenlp-client` unless the goal is to convert into a Stanza `Document`

Start here:
- `references/api-reference.md`
- `references/data-formats.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/validate_conllu.py`

If a file does not parse, run the validator first. These details were distilled from Stanza 1.14.0 source, tests, and installed API signatures; use the root provenance file when checking staleness. 
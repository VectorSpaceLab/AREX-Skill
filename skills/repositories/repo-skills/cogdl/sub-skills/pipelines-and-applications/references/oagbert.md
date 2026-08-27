# OAG-BERT Reference

## Purpose

Read this when the user asks for OAG-BERT paper, entity, similarity, or text
generation workflows. The model archive surface is optional and may require a
cache or network fetch.

## Verified loader

Public API:

```python
from cogdl.oag import oagbert
tokenizer, model = oagbert(model_name_or_path="oagbert-v1", load_weights=True)
```

The installed package returns a tokenizer plus a model object. Depending on the
variant, the tokenizer is either Hugging Face `BertTokenizer` or a
SentencePiece-based tokenizer.

## Supported archive/model names observed in the source

| Name | Notes |
| --- | --- |
| `oagbert-v1` | Vanilla English model |
| `oagbert-test` | Test archive used by the repo's CPU smoke tests |
| `oagbert-v2-test` | Test archive for the entity-aware version |
| `oagbert-v2` | Entity-aware English model |
| `oagbert-v2-lm` | Generation-oriented variant |
| `oagbert-v2-sim` | Sentence/OAG similarity variant |
| `oagbert-v2-zh` | Chinese variant |
| `oagbert-v2-zh-sim` | Chinese similarity variant |

## Common methods on the returned model

The README and tests exercise these methods on the OAG model family:

- `build_inputs(...)`
- `calculate_span_prob(...)`
- `decode_beamsearch(...)`
- `generate_title(...)`
- `encode_paper(...)`
- `forward(...)`

## Typical input fields

- `title`
- `abstract`
- `venue`
- `authors`
- `concepts`
- `affiliations`
- `decode_span_type`
- `decode_span_length`
- `mask_propmt_text`

Keep the academic-entity vocabulary and entity-type prompts aligned with the
selected model variant.

## Cache/network boundary

- OAG-BERT archives are fetched from remote URLs when the requested archive is
  not already present.
- The preflight inspection observed an `oagbert-test` archive/unpack failure in
  this environment, so treat OAG weights as optional and cache-dependent.
- Do not promise OAG-BERT availability without verifying the archive or local
  model path.

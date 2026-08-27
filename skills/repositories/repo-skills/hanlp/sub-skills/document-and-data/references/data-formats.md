# Data Formats

RESTful `/parse` accepts at least one of:

```json
{"text": "HanLP为生产环境带来次世代最先进的多语种NLP技术。"}
```

```json
{"text": ["第一句。", "第二句。"]}
```

```json
{"tokens": [["商品", "和", "服务"]], "tasks": ["ner", "dep"]}
```

Native MTL model input is sentence-level: a single sentence `str`, multiple sentences `list[str]`, or pre-tokenized `list[list[str]]` with `skip_tasks='tok*'` where supported.

Outputs are JSON-compatible dictionaries keyed by task names. Multi-sentence outputs are usually nested by sentence. Use `scripts/validate_document_json.py` for lightweight shape checks.

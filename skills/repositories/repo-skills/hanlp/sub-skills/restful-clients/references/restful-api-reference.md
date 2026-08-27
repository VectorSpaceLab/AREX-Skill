# RESTful API Reference

Verified Python signatures:

```python
HanLPClient(url: str, auth: str = None, language=None, timeout=60, verify=True)
HanLPClient.parse(text=None, tokens=None, tasks=None, skip_tasks=None, language=None) -> Document
HanLPClient.tokenize(text, coarse=None, language=None) -> list[list[str]]
```

`parse` accepts raw `text` string, `text` as a list of sentence strings, or `tokens` as `list[list[str]]`. `tasks` and `skip_tasks` select or skip task families. Per-call `language` overrides the client default.

Advanced client methods include `about`, `text_style_transfer`, `semantic_textual_similarity`, `coreference_resolution`, `abstract_meaning_representation`, `keyphrase_extraction`, `extractive_summarization`, `abstractive_summarization`, `grammatical_error_correction`, `text_classification`, `sentiment_analysis`, and `language_identification`. Server support and quota may vary by endpoint.

Use `scripts/restful_payload_preview.py` to build the JSON body for `/parse` without network calls.

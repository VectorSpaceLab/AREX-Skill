# API reference

## AnalyzerEngine

Use `AnalyzerEngine` for one text at a time.

Constructor shape:

```python
AnalyzerEngine(
    registry=None,
    nlp_engine=None,
    app_tracer=None,
    log_decision_process=False,
    default_score_threshold=0,
    supported_languages=None,
    context_aware_enhancer=None,
)
```

### `analyze(...)`

Key parameters:

- `text`: input string
- `language`: language code for the request
- `entities`: entity names to look for; omit it to search all entities known for that language
- `score_threshold`: request-level override for every returned result
- `ad_hoc_recognizers`: temporary pattern or deny-list recognizers for this call only
- `context`: extra context words from surrounding metadata
- `allow_list`: spans that should be kept out of the result
- `allow_list_match`: `exact` or `regex`
- `regex_flags`: flags used when `allow_list_match='regex'`
- `return_decision_process`: keep `analysis_explanation` on each result
- `nlp_artifacts`: precomputed NLP artifacts, if you already ran the NLP stage

Return value: `list[RecognizerResult]`.

### Score precedence

Threshold filtering resolves in this order:

1. request-level `score_threshold`, when supplied for this call
2. entity-specific threshold from the selected recognizer
3. recognizer `default`
4. engine `default_score_threshold`

### Other useful methods

- `get_recognizers(language=None)`
- `get_supported_entities(language=None)`

## BatchAnalyzerEngine

Use `BatchAnalyzerEngine` for iterables or nested dict/list inputs.

- `analyze_iterator(texts, language, batch_size=1, n_process=1, **kwargs)`
  - accepts primitive iterables only
  - returns `list[list[RecognizerResult]]`
- `analyze_dict(input_dict, language, keys_to_skip=None, batch_size=1, n_process=1, **kwargs)`
  - recurses into nested dicts and iterables
  - adds the current key to context automatically
  - useful for small JSON-like payloads, not for full structured-data pipelines

## RecognizerRegistry

Constructor shape:

```python
RecognizerRegistry(
    recognizers=None,
    global_regex_flags=regex.DOTALL | regex.MULTILINE | regex.IGNORECASE,
    supported_languages=None,
)
```

Core methods:

- `add_recognizer(recognizer)`
- `remove_recognizer(recognizer_name, language=None)`
- `load_predefined_recognizers(languages=None, nlp_engine=None, countries=None)`
- `add_recognizers_from_yaml(yml_path)`
- `get_recognizers(language, entities=None, all_fields=False, ad_hoc_recognizers=None)`
- `get_supported_entities(languages=None)`
- `get_country_codes()`

### Country filter rule

- locale-agnostic recognizers are always kept
- country-tagged recognizers are kept only when their country is requested
- `countries=[]` keeps only locale-agnostic recognizers
- `countries=None` disables country filtering

## Pattern, PatternRecognizer, RecognizerResult

### `Pattern`

```python
Pattern(name, regex, score)
```

### `PatternRecognizer`

Pattern and deny-list recognizer constructor shape:

```python
PatternRecognizer(
    supported_entity,
    name=None,
    supported_language="en",
    patterns=None,
    deny_list=None,
    context=None,
    deny_list_score=1.0,
    global_regex_flags=regex.DOTALL | regex.MULTILINE | regex.IGNORECASE,
    version="0.0.1",
    country_code=None,
)
```

Notes:

- supply either `patterns` or `deny_list`
- `country_code` tags a custom recognizer for country filtering
- `deny_list` is converted into regex logic internally
- subclass hooks: `validate_result(...)` and `invalidate_result(...)`

### `RecognizerResult`

Constructor shape:

```python
RecognizerResult(entity_type, start, end, score, analysis_explanation=None, recognition_metadata=None)
```

Important fields:

- `entity_type`
- `start`, `end`
- `score`
- `analysis_explanation`
- `recognition_metadata`

## Providers and NLP engines

### `NlpEngineProvider`

Constructor shape:

```python
NlpEngineProvider(
    nlp_engines=None,
    conf_file=None,
    nlp_configuration=None,
)
```

Default engine names:

- `spacy`
- `stanza`
- `transformers`
- `slim`
- `no_op`

Configuration notes:

- the default analyzer path uses the spaCy model `en_core_web_lg`
- `transformers` engine configs need both `spacy` and `transformers` model names
- `no_op` still requires a `models` list with at least one language entry

### `NoOpNlpEngine`

Constructor shape:

```python
NoOpNlpEngine(models=[{"lang_code": "en", "model_name": "no_op"}])
```

Use it when recognizers do not need linguistic features from tokens or lemmas.
It returns empty NLP artifacts, so explicit `context=` on `analyze()` is the only
context source it can help with.

### `AnalyzerEngineProvider`

Constructor shape:

```python
AnalyzerEngineProvider(
    analyzer_engine_conf_file=None,
    nlp_engine_conf_file=None,
    recognizer_registry_conf_file=None,
)
```

Use it for YAML-driven assembly of analyzer + NLP engine + registry. Inline
`nlp_configuration` and `recognizer_registry` sections in the analyzer YAML take
priority over separate per-section files.

### `RecognizerRegistryProvider`

Constructor shape:

```python
RecognizerRegistryProvider(
    conf_file=None,
    registry_configuration=None,
    nlp_engine=None,
)
```

Use it when you want registry-only YAML loading or dict-based registry assembly.

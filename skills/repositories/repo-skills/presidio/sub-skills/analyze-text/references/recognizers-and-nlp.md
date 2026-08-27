# Recognizers and NLP

## Pattern and custom recognizers

The fastest way to add text detection is `PatternRecognizer`.

```python
from presidio_analyzer import Pattern, PatternRecognizer

zip_pattern = Pattern(name="zip", regex=r"\b\d{5}(?:-\d{4})?\b", score=0.01)
zip_recognizer = PatternRecognizer(
    supported_entity="ZIP",
    patterns=[zip_pattern],
    context=["zip", "code"],
)
```

Deny-list recognizers use the same class:

```python
title_recognizer = PatternRecognizer(
    supported_entity="TITLE",
    deny_list=["Mr.", "Mrs.", "Dr.", "Professor"],
)
```

Add custom recognizers with `RecognizerRegistry.add_recognizer(...)` or pass
them as `ad_hoc_recognizers` for a single `analyze()` call.

### When to subclass

Subclass `EntityRecognizer` / `LocalRecognizer` when your logic needs:

- checksum or validation steps
- custom result pruning
- direct access to `NlpArtifacts`
- integration with a remote service or model wrapper

## YAML recognizer configs

Recognizer YAML can describe both predefined and custom recognizers.

Top-level keys:

- `supported_languages`
- `supported_countries`
- `global_regex_flags`
- `recognizers`

Recognizer entry rules:

- `type: predefined` or `type: custom`
- `name` is the instance label
- `class_name` can point at a different predefined class name
- `enabled: false` disables the entry
- `supported_language` and `supported_languages` are mutually exclusive
- `supported_entity` and `supported_entities` are mutually exclusive
- custom recognizers need `patterns` or `deny_list`
- `score_thresholds` can define a `default` plus entity overrides
- `country_code` tags custom recognizers for country filtering
- `text_chunker` config is used by chunked NER recognizers

A compact custom example:

```yaml
recognizers:
  - name: ZipCodeRecognizer
    type: custom
    supported_entity: ZIP
    supported_languages:
      - language: en
        context: [zip, code]
    patterns:
      - name: zip
        regex: '(\b\d{5}(?:-\d{4})?\b)'
        score: 0.01
```

### Country filtering

Use either:

- `RecognizerRegistry.load_predefined_recognizers(countries=["us", "uk"])`
- top-level YAML `supported_countries: ["us", "uk"]`

Rules:

- locale-agnostic recognizers stay loaded
- tagged country-specific recognizers are filtered by code
- `countries=[]` leaves only locale-agnostic recognizers
- YAML `country_code` on predefined entries must match the class-level `COUNTRY_CODE`

### Supported language shapes

`supported_languages` can be either:

- a list of strings: `['en', 'es']`
- a list of objects: `[{language: en, context: [...]}, ...]`

Use language-specific context words when the recognizer should score differently
per language.

## NLP engine routing

`NlpEngineProvider` supports these engine names:

- `spacy`
- `stanza`
- `transformers`
- `slim`
- `no_op`

### Default spaCy path

The default analyzer path expects the documented English spaCy model. If the
model is missing, the default `AnalyzerEngine()` path will fail until the model
is installed or a custom engine is provided.

### NoOpNlpEngine

Use `NoOpNlpEngine` for pattern-only workflows and smoke tests that must not
pull a model.

Important constraints:

- it still needs a `models` list
- each model needs `lang_code` and `model_name`
- it returns empty NLP artifacts
- NLP engine recognizers such as `SpacyRecognizer` are incompatible with it
- explicit request `context=` still works, but text-derived lemmas do not

### spaCy / Stanza / Transformers

- spaCy and Stanza are the standard NLP routes for tokenization and NER
- `transformers` needs both a spaCy pipeline name and a transformers model name
- `ner_model_configuration` controls label mapping, confidence shaping, and token alignment
- `transformers` is the right route when you need model-backed NER instead of only regex / deny-list logic

## Optional recognizer routes

### GLiNER

`GLiNERRecognizer` is useful when the model should map arbitrary labels to Presidio
entities.

Key knobs:

- `model_name`
- `entity_mapping` or `supported_entities` (mutually exclusive)
- `map_location` for device selection
- `load_onnx_model` for ONNX CPU compatibility
- `text_chunker` for long texts

If you need YAML, use `class_name: GLiNERRecognizer` and a `text_chunker` block.

### HuggingFace NER

`HuggingFaceNerRecognizer` is the direct token-classification route and is a
useful fallback for agglutinative languages where spaCy alignment is fragile.
Use it when you want the model's tokenizer and chunking behavior rather than the
spaCy alignment path.

### LangExtract

Use `BasicLangExtractRecognizer` or `AzureOpenAILangExtractRecognizer` when the
source model is an LLM/SLM via LangExtract.

Notes:

- `config_path` survives YAML validation and should be bundled with the skill
- connectivity is not validated at construction time; errors can appear on the
  first `analyze()` call
- Azure OpenAI settings can come from parameters or environment variables

### Azure AI Language

Use `AzureAILanguageRecognizer` for Azure AI Language PII detection. It accepts
an injected client or can build one from an Azure key and endpoint.

### AHDS

Use `AzureHealthDeidRecognizer` for Azure Health Data Services PHI detection. It
uses an injected de-identification client or the `AHDS_ENDPOINT` environment
variable.

## Wiring guidance

- Use `RecognizerRegistryProvider` for registry-only YAML.
- Use `AnalyzerEngineProvider` when you want one YAML to drive analyzer, NLP,
  and registry settings together.
- Keep `supported_languages` consistent across the analyzer, registry, and NLP
  engine configurations.

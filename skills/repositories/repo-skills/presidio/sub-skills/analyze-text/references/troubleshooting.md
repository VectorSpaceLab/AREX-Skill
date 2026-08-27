# Troubleshooting

Start with the bundled smoke scripts:

- `scripts/analyzer_smoke.py`
- `scripts/custom_recognizer_smoke.py`

They cover the most common default-model and no-download analyzer paths.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Default `AnalyzerEngine()` fails or cannot load the English NLP path | The documented default spaCy model is missing | Install the default model, or switch to `NoOpNlpEngine` plus pattern recognizers for a no-download path |
| Analyzer says a language is unsupported | The analyzer, registry, and NLP engine do not agree on `supported_languages` | Make the language set consistent across all three config layers |
| No result for a known entity | Wrong entity name, wrong language, or the recognizer was never loaded | Check `get_supported_entities()`, confirm the recognizer is in the registry, and verify the language filter |
| Score is lower or higher than expected | Request-level threshold, recognizer thresholds, or context words changed the score | Remember the precedence order: request `score_threshold` > entity-specific threshold > recognizer default > engine default |
| Allow-list did not remove a result | `allow_list_match` mode does not match the data | Use `exact` for exact span equality or `regex` for pattern matching; set `regex_flags` when needed |
| Allow-list regex appears to do nothing | The regex timed out or a blank allow-list entry was ignored | Simplify the pattern, keep an eye on `REGEX_TIMEOUT_SECONDS`, and remove empty entries |
| Regex matching behaves oddly across case or line breaks | The flags are different from what you expected | Check `global_regex_flags`, request `regex_flags`, and any per-recognizer regex flags |
| A custom YAML recognizer fails to load | `patterns` / `deny_list` / language / entity fields are malformed | Verify that custom recognizers have either `patterns` or `deny_list`, and that `supported_language` / `supported_languages` are not both set |
| A predefined YAML entry with `country_code` fails | The YAML country tag does not match the class-level `COUNTRY_CODE`, or the class is not country-tagged | Make the YAML and class tag match, or remove the YAML `country_code` for locale-agnostic recognizers |
| Country filtering returns too little | The recognizer is not tagged, or the requested country list is wrong | Check `get_country_codes()`, make sure the country code is lowercased and non-empty, and remember that untagged recognizers are always kept |
| `NoOpNlpEngine` raises compatibility errors | NLP engine recognizers are still enabled | Remove `SpacyRecognizer`, `StanzaRecognizer`, or `TransformersRecognizer` from the registry when using NoOp |
| `transformers`, `stanza`, `gliner`, `langextract`, `azure-ai-language`, or `ahds` imports fail | Optional extras are missing | Install only the extra needed for the route you want |
| GPU is available but the model still runs on CPU | GPU support is optional and model/device selection is explicit | Use the GPU-aware recognizer or engine options; CPU fallback is expected and supported |
| `AnalyzerEngineProvider` or registry YAML seems to ignore a change | Inline analyzer config can override separate per-section files | Recheck which YAML layer owns the setting and whether the file path actually points at the intended config |
| `LangExtract` or Azure recognizer only fails on first use | Connectivity is not checked at construction time | Confirm endpoint, credentials, and config path before calling `analyze()` |

## Default model diagnostics

If the default analyzer path fails but `NoOpNlpEngine` plus custom recognizers
works, the problem is model availability rather than the analyzer API. That is a
good signal to install the default spaCy model or keep the workflow pattern-only.

## Threshold and allow-list pitfalls

- `allow_list_match='exact'` compares the final span text literally.
- `allow_list_match='regex'` uses regex matching on the final span text.
- The allow list is applied after low-score filtering and duplicate removal.
- Request-level `score_threshold` overrides recognizer-level thresholds for that call.
- Context can boost results even when the regex is weak.

## YAML config pitfalls

- `supported_language` and `supported_languages` are mutually exclusive.
- `supported_entity` and `supported_entities` are mutually exclusive.
- `score_thresholds` must be a mapping.
- `text_chunker` fields must match the selected `chunker_type`.
- Blank or malformed `country_code` values are rejected.
- If you need service startup or HTTP deployment, use the root Presidio service reference instead of this sub-skill.

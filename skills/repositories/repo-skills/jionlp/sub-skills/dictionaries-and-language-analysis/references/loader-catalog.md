# Loader catalog

## Common packaged loaders and return shapes
- `stopwords_loader() -> list[str]`
- `negative_words_loader() -> list[str]`
- `china_location_loader(detail=False) -> nested dict`
- `china_location_change_loader() -> list[dict]`
- `world_location_loader() -> nested dict`
- `pinyin_char_loader() -> dict[str, list[str]]`
- `pinyin_phrase_loader() -> dict[str, list[str]]`
- `phone_location_loader() -> tuple[dict, dict, dict]`
- `telecom_operator_loader() -> dict[str, str]`
- `char_radical_loader() -> dict[str, dict[str, str]]`
- `html_entities_dictionary_loader() -> dict[str, dict[str, str]]`
- `idf_loader() -> dict[str, float]`
- `word_distribution_loader() -> dict[str, dict[str, float | int]]`
- `char_distribution_loader() -> dict[str, dict[str, float | int]]`
- `sentiment_words_loader() -> dict[str, float]`
- `sentiment_expand_words_loader() -> dict[str, float]`
- `quantifiers_loader() -> dict[str, dict[str, float | int]]`
- `traditional_simplified_loader(file_name) -> dict[str, str]`

## LLM dataset loader
- `llm_test_dataset_loader(version='1.0'|'1.1', field=None) -> list[dict] | field slice`
- Sample item fields: `question_type`, `score` (1.1), `correct_answer`, `question`

## Notes
- Many loaders expose nested dictionaries with `_full_name`, `_alias`, or probability fields.
- The packaged loader data is part of the runtime skill contract; future agents should use the loaders rather than reading the source checkout.

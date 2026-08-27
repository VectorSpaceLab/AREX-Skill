# API Reference

## Purpose

Use this when you need exact component names, signatures, or extension attributes for scispaCy's text-processing pipeline.

## Verified signatures

| API | Verified signature | Notes |
| --- | --- | --- |
| `combined_rule_tokenizer` | `combined_rule_tokenizer(nlp: spacy.language.Language) -> spacy.tokenizer.Tokenizer` | Returns a tokenizer with scispaCy punctuation, hyphen, and abbreviation exceptions |
| `combined_rule_prefixes` | `combined_rule_prefixes() -> List[str]` | Helper for prefix regex construction |
| `remove_new_lines` | `remove_new_lines(text: str) -> str` | Preprocesses hyphenated line breaks before tokenization |
| `pysbd_sentencizer` | `pysbd_sentencizer(doc: spacy.tokens.Doc) -> spacy.tokens.Doc` | `@Language.component("pysbd_sentencizer")` |
| `WhitespaceTokenizer` | `WhitespaceTokenizer(vocab)` | spaCy tokenizer replacement for pretokenized text |
| `create_combined_rule_model` | `create_combined_rule_model() -> spacy.language.Language` | Loads `en_core_web_sm`, replaces tokenizer, and adds `pysbd_sentencizer` |
| `AbbreviationDetector` | `AbbreviationDetector(nlp, name='abbreviation_detector', make_serializable=False)` | `@Language.factory("abbreviation_detector")` |
| `find_abbreviation` | `find_abbreviation(long_form_candidate, short_form_candidate) -> Tuple[Span, Optional[Span]]` | Schwartz & Hearst matching helper |
| `filter_matches` | `filter_matches(matcher_output, doc) -> List[Tuple[Span, Span]]` | Filters parenthesis matches into long/short candidates |
| `short_form_filter` | `short_form_filter(span) -> bool` | Rejects too-short, non-alpha, or mostly-nonalpha abbreviations |
| `HyponymDetector` | `HyponymDetector(nlp, name='hyponym_detector', extended=False)` | `@Language.factory("hyponym_detector")` |

## Extension attributes

| Extension | Owner | Shape |
| --- | --- | --- |
| `Doc._.abbreviations` | `AbbreviationDetector` | `List[Span]` by default; serializable dicts when `make_serializable=True` |
| `Span._.long_form` | `AbbreviationDetector` | `Span` for the detected expansion, or `None` |
| `Doc._.hearst_patterns` | `HyponymDetector` | `List[Tuple[str, Span, Span]]` |

## Serializable abbreviation payload

When `make_serializable=True`, the detector converts each abbreviation to a dict with these keys:

- `short_text`
- `short_start`
- `short_end`
- `long_text`
- `long_start`
- `long_end`

This is the mode to use if the document must survive `doc.to_bytes()` or multiprocessing.

## Common component ordering

1. Load a spaCy model.
2. Import `scispacy.abbreviation` and/or `scispacy.hyponym_detector` so the factories register.
3. Replace the tokenizer or add `pysbd_sentencizer` before downstream pipes.
4. Add `abbreviation_detector` before `scispacy_linker` when abbreviation resolution is needed.

## Notes from the source and tests

- `pysbd_sentencizer` is the current exported sentence-segmentation component; do not look for a `combined_rule_sentence_segmenter` symbol.
- `HyponymDetector` can run with `extended=True` to enable the larger Hearst-pattern set.
- The abbreviation detector test suite covers tricky parentheses, spacing, and serialization cases; use those tests as the behavioral reference for edge cases.

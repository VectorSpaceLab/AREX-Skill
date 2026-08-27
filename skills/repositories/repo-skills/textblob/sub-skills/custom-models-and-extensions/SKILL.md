---
name: custom-models-and-extensions
description: "Build TextBlob-compatible custom models, Blobber shared factories,
  extensions, and classifier format handoffs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Custom Models and Extensions

Use this sub-skill when a task needs a custom or third-party TextBlob model object: tokenizer, POS tagger, noun phrase extractor, sentiment analyzer, parser, classifier adapter, language package, or extension package.

## Route first

Stay here for:

- Implementing objects that satisfy `textblob.base` interfaces.
- Passing custom model instances to `TextBlob(...)` or `Blobber(...)`.
- Reusing a custom tokenizer/analyzer/tagger across many blobs with `Blobber`.
- Packaging model or language extensions with TextBlob naming conventions.
- Understanding the classifier/data-format registration hook before routing to classifier details.

Route away when the user wants:

- Built-in tokenization, tags, noun phrases, sentiment, parsing, or ordinary `TextBlob` workflows: `../core-nlp-workflows/SKILL.md`.
- Classifier training, evaluation, updating, feature extractors, CSV/JSON/TSV/custom training formats: `../classifiers-and-data-formats/SKILL.md`.
- `Word`, `WordList`, spelling, morphology, stemming, lemmatization, or WordNet: `../word-and-lexical-tools/SKILL.md`.

## Operating workflow

1. **Pick the insertion point.** `TextBlob` and `Blobber` accept `tokenizer`, `pos_tagger`, `np_extractor`, `analyzer`, `parser`, and `classifier`. Constructor signatures are compatible with `TextBlob(text, tokenizer=None, pos_tagger=None, np_extractor=None, analyzer=None, parser=None, classifier=None, clean_html=False)` and `Blobber(tokenizer=None, pos_tagger=None, np_extractor=None, analyzer=None, parser=None, classifier=None)`.
2. **Implement the correct interface.** Use [references/custom-models.md](references/custom-models.md) for the exact base methods: `BaseTokenizer.tokenize`/`itokenize`, `BaseTagger.tag`, `BaseNPExtractor.extract`, `BaseSentimentAnalyzer.analyze`/`train`, and `BaseParser.parse`.
3. **Validate with TextBlob before broader use.** Wrong model types raise `ValueError`; NLTK tokenizer instances are accepted for `tokenizer`; `classifier` is not base-class validated but must provide the methods the workflow calls.
4. **Use `Blobber` for shared models.** Prefer `Blobber(tokenizer=..., analyzer=..., pos_tagger=...)` when many texts should use the same trained or configured model instances. Each blob made by the factory receives the same model objects.
5. **Package reusable extensions deliberately.** Use [references/extensions.md](references/extensions.md) for package/import naming (`textblob-name` -> `textblob_name`, language packages `textblob-xx`).
6. **Run the bundled smoke check.** `python scripts/custom_model_smoke.py --json` verifies tiny custom models, `TextBlob`/`Blobber` acceptance, shared model identity, and invalid tagger rejection without writing files or downloading corpora.

## Fast troubleshooting in the workflow

- `ValueError: pos_tagger must be an instance of BaseTagger` means TextBlob requires inheritance, not only a `tag` method. Recover by subclassing `BaseTagger`; see the minimal adapter in [references/troubleshooting.md](references/troubleshooting.md).
- If a custom tokenizer works with `.tokens` but punctuation appears unexpectedly in `.words`, remember that punctuation filtering is special to TextBlob's default word tokenizer. Custom tokenizers own their output.
- If a custom analyzer seems ignored by `.polarity` or `.subjectivity`, check `.sentiment`; TextBlob's convenience `.polarity` and `.subjectivity` use the built-in pattern analyzer.
- If `TextBlob(...).tags` fails before your tagger runs, the default sentence segmentation path may need NLTK sentence data. For a no-corpus custom tagger smoke, exercise `Sentence(...).tags` or run the root setup check.
- If an extension cannot be imported, verify the hyphen/underscore naming rule: install/distribution name uses `textblob-name`, Python import uses `textblob_name`.

## Bundled references and script

- [references/custom-models.md](references/custom-models.md): interface contracts, constructor validation, Blobber sharing, and minimal model examples.
- [references/extensions.md](references/extensions.md): extension and language package naming, packaging skeleton, and registration guidance.
- [references/troubleshooting.md](references/troubleshooting.md): recovery recipes for invalid model types, analyzer/parser/tokenizer pitfalls, state sharing, corpora, and registry issues.
- [scripts/custom_model_smoke.py](scripts/custom_model_smoke.py): deterministic smoke test for custom model integration.

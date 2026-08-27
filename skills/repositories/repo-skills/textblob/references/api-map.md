# TextBlob API map

Use this map to route a TextBlob task to the right sub-skill and public module.

## Package-level imports

```python
from textblob import TextBlob, Word, WordList, Sentence, Blobber
```

These names are the most common entry points. Deeper modules expose model
classes, classifiers, formats, exceptions, and WordNet helpers.

## Route by module or object

| Module/object | Main capability | Skill location |
| --- | --- | --- |
| `textblob.TextBlob`, `textblob.blob.TextBlob` | document-level NLP wrapper | `sub-skills/core-nlp-workflows/` |
| `textblob.Sentence` | sentence object with shared models and indices | `sub-skills/core-nlp-workflows/` |
| `textblob.Blobber` | factory for blobs sharing model objects | core workflows for built-ins; custom-model sub-skill when implementing models |
| `textblob.Word`, `textblob.WordList` | word-level morphology, spelling, lemmatization, WordNet, list transforms | `sub-skills/word-and-lexical-tools/` |
| `textblob.tokenizers.WordTokenizer`, `SentenceTokenizer`, `word_tokenize`, `sent_tokenize` | tokenization and sentence splitting | `sub-skills/core-nlp-workflows/` |
| `textblob.taggers.NLTKTagger`, `PatternTagger` | POS tagging | `sub-skills/core-nlp-workflows/` |
| `textblob.np_extractors.FastNPExtractor`, `ConllExtractor` | noun phrase extraction | `sub-skills/core-nlp-workflows/` |
| `textblob.sentiments.PatternAnalyzer`, `NaiveBayesAnalyzer` | continuous and discrete sentiment analyzers | `sub-skills/core-nlp-workflows/` |
| `textblob.parsers.PatternParser` | pattern-style parse string | `sub-skills/core-nlp-workflows/` |
| `textblob.classifiers.*Classifier` | text classifiers and feature extraction | `sub-skills/classifiers-and-data-formats/` |
| `textblob.formats` | CSV/JSON/TSV/custom classifier data formats | `sub-skills/classifiers-and-data-formats/` |
| `textblob.wordnet` | WordNet constants, Synset, Lemma | `sub-skills/word-and-lexical-tools/` |
| `textblob.base` | base interfaces for custom tokenizers/taggers/extractors/analyzers/parsers | `sub-skills/custom-models-and-extensions/` |
| `textblob.exceptions.MissingCorpusError` | setup/corpus failure wrapper | root troubleshooting plus workflow-specific troubleshooting |
| `textblob.exceptions.FormatError` | classifier data format detection failure | `sub-skills/classifiers-and-data-formats/` |

## Frequent task routes

- "Extract noun phrases and sentiment from reviews" -> core NLP workflows.
- "Why is `Word('went').lemmatize()` not `go`?" -> word and lexical tools.
- "Train a Naive Bayes classifier from JSON" -> classifiers and data formats.
- "Register a pipe-delimited training format" -> classifiers and data formats,
  with optional custom-model cross-link for reusable packaging.
- "Use a custom tokenizer/tagger/analyzer" -> custom models and extensions.
- "Create a French TextBlob extension" -> custom models and extensions.
- "Missing corpus error" -> root corpora/setup, then the sub-skill owning the
  API that failed.

## Verified public signatures

These signatures were verified from an installed TextBlob 0.20.1 package:

```text
TextBlob(text, tokenizer=None, pos_tagger=None, np_extractor=None, analyzer=None, parser=None, classifier=None, clean_html=False)
Blobber(tokenizer=None, pos_tagger=None, np_extractor=None, analyzer=None, parser=None, classifier=None)
Word(string, pos_tag=None)
WordTokenizer.tokenize(self, text, include_punc=True)
SentenceTokenizer.tokenize(self, text)
NaiveBayesClassifier(train_set, feature_extractor=basic_extractor, format=None, **kwargs)
DecisionTreeClassifier(train_set, feature_extractor=basic_extractor, format=None, **kwargs)
MaxEntClassifier(train_set, feature_extractor=basic_extractor, format=None, **kwargs)
PositiveNaiveBayesClassifier(positive_set, unlabeled_set, feature_extractor=contains_extractor, positive_prob_prior=0.5, **kwargs)
PatternAnalyzer.analyze(self, text, keep_assessments=False)
NaiveBayesAnalyzer(feature_extractor=_default_feature_extractor)
ConllExtractor(parser=None)
PatternTagger.tag(self, text, tokenize=True)
NLTKTagger.tag(self, text)
```

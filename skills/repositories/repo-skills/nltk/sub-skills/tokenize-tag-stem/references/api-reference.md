# API Reference: NLTK Tokenize, Tag, Stem, Lemmatize, Sentiment

This reference distills NLTK 3.10.x public contracts for preprocessing workflows. It is self-contained and does not require the original source checkout at runtime.

## Tokenization APIs

### Sentence and word tokenization

Installed signature evidence:

```python
nltk.sent_tokenize(text, language="english")
nltk.word_tokenize(text, language="english", preserve_line=False)
```

Behavior:

- `sent_tokenize` uses `PunktTokenizer(language)` and requires the data resource `tokenizers/punkt_tab/<language>/`.
- `word_tokenize(..., preserve_line=False)` first sentence-tokenizes, so it also requires `punkt_tab` for the language.
- `word_tokenize(..., preserve_line=True)` skips sentence splitting and uses the improved Treebank word tokenizer directly; this is useful for no-download line-by-line workflows.
- `language` is the Punkt language directory name, e.g. `english` or `german`, not a two-letter ISO code.

Example:

```python
from nltk.tokenize import word_tokenize

print(word_tokenize("Hello, world!", preserve_line=True))
# ['Hello', ',', 'world', '!']
```

### Tokenizer classes

| API | Contract | Use when |
| --- | --- | --- |
| `TreebankWordTokenizer().tokenize(text, convert_parentheses=False, return_str=False)` | Penn Treebank-style tokenization with contractions, punctuation, quotes, and optional parenthesis conversion. | You need deterministic word tokenization without sentence splitting. |
| `TreebankWordDetokenizer().detokenize(tokens)` | Reconstructs readable text from Treebank-style tokens. | You need to round-trip or display tokenized output. |
| `WordPunctTokenizer().tokenize(text)` / `wordpunct_tokenize(text)` | Splits on punctuation and word-character spans. | You want simple regex splitting and no data packages. |
| `RegexpTokenizer(pattern, gaps=False, discard_empty=True, flags=re.UNICODE | re.MULTILINE | re.DOTALL)` | Uses a regex to select tokens or gaps. | You need a custom token definition. Avoid capturing groups unless you intentionally want group text. |
| `WhitespaceTokenizer`, `SpaceTokenizer`, `TabTokenizer`, `LineTokenizer` | Split on whitespace, spaces, tabs, or lines. | You need transparent layout-sensitive tokenization. |
| `TweetTokenizer(preserve_case=True, reduce_len=False, strip_handles=False, match_phone_numbers=True)` | Social-media tokenizer with handles, emoticons, URLs, repeated characters, phone-number behavior. | Tweets, chats, or informal text. |
| `MWETokenizer(mwes=None, separator="_")` | Merges multi-word expressions such as `("New", "York")`. | You need phrase tokens after word tokenization. |
| `SExprTokenizer`, `sexpr_tokenize` | Tokenizes Lisp/S-expression syntax. | Logic or tree-like S-expression inputs. |

Span tokenization:

```python
from nltk.tokenize import WhitespaceTokenizer
spans = list(WhitespaceTokenizer().span_tokenize("Good muffins"))
# [(0, 4), (5, 12)]
```

Span methods return string-slice offsets, which are safer than recomputing positions after normalization.

## `nltk tokenize` CLI

The installed console entry point is `nltk=nltk.cli:cli`. The `tokenize` command reads stdin and writes tokenized lines to stdout.

```bash
printf 'Hello, world!\n' | nltk tokenize --preserve-line --delimiter '|'
```

Relevant flags:

| Flag | Meaning |
| --- | --- |
| `-l`, `--language TEXT` | Punkt language used when sentence tokenization is enabled. Default `en` in CLI source, but Punkt resources are language-directory names; use `english` for standard English Punkt data. |
| `-p`, `--preserve-line` | Keep each input line as one sentence and skip Punkt sentence splitting. This avoids `punkt_tab` for simple line tokenization. |
| `-j`, `--processes INTEGER` | Parallelize line preprocessing with joblib when greater than 1. |
| `-e`, `--encoding TEXT` | Stdin/stdout encoding, default `utf8`. |
| `-d`, `--delimiter TEXT` | String used to join output tokens, default space. |

The repository has a regression test that `-p` is the short flag for `--preserve-line`; do not document `-l` for preserve-line.

## POS tagging APIs

Installed signature evidence:

```python
nltk.tag.pos_tag(tokens, tagset=None, lang="eng")
nltk.tag.pos_tag_sents(sentences, tagset=None, lang="eng")
```

Contracts:

- `tokens` must be a list of strings. Passing a raw string raises `TypeError` through the internal tagger path.
- `sentences` is a list of token lists for efficient batch tagging.
- `lang` supports `"eng"` and `"rus"`; other values raise `NotImplementedError`.
- English uses `taggers/averaged_perceptron_tagger_eng/`; Russian uses `taggers/averaged_perceptron_tagger_rus/`.
- `tagset="universal"` maps language-specific tags to universal tags and may require the `universal_tagset` data package.

Example:

```python
from nltk import pos_tag
print(pos_tag(["John", "saw", "Mary", "."]))
```

### Tagger classes

| API | Contract | Notes |
| --- | --- | --- |
| `RegexpTagger(regexps, backoff=None)` | `regexps` is `[(pattern, tag), ...]`; first matching pattern wins. | Good no-data baseline and backoff. |
| `DefaultTagger(tag)` | Tags every token with the same tag. | Simple baseline/backoff. |
| `UnigramTagger(train=None, model=None, backoff=None, cutoff=0, verbose=False)` | Learns most likely tag per token from tagged sentences, or uses an explicit model. | Unknown tokens return `None` unless a backoff is provided. |
| `BigramTagger`, `TrigramTagger`, `NgramTagger` | Contextual n-gram taggers trained on tagged sentences. | Use with lower-order backoff to avoid many `None` tags. |
| `AffixTagger`, `ClassifierBasedPOSTagger`, `BrillTaggerTrainer`, `HiddenMarkovModelTrainer`, `PerceptronTagger`, `CRFTagger` | More specialized/trainable taggers. | CRF requires `python-crfsuite`; some models/data may be optional. |

Useful methods:

- `tagger.tag(tokens)` -> list of `(token, tag)`.
- `tagger.tag_sents(sentences)` -> batch tagging.
- `tagger.accuracy(gold_tagged_sents)` -> token accuracy.
- Some taggers expose `evaluate_per_tag` and `confusion` for detailed evaluation.
- `untag(tagged_sentence)` removes tags; `tuple2str` and `str2tuple` convert tagged-token representations.

## Stemming and lemmatization

Installed signatures:

```python
PorterStemmer(mode="NLTK_EXTENSIONS")
PorterStemmer().stem(word, to_lowercase=True)
SnowballStemmer(language, ignore_stopwords=False)
WordNetLemmatizer().lemmatize(word, pos="n")
```

| API | Use | Data requirement |
| --- | --- | --- |
| `PorterStemmer` | English stemming; modes include `NLTK_EXTENSIONS`, `MARTIN_EXTENSIONS`, and `ORIGINAL_ALGORITHM`. | None. |
| `SnowballStemmer` | Multilingual stemming; `SnowballStemmer.languages` lists supported languages. | Some languages with `ignore_stopwords=True` may need stopword data; core stemming rules are bundled in code. |
| `LancasterStemmer`, `RegexpStemmer`, `ISRIStemmer`, `ARLSTem`, `Cistem`, `RSLPStemmer` | Algorithm/language-specific stemming. | Usually none unless a specific algorithm says otherwise. |
| `WordNetLemmatizer` | Lemmatization via WordNet morphology. | `wordnet`; use `omw-2.0` for multilingual WordNet workflows. |

Example:

```python
from nltk.stem import PorterStemmer, SnowballStemmer, WordNetLemmatizer
print(PorterStemmer().stem("running"))
print(SnowballStemmer("german").stem("Schränke"))
print(WordNetLemmatizer().lemmatize("dogs", pos="n"))
```

## Sentiment preprocessing

| API | Contract | Data requirement |
| --- | --- | --- |
| `SentimentIntensityAnalyzer(lexicon_file="sentiment/vader_lexicon.zip/vader_lexicon/vader_lexicon.txt")` | VADER rule/lexicon sentiment scorer. `polarity_scores(text)` returns `neg`, `neu`, `pos`, and `compound`. | `vader_lexicon`. |
| `SentimentAnalyzer` | Feature-extraction helper for training/evaluating classifiers. | Depends on the corpora/features you choose. |
| `nltk.sentiment.util.mark_negation`, `extract_unigram_feats`, `demo_*` helpers | Feature engineering for sentiment classifiers. | Corpus examples may require `subjectivity`, `movie_reviews`, or other data. |

VADER example after `vader_lexicon` is installed:

```python
from nltk.sentiment import SentimentIntensityAnalyzer
sid = SentimentIntensityAnalyzer()
print(sid.polarity_scores("VADER is smart, handsome, and funny!"))
```

## Data package map for this sub-skill

| API/workflow | Targeted package(s) to check/download |
| --- | --- |
| `sent_tokenize`, `word_tokenize` with sentence splitting | `punkt_tab` |
| `pos_tag(..., lang="eng")` | `averaged_perceptron_tagger_eng` |
| `pos_tag(..., lang="rus")` | `averaged_perceptron_tagger_rus` |
| `tagset="universal"` | `universal_tagset` |
| `WordNetLemmatizer`, WordNet synonyms in adjacent metrics | `wordnet`, optionally `omw-2.0` |
| `SentimentIntensityAnalyzer` | `vader_lexicon` |
| Tagger training/evaluation examples from Brown/Treebank | `brown`, `treebank`, and `universal_tagset` if universal tags are requested |

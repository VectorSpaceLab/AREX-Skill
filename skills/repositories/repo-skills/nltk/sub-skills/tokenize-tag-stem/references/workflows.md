# Workflows: NLTK Tokenize, Tag, Stem, Lemmatize, Sentiment

These recipes are designed for future agents operating from an installed NLTK package. They avoid downloads unless a step explicitly says to check or install a data package.

## 1. Choose a tokenizer

Start by deciding whether sentence boundaries, social text, regex rules, or exact spans matter.

| Need | Recommended API | Data requirement |
| --- | --- | --- |
| Simple no-download word/punctuation split | `word_tokenize(text, preserve_line=True)`, `TreebankWordTokenizer`, or `WordPunctTokenizer` | none for `preserve_line=True`/classes shown |
| Sentence splitting plus words | `sent_tokenize`, `word_tokenize(..., preserve_line=False)` | `punkt_tab` for the language |
| Tweet/social media tokens | `TweetTokenizer` | none |
| Custom regex tokens | `RegexpTokenizer` | none |
| Token positions in original string | `span_tokenize` methods | none |
| Merge multiword expressions | `MWETokenizer` after initial word tokenization | none |

Example no-download splitter:

```python
from nltk.tokenize import TreebankWordTokenizer, WordPunctTokenizer

text = "Good muffins cost $3.88 in New York."
print(TreebankWordTokenizer().tokenize(text))
print(WordPunctTokenizer().tokenize(text))
```

Example Punkt-backed splitter after `punkt_tab` is available:

```python
from nltk import sent_tokenize, word_tokenize

text = "I called Dr. Jones. I called again."
print(sent_tokenize(text, language="english"))
print(word_tokenize(text, language="english", preserve_line=False))
```

If `word_tokenize` fails with a Punkt `LookupError`, either download `punkt_tab` or set `preserve_line=True` when line-level tokenization is acceptable.

## 2. Run the `nltk tokenize` CLI safely

Use the CLI for stream tokenization in shell pipelines.

```bash
printf 'Hello, world!\n' | nltk tokenize --preserve-line --delimiter '|'
```

Guidelines:

- Use `--preserve-line` for no-download line tokenization.
- Use `--language english` when sentence tokenization is enabled and `punkt_tab` is installed.
- Use `--processes 1` for tiny inputs; parallelism only helps for many lines.
- Use `--encoding utf8` unless the input stream has a known different encoding.
- Use the bundled `scripts/tokenize_cli_smoke.py --json` to verify the CLI entry point before embedding it in a pipeline.

## 3. Tokenize tweets or chat text

```python
from nltk.tokenize import TweetTokenizer

tok = TweetTokenizer(strip_handles=True, reduce_len=True, preserve_case=False)
print(tok.tokenize("@myke SOOO coool!!! Call 601-984-4813 :)"))
```

Decision points:

- `strip_handles=True` removes usernames but can leave punctuation such as a leading colon depending on the text.
- `reduce_len=True` reduces repeated character sequences such as `waaaaayyyy` while preserving emphasis.
- `preserve_case=False` lowercases most tokens.
- `match_phone_numbers=False` can prevent phone-number regex behavior from splitting long product IDs incorrectly; test both modes when phone-like numbers are present.

## 4. Use spans and detokenization

When a downstream tool needs offsets, prefer span tokenization instead of searching tokens after the fact.

```python
from nltk.tokenize import WhitespaceTokenizer

text = "Good muffins"
spans = list(WhitespaceTokenizer().span_tokenize(text))
print(spans)
print([text[start:end] for start, end in spans])
```

When converting Treebank tokens back to text:

```python
from nltk.tokenize import TreebankWordTokenizer, TreebankWordDetokenizer

text = "Don't split quotes incorrectly."
tokens = TreebankWordTokenizer().tokenize(text)
print(TreebankWordDetokenizer().detokenize(tokens))
```

Detokenization is not a guarantee of byte-for-byte round-trip for every tokenizer; use spans when exact source recovery matters.

## 5. POS tag one sentence or many sentences

After targeted data packages are installed:

```python
from nltk import pos_tag

sentence = ["John", "saw", "Mary", "."]
print(pos_tag(sentence, lang="eng"))
print(pos_tag(sentence, tagset="universal", lang="eng"))
```

Batch tagging:

```python
from nltk.tag import pos_tag_sents
sents = [["John", "runs", "."], ["Mary", "walks", "."]]
print(pos_tag_sents(sents, lang="eng"))
```

Validation checklist:

1. `tokens` is a `list[str]`; do not pass a raw string.
2. `lang` is `"eng"` or `"rus"`.
3. English resource: `taggers/averaged_perceptron_tagger_eng/`.
4. Russian resource: `taggers/averaged_perceptron_tagger_rus/`.
5. Universal tagset resource: `taggers/universal_tagset/`.

## 6. Train a tiny backoff tagger

Use a no-data `RegexpTagger` as a backoff, then train a unigram tagger over gold tagged sentences when available.

```python
from nltk.tag import RegexpTagger, UnigramTagger

backoff = RegexpTagger([
    (r"^-?[0-9]+(\.[0-9]+)?$", "CD"),
    (r".*ing$", "VBG"),
    (r".*ed$", "VBD"),
    (r".*s$", "NNS"),
    (r".*", "NN"),
])
train = [[("the", "DT"), ("dog", "NN"), ("runs", "VBZ")]]
tagger = UnigramTagger(train, backoff=backoff)
print(tagger.tag(["cats", "jumped", "42"]))
```

With a corpus such as Treebank or Brown installed, split train/test before reporting accuracy:

```python
from nltk.corpus import treebank
from nltk.tag import untag

train_sents = treebank.tagged_sents()[:100]
test_sents = treebank.tagged_sents()[100:120]
tagger = UnigramTagger(train_sents, backoff=backoff)
print(tagger.accuracy(test_sents))
print(tagger.tag(untag(test_sents[0])))
```

## 7. Stem or lemmatize words

Stemming is rule-based and usually no-download:

```python
from nltk.stem import PorterStemmer, SnowballStemmer

print(PorterStemmer().stem("running"))
print(PorterStemmer(mode=PorterStemmer.ORIGINAL_ALGORITHM).stem("running"))
print(SnowballStemmer("german", ignore_stopwords=False).stem("Schränke"))
```

Lemmatization uses WordNet:

```python
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()
print(lemmatizer.lemmatize("dogs", pos="n"))
print(lemmatizer.lemmatize("running", pos="v"))
```

If WordNet is missing, install/check `wordnet`; add `omw-2.0` for multilingual WordNet data. Always pass `pos` when the default noun assumption would be wrong.

## 8. Use VADER or sentiment feature extraction

VADER after `vader_lexicon` is available:

```python
from nltk.sentiment import SentimentIntensityAnalyzer
sid = SentimentIntensityAnalyzer()
print(sid.polarity_scores("The script is not fantastic, but the acting is EXCELLENT!"))
```

Interpretation:

- `compound` is a normalized overall score in `[-1, 1]`.
- `pos`, `neu`, and `neg` are proportions and usually sum to about 1.
- VADER handles capitalization, punctuation, booster words, negation, emoticons, slang, and contrastive conjunctions.

For trainable sentiment workflows, use `SentimentAnalyzer` to build feature sets, then route the classifier training/evaluation to `ml-metrics-and-translation`.

```python
from nltk.sentiment import SentimentAnalyzer
from nltk.sentiment.util import mark_negation, extract_unigram_feats

training_docs = [(["good", "movie"], "pos"), (["not", "good"], "neg")]
analyzer = SentimentAnalyzer()
all_words = analyzer.all_words([mark_negation(doc) for doc, label in training_docs])
unigrams = analyzer.unigram_word_feats(all_words, min_freq=1)
analyzer.add_feat_extractor(extract_unigram_feats, unigrams=unigrams)
features = analyzer.apply_features(training_docs)
```

## 9. Smoke-check preprocessing APIs

Run from any working directory in an environment with NLTK installed:

```bash
python /path/to/skills/disco/nltk/sub-skills/tokenize-tag-stem/scripts/text_preprocess_smoke.py --json
python /path/to/skills/disco/nltk/sub-skills/tokenize-tag-stem/scripts/tokenize_cli_smoke.py --json
```

Expected signal: exit code `0` and deterministic tokenizer/stemmer/CLI summaries. The scripts do not download data by default; optional data-backed checks are reported as present/missing rather than forced.

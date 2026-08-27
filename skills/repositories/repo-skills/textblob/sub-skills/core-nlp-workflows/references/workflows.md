# TextBlob core NLP workflows

Use this reference for installed TextBlob document and sentence workflows. It
keeps practical recipes close to the APIs they need and assumes TextBlob is
installed in the target Python environment.

## Setup-sensitive workflow map

| Task | Main API | Corpus/data needs | Output shape |
| --- | --- | --- | --- |
| Basic sentiment | `TextBlob(text).sentiment` | packaged English sentiment resources | `Sentiment(polarity, subjectivity)` |
| Sentence splitting | `blob.sentences` | NLTK `punkt_tab` | list of `Sentence` objects |
| Word tokens without punctuation | `blob.words` | NLTK `punkt_tab` for default sentence-first tokenization | `WordList` |
| Raw tokenizer output | `blob.tokens` | tokenizer-dependent | `WordList` |
| POS tags | `blob.tags` / `.pos_tags` | `punkt_tab`, `averaged_perceptron_tagger_eng`; numpy for the NLTKTagger test surface | list of `(Word, tag)` tuples |
| Noun phrases | `blob.noun_phrases` | default `FastNPExtractor` needs `brown`; `ConllExtractor` needs `conll2000` | lowercase `WordList` |
| Parsing | `blob.parse()` | packaged pattern-style parser resources | slash-delimited parse string |
| Discrete sentiment | `TextBlob(text, analyzer=NaiveBayesAnalyzer()).sentiment` | `movie_reviews` plus tokenizers | `Sentiment(classification, p_pos, p_neg)` |

For setup details and exact corpus names, read the parent skill's
`references/corpora-and-setup.md` and run the root `scripts/check_textblob_setup.py`.

## Basic document analysis

```python
from textblob import TextBlob

text = "TextBlob is amazingly simple to use. What great fun!"
blob = TextBlob(text)

sentences = [str(sentence) for sentence in blob.sentences]
words = [str(word) for word in blob.words]
tokens = [str(token) for token in blob.tokens]
tags = [(str(word), tag) for word, tag in blob.tags]
noun_phrases = [str(phrase) for phrase in blob.noun_phrases]
sentiment = blob.sentiment
```

Validation checklist:

- `sentiment.polarity` is in `[-1.0, 1.0]` and `sentiment.subjectivity` is in
  `[0.0, 1.0]` for the default analyzer.
- `.sentences` returns `Sentence` objects; use `str(sentence)` for plain text.
- `.words` excludes punctuation under the default `WordTokenizer`; use
  `.tokens` when punctuation is part of the task.
- `.tags` aliases `.pos_tags`.
- `.noun_phrases` normalizes phrases to lowercase.

## Sentence-level processing

Sentence objects share the parent blob's models and expose the same base
properties as a blob.

```python
from textblob import TextBlob

blob = TextBlob("The beer is good. But the hangover is horrible.")
for sentence in blob.sentences:
    print(sentence.raw, sentence.start_index, sentence.end_index)
    print(sentence.sentiment.polarity)
    print(sentence.words)
```

`Sentence.dict` is useful when creating JSON-like output for each sentence:

```python
records = [sentence.dict for sentence in blob.sentences]
json_text = blob.to_json(indent=2)
```

`Sentence.dict` includes raw text, start/end indices, stripped text, noun
phrases, polarity, and subjectivity.

## Words, tokens, and custom tokenizers

Default word behavior:

```python
from textblob import TextBlob

blob = TextBlob("Can't stop, won't stop.")
blob.tokens  # includes punctuation tokens from WordTokenizer
blob.words   # strips punctuation while preserving contraction fragments
```

Custom tokenizer behavior is different: `.words` uses the custom tokenizer
output directly instead of applying the default punctuation stripping path.

```python
from nltk.tokenize import TabTokenizer
from textblob import TextBlob

blob = TextBlob("left\tright\tend.", tokenizer=TabTokenizer())
assert [str(t) for t in blob.tokens] == ["left", "right", "end."]
assert [str(w) for w in blob.words] == ["left", "right", "end."]
```

When a task says "do not lose punctuation" or "split on tabs/pipes", use
`.tokens` and document the tokenizer contract. When it says "word counts" or
"ignore punctuation", use `.words` with the default tokenizer or explicitly
filter a custom tokenizer's output.

## Tags and noun phrases

```python
from textblob import TextBlob
from textblob.np_extractors import ConllExtractor
from textblob.taggers import PatternTagger

blob = TextBlob("Python is a high-level programming language.")
[(str(word), tag) for word, tag in blob.tags]
[str(phrase) for phrase in blob.noun_phrases]

# Optional model override for noun phrases.
blob2 = TextBlob("Python is a high-level programming language.", np_extractor=ConllExtractor())
blob2.noun_phrases

# PatternTagger can be supplied when that tagger behavior is desired.
TextBlob("Simple is better than complex.", pos_tagger=PatternTagger()).tags
```

Use `ConllExtractor` only when the CoNLL-trained NP behavior is required and
the `conll2000` corpus is available. The default `FastNPExtractor` trains from
Brown corpus data.

## Sentiment workflows

Default continuous sentiment:

```python
from textblob import TextBlob

blob = TextBlob("TextBlob is amazingly simple to use. What great fun!")
score = blob.sentiment
score.polarity       # e.g. positive float
score.subjectivity   # e.g. subjective float
```

Assessment details:

```python
blob.sentiment_assessments.assessments
```

Discrete Naive Bayes sentiment:

```python
from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer

blob = TextBlob("I love this library", analyzer=NaiveBayesAnalyzer())
result = blob.sentiment
result.classification  # 'pos' or 'neg'
result.p_pos
result.p_neg
```

Important distinction: `.sentiment` reads the blob's analyzer, while `.polarity`
and `.subjectivity` use the built-in pattern analyzer convenience path. For a
custom analyzer or `NaiveBayesAnalyzer`, read `.sentiment`.

## Parsing and n-grams

```python
from textblob import TextBlob

blob = TextBlob("And now for something completely different.")
print(blob.parse())

bigrams = [[str(word) for word in gram] for gram in blob.ngrams(2)]
trigrams = blob.ngrams()  # default n=3
empty = blob.ngrams(0)    # []
```

The parser returns a slash-delimited pattern-style parse string. Treat it as a
format-specific string rather than a Python parse tree.

## Counts and serialization

```python
from textblob import TextBlob

blob = TextBlob("We are now the Knights who say Ekki ekki ekki PTANG.")
blob.word_counts["ekki"]   # lower-stripped count
blob.words.count("ekki")   # WordList count; case-insensitive by default
blob.np_counts             # noun phrase counts after extraction
blob.json                  # JSON string for sentence dictionaries
```

For POS-aware lemmatization, stemming, spelling correction, or WordNet lookup on
individual tokens, route the resulting words to `../word-and-lexical-tools/SKILL.md`.

## Blobber shared factory

Use `Blobber` when model objects should be reused across many texts:

```python
from textblob import Blobber
from textblob.taggers import NLTKTagger

tb = Blobber(pos_tagger=NLTKTagger())
blob1 = tb("This is a blob.")
blob2 = tb("This is another blob.")
assert blob1.pos_tagger is blob2.pos_tagger
```

If the task involves implementing those models, use the custom-model sub-skill.
If the task only needs consistent built-in model selection across many texts,
this core workflow is enough.

## Integrated difficult case pattern

For an end-to-end text-processing report:

1. Run or adapt the root setup check; confirm required corpora.
2. Build a `TextBlob` from raw text.
3. Extract sentence records: raw sentence, sentiment, tags, noun phrases.
4. Use `.words` or `.tokens` intentionally based on punctuation requirements.
5. Route selected `Word` objects to the lexical sub-skill for POS-aware
   lemmatization or spelling correction.
6. If classification is required, train the classifier separately with the
   classifier sub-skill, then pass it into `TextBlob(..., classifier=cl)` and
   classify each sentence.

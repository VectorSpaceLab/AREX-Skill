# TextBlob Word and WordList lexical reference

This reference covers installed `textblob` word-level APIs. Use the core NLP
sub-skill first when raw documents need tokenization, POS tags, noun phrases,
sentiment, or parsing.

## Imports and constructors

```python
from textblob import Word, WordList
from textblob.wordnet import NOUN, VERB, ADJ, ADV, Synset, Lemma
```

| API | Purpose | Notes |
| --- | --- | --- |
| `Word(string, pos_tag=None)` | `str` subclass with lexical helpers. | Stores `.string` and optional `.pos_tag`; normal string operations still work. |
| `WordList(collection)` | List-like collection whose string elements are converted to `Word`. | Preserves non-string elements appended later. |
| `textblob.wordnet.NOUN`, `VERB`, `ADJ`, `ADV` | WordNet POS constants. | Values are NLTK WordNet POS codes. |
| `textblob.wordnet.Synset(name)`, `Lemma(name)` | Direct WordNet object constructors. | Require WordNet corpus data. |

`Word` is string-like:

```python
w = Word("cat", pos_tag="NN")
assert w == "cat"
assert w.upper() == "CAT"
assert w.pos_tag == "NN"
```

## Morphology and inflection

Use inflection for singular/plural word forms:

```python
Word("cats").singularize()      # Word('cat')
Word("cat").pluralize()         # Word('cats')
Word("wolves").singularize()    # Word('wolf')
```

`Word.singularize()` and `Word.pluralize()` return `Word` instances. Direct
function-level imports are available:

```python
from textblob.inflect import singularize, pluralize
```

TextBlob's English inflector includes irregulars, uninflected words, and
classical forms. Verify exact output for domain vocabulary.

## Lemmatization

Use lemmatization for dictionary forms grounded in WordNet. It requires NLTK
WordNet data.

```python
Word("cars").lemmatize()        # 'car'
Word("went").lemmatize()        # 'went' because default POS is noun
Word("went").lemmatize("v")    # 'go'
Word("went").lemmatize("VBD")  # 'go'
Word("went", "VBD").lemma      # 'go'
```

Details:

- `Word.lemmatize(pos=None)` defaults to WordNet noun POS.
- `pos` can be `NOUN`, `VERB`, `ADJ`, `ADV`, their string codes, or common Penn
  tags such as `NN`, `VBD`, `JJ`, and `RB`.
- `Word.lemma` is a cached property that calls `lemmatize(pos=self.pos_tag)`.

| Desired POS | WordNet constant/code | Common Penn tags |
| --- | --- | --- |
| Noun | `NOUN` / `'n'` | `NN`, `NNS`, `NNP`, `NNPS` |
| Verb | `VERB` / `'v'` | `VB`, `VBD`, `VBG`, `VBN`, `VBP`, `VBZ` |
| Adjective | `ADJ` / `'a'` | `JJ`, `JJR`, `JJS` |
| Adverb | `ADV` / `'r'` | `RB`, `RBR`, `RBS` |

## Stemming

Use stemming for corpus-free rough feature keys:

```python
Word("cars").stem()      # 'car'
Word("wolves").stem()    # often a non-word stem such as 'wolv'
```

`Word.stem(stemmer=Word.PorterStemmer)` uses NLTK's Porter stemmer by default.
You can pass compatible stemmer objects such as `Word.LancasterStemmer` or
`Word.SnowballStemmer`. Stemming returns strings; `WordList.stem()` returns a
new `WordList` of the stems.

## Spelling correction

```python
suggestions = Word("speling").spellcheck()
best = Word("speling").correct()
```

- `spellcheck()` returns `(candidate, confidence)` tuples ordered by confidence.
- `correct()` returns the top candidate as a `Word`.
- Punctuation, numbers, decimals, and common one-letter words often return
  unchanged with confidence `1.0`.
- TextBlob's public docs describe the correction model as roughly 70% accurate;
  confidence is a heuristic ranking signal.

For pipelines, keep audit fields:

```python
from textblob import Word
from textblob.wordnet import NOUN

def normalize_keyword(token, pos=NOUN, min_confidence=0.80):
    suggestion, confidence = Word(token).spellcheck()[0]
    chosen = suggestion if confidence >= min_confidence else token
    return {
        "original": token,
        "suggestion": suggestion,
        "confidence": confidence,
        "used_correction": chosen != token,
        "normalized": Word(chosen).lemmatize(pos),
    }
```

## WordNet synsets and definitions

```python
from textblob import Word
from textblob.wordnet import NOUN, VERB, Synset

word = Word("octopus")
word.synsets
word.get_synsets(pos=NOUN)
word.definitions
word.define(pos=NOUN)
Synset("octopus.n.02")
Word("hack").get_synsets(pos=VERB)
```

`Word.synsets` and `Word.definitions` are cached properties. Create a new
`Word` instance if corpus data changes within a long-running process.

## WordList behavior

`WordList` is a list subclass with extra lexical methods:

```python
wl = WordList(["Beautiful", "is", "better"])
wl[0]       # Word('Beautiful')
wl[:2]      # WordList(['Beautiful', 'is'])
repr(wl)    # "WordList(['Beautiful', 'is', 'better'])"
```

Mutation and conversion:

```python
wl = WordList(["dog"])
wl.append("cat")       # converts to Word('cat')
wl.append(("a", "tuple"))  # non-string preserved
wl.extend(["buffalo", 4])
wl[0] = "hound"        # string assigned by index converts to Word
plain = list(wl)
```

Batch methods return new `WordList` objects:

```python
WordList(["Dog", "CAT"]).lower()
WordList(["dogs", "men"]).singularize()
WordList(["dog", "cat"]).pluralize()
WordList(["cat", "dogs"]).lemmatize()
WordList(["cat", "dogs"]).stem()
```

`WordList.lemmatize()` does not accept per-word POS. For mixed POS batches:

```python
tagged = [("went", "VBD"), ("cars", "NNS")]
lemmas = [Word(token, pos).lemma for token, pos in tagged]
```

## Counts for words and noun phrases

If a `TextBlob` has already been produced:

```python
from textblob import TextBlob

monty = TextBlob("We are now the Knights who say Ekki ekki ekki PTANG.")
monty.word_counts["ekki"]
monty.words.count("ekki")
monty.words.count("ekki", case_sensitive=True)
monty.noun_phrases.count("python")
```

`word_counts` and `np_counts` are document-level properties; route extraction to
the core NLP sub-skill. This sub-skill owns the `WordList` transforms and
case-sensitive count behavior after extraction.

## Choosing the right normalization

| Goal | Prefer | Avoid |
| --- | --- | --- |
| Singular/plural display form | `singularize` / `pluralize` | Assuming every noun changes form. |
| Dictionary lemma | `lemmatize(pos=...)` or `Word(..., pos).lemma` | Omitting POS for verbs like `went`. |
| Coarse feature key without corpora | `stem()` | Expecting real words. |
| Typo repair | `spellcheck()` plus threshold/audit | Blind `.correct()` on domain terms. |
| Lexical semantics | `synsets`, `define`, `Synset` | Running without WordNet corpus. |

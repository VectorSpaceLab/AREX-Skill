# Stemming and multilingual stopwords

## Stopword inputs

The built-in stopword registry accepts these full names and short codes. The aliases select the same tuple; the lists are bundled with bm25s and do not require an NLTK corpus download.

| Language | Accepted names |
|---|---|
| English | `"english"`, `"en"`, `True` |
| English plus | `"english_plus"`, `"en_plus"` |
| German | `"german"`, `"de"` |
| Dutch | `"dutch"`, `"nl"` |
| French | `"french"`, `"fr"` |
| Spanish | `"spanish"`, `"es"` |
| Portuguese | `"portuguese"`, `"pt"` |
| Italian | `"italian"`, `"it"` |
| Russian | `"russian"`, `"ru"` |
| Swedish | `"swedish"`, `"sv"` |
| Norwegian | `"norwegian"`, `"no"` |
| Chinese | `"chinese"`, `"zh"` |
| Turkish | `"turkish"`, `"tr"` |
| Korean | `"korean"`, `"ko"` |

Use `None` or `False` to disable stopword removal, or pass a custom list/tuple such as `stopwords=["the", "is"]`. An unrecognized string raises `ValueError` with the supported-language guidance. Do not pass a language name in a different spelling and expect automatic lookup.

The text is lowercased before stopword matching when `lower=True` (the default). Custom entries are not lowercased for you, so use lowercase entries when lowercasing is enabled. Stopword matching happens before stemming. For a class tokenizer, a word already present in `word_to_id` is handled before the stopword check; do not mutate stopwords after vocab construction and expect old IDs to be retroactively removed.

## Module-function stemmer contract

`bm25s.tokenize(..., stemmer=...)` processes the unique surface tokens as a batch after splitting and stopword removal. The stemmer must be either:

1. an object exposing `stemWords(tokens)`, where `tokens` is `list[str]` and the return is a same-length list of strings; or
2. a callable receiving `list[str]` and returning a same-length list of strings.

```python
# A batch callable for bm25s.tokenize

def first_four(tokens):
    return [token[:4] for token in tokens]

result = bm25s.tokenize(
    ["running runner"],
    stopwords=None,
    stemmer=first_four,
    show_progress=False,
)
```

`PyStemmer` objects such as `Stemmer.Stemmer("english")` expose `stemWords` and can be passed directly to the module function. An NLTK-style single-token stemmer must be wrapped:

```python
from nltk.stem import PorterStemmer
porter = PorterStemmer()
result = bm25s.tokenize(
    ["running runner"],
    stopwords=None,
    stemmer=lambda tokens: [porter.stem(token) for token in tokens],
    show_progress=False,
)
```

A non-callable object without `stemWords` raises `ValueError`. A callable returning the wrong length or non-string values violates the algorithm's implicit contract and can produce missing-ID errors or unusable vocabularies; validate adapters with a tiny fixture first. Numeric IDs are assigned from a set of stemmed tokens in the module implementation, so never persist or compare module-function stem IDs by assuming a cross-process numeric order. Carry the returned `Tokenized` object when IDs and vocab must travel together.

## `Tokenizer` stemmer contract

`Tokenizer` adapts an object exposing `stemWord` to that bound method. Otherwise it requires a callable that accepts **one string** and returns **one string**:

```python
import Stemmer
from bm25s.tokenization import Tokenizer

stateful = Tokenizer(
    stopwords=None,
    stemmer=Stemmer.Stemmer("english"),  # stemWord is detected
)
custom = Tokenizer(
    stopwords=None,
    stemmer=lambda word: word[:4],
)
```

The class keeps three maps:

- `word_to_stem`: surface word to its computed stem;
- `stem_to_sid`: stem to the shared integer ID;
- `word_to_id`: surface word to either a stem ID or an unstemmed word ID.

`get_vocab_dict()` returns `stem_to_sid` when a stemmer is configured and `word_to_id` otherwise. Therefore corpus and query tokenization should use the same stemmer object/configuration and the same loaded state. `decode()` returns stems when a stemmer is active, not the original surface words.

A new surface form whose stem is already known may be mapped during `update_vocab=False`; `update_vocab="never"` intentionally disallows that new mapping. This makes `"never"` the strictest choice for a query against a frozen vocabulary.

## Stemming order and stopwords

The effective class pipeline is:

1. lowercase the document if requested;
2. run the regex or callable splitter;
3. skip configured stopword surface tokens;
4. resolve/apply the stemmer and update the class maps according to `update_vocab`;
5. emit IDs or decode them to strings.

A stopword list should contain the surface forms produced by the splitter. If a custom splitter returns punctuation or one-character tokens, those exact values are what the stopword filter sees.

## Choosing between the APIs

- Choose the module function for independent, batch-oriented conversion where a returned `Tokenized` vocabulary is enough.
- Choose `Tokenizer` for a corpus/query pair, frozen vocab behavior, `reset_vocab`, streaming, persistence, or different output modes from one shared state.
- Do not pass a per-word class stemmer directly to the module function; wrap it over a list. Do not pass a batch module stemmer directly to `Tokenizer`; adapt it to one word.

# Phrase Detection

`Phrases` detects token pairs or longer n-grams based on collocation counts.
`FrozenPhrases` is the reduced exported form for inference or reuse.

## Basic pattern

```python
from gensim.models import Phrases

sentences = [
    ["new", "york", "city"],
    ["new", "york", "times"],
    ["human", "computer", "interface"],
]
phrases = Phrases(sentences, min_count=1, threshold=1.0)
```

Iterating `phrases[sentence]` yields transformed tokens with phrase markers such
as `new_york` when the collocation score is strong enough.

## Useful parameters

- `min_count`: minimum collocation count.
- `threshold`: higher values make phrase creation stricter.
- `delimiter`: token inserted between phrase parts, often `_`.
- `connector_words`: stopword-like tokens that may be allowed inside phrases.
- `scoring`: choose the scoring strategy documented by the API.

## Workflow notes

- Phrase detection usually happens before Word2Vec/FastText/Doc2Vec training.
- Do not expect every bigram to be preserved; the score threshold is the gate.
- Save the trained `Phrases` model if you need the same transformation later.
- `FrozenPhrases` is useful when you want a compact read-only artifact.

## Troubleshooting

- If no phrases appear, lower `threshold` or `min_count` and inspect the token
  stream.
- If phrase tokens disappear after save/load, confirm that the scorer and
  connector-word configuration were preserved.
- If phrase boundaries are wrong, review tokenization and stopword handling
  before changing `Phrases` parameters.

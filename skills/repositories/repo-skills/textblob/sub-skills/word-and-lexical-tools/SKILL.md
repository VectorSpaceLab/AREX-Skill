---
name: word-and-lexical-tools
description: "Use TextBlob Word and WordList for word-level morphology, spelling
  correction, lemmatization, WordNet lookup, and lexical frequency utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TextBlob word and lexical tools

Use this sub-skill when the task is word-level: inflecting words, stemming,
lemmatizing with optional POS tags, checking spelling suggestions, using
WordNet synsets/definitions, operating on `WordList`, or counting already
extracted words/noun phrases.

Route elsewhere when the user needs document-level NLP first:

- Tokenization, sentence splitting, POS tagging, noun-phrase extraction,
  sentiment, parsing, n-grams, or full `TextBlob` workflows: sibling
  sub-skill `core-nlp-workflows`.
- Classifier training, classifier data formats, feature extractors, or
  `TextBlob(..., classifier=...)`: sibling sub-skill
  `classifiers-and-data-formats`.

## Bundled resources

- [Lexical reference](references/lexical-reference.md): API details, recipes,
  WordNet POS mapping, WordList behavior, and frequency patterns.
- [Troubleshooting](references/troubleshooting.md): missing corpora, wrong
  lemmas, spelling-correction caveats, inflection surprises, and list mutation
  gotchas.
- [Lexical smoke script](scripts/lexical_smoke.py): deterministic installed
  package smoke checks. Run `python scripts/lexical_smoke.py --help`.

## Operating workflow

1. **Confirm this is word-level.** If raw text still needs tokenization, POS
   tagging, noun phrases, or sentiment, route to `core-nlp-workflows` first and
   return here for lexical normalization or counts on the resulting words.
2. **Create lexical objects.** Import `Word` and `WordList` from `textblob`:
   `Word(string, pos_tag=None)` for one token and `WordList(collection)` for a
   list-like token collection.
3. **Choose the lexical operation.**
   - Inflection: `Word(...).singularize()` and `.pluralize()`; batch with
     `WordList(...).singularize()` or `.pluralize()`.
   - Lemmatization: `Word(...).lemmatize(pos=None)` or cached `.lemma` when a
     `Word` was created with `pos_tag`; pass a WordNet or Penn POS for verbs,
     adjectives, and adverbs.
   - Stemming: `Word(...).stem()` or `WordList(...).stem()`; Porter is the
     default stemmer.
   - Spelling: `Word(...).spellcheck()` returns `(candidate, confidence)`
     tuples; `.correct()` returns the top candidate as a `Word`.
   - WordNet: `.synsets`, `.get_synsets(pos=...)`, `.definitions`, and
     `.define(pos=...)` require the NLTK WordNet corpus.
   - Counts: use `WordList.count(term, case_sensitive=False)` for words or
     noun phrases that have already been extracted.
4. **Check corpora before WordNet-dependent operations.** `lemmatize`, `lemma`,
   synsets, and definitions rely on NLTK WordNet data. Do not download corpora
   implicitly; use the smoke script with `--skip-wordnet` when corpus-backed
   checks should be bypassed.
5. **Record uncertainty.** Spelling correction is heuristic and approximate;
   keep the original token, the proposed correction, and confidence when
   normalizing noisy keywords.
6. **Troubleshoot near the workflow.** If output is surprising, inspect
   `references/troubleshooting.md` before changing algorithms.

## Quick patterns

```python
from textblob import Word, WordList
from textblob.wordnet import VERB

Word("cats").singularize()          # Word('cat')
Word("speling").correct()           # Word('spelling')
Word("went").lemmatize(VERB)        # 'go'
Word("went", "VBD").lemma          # 'go'
WordList(["Dog", "dog"]).count("dog")  # 2, case-insensitive by default
```

For noisy keyword normalization, combine spelling suggestions with an explicit
POS-aware lemma and keep audit fields:

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
        "normalized": Word(chosen).lemmatize(pos),
    }
```

If `Word("went").lemmatize()` returns `"went"`, it used the default noun POS;
recover with `Word("went").lemmatize("v")`, `Word("went").lemmatize(VERB)`,
or `Word("went", "VBD").lemma`.

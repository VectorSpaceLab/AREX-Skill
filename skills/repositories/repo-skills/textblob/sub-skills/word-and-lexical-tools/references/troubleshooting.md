# Troubleshooting word and lexical tools

This guide covers failures and surprising behavior in `Word`, `WordList`,
spelling correction, lemmatization, inflection, and WordNet lookup. It does not
cover document tokenization, POS tagging, sentiment, parsing, classifier data,
or model-extension interfaces; route those to the appropriate sibling sub-skill.

## Quick triage

1. Identify whether the operation needs NLTK corpus data.
   - Does not require WordNet corpus: `singularize`, `pluralize`, `stem`,
     `spellcheck`, `correct`, most `WordList` list behavior.
   - Requires WordNet corpus: `lemmatize`, `lemma`, `synsets`, `get_synsets`,
     `definitions`, `define`, direct `Synset`/`Lemma` construction.
2. Run the bundled smoke script without modifying user data:

   ```bash
   python scripts/lexical_smoke.py --skip-wordnet
   python scripts/lexical_smoke.py --json
   ```

   The script only imports the installed package and checks APIs; it never
   downloads corpora.
3. If WordNet-backed checks fail, install TextBlob corpora explicitly outside
   the script with the installed package command:

   ```bash
   python -m textblob.download_corpora
   ```

   For only the basic default corpora, `python -m textblob.download_corpora lite`
   may be enough, but use the full command when WordNet or other optional
   corpus-backed features are required.

## Missing WordNet or other NLTK corpus data

### Symptom

`Word("wolves").lemma`, `Word("went").lemmatize("v")`, `Word("car").synsets`,
or `Word("octopus").definitions` raises a TextBlob missing corpus error or an
NLTK lookup error.

### Cause

TextBlob delegates lemmatization and WordNet lookup to NLTK's WordNet corpus.
The package import can succeed even when corpus data is absent.

### Recovery

- Do not add a hidden download step to a library function or smoke script.
- Ask the user to run corpus setup in the environment where TextBlob is
  installed:

  ```bash
  python -m textblob.download_corpora
  ```

- Re-run `python scripts/lexical_smoke.py --json` and confirm the `wordnet`
  check group passes.
- If the task can proceed without semantic lookup, re-run with
  `--skip-wordnet` and restrict the workflow to inflection, stemming, spelling,
  and `WordList` list behavior.

## Wrong lemma for a verb, adjective, or adverb

### Symptom

```python
Word("went").lemmatize()       # 'went', not 'go'
WordList(["went"]).lemmatize() # WordList(['went'])
```

### Cause

When `pos` is omitted, TextBlob uses WordNet noun POS. Many verb, adjective,
and adverb lemmas only resolve when a compatible POS tag is passed.

### Recovery

Pass WordNet or Penn Treebank POS explicitly:

```python
from textblob import Word
from textblob.wordnet import VERB

Word("went").lemmatize("v")      # 'go'
Word("went").lemmatize(VERB)     # 'go'
Word("went").lemmatize("VBD")    # 'go'
Word("went", "VBD").lemma        # 'go'
```

For batches, avoid `WordList.lemmatize()` when tokens have mixed POS. Keep POS
alongside tokens and iterate:

```python
tagged = [("went", "VBD"), ("cars", "NNS")]
lemmas = [Word(token, tag).lemma for token, tag in tagged]
```

## Spell correction changes a domain term incorrectly

### Symptom

`Word(token).correct()` changes a product name, identifier, jargon term, or rare
proper noun to a common dictionary word.

### Cause

TextBlob spelling correction is heuristic and approximate. It returns the top
candidate from a Norvig-style spelling model and the public documentation notes
roughly 70% accuracy. Confidence values are useful ranking signals, not
application-calibrated probabilities.

### Recovery

- Prefer `spellcheck()` over blind `correct()` so the pipeline can preserve
  the original token and confidence.
- Use a confidence threshold and domain allowlist.
- Keep an audit record with original token, suggestion, confidence, whether a
  correction was used, and the final normalized form.

```python
from textblob import Word
from textblob.wordnet import NOUN

ALLOW = {"TextBlob", "PyPI", "sklearn"}

def safe_normalize(token, pos=NOUN, min_confidence=0.90):
    if token in ALLOW:
        return {"original": token, "normalized": token, "used_correction": False}
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

Special cases such as punctuation (`!`), numbers (`42`, `12.34`), and common
one-letter words (`I`, `A`, `a`) are returned unchanged with confidence `1.0`.

## Inflection returns an unexpected plural or no change

### Symptom

- `Word("octopus").pluralize()` produces a classical plural.
- `Word("antelope").pluralize()` or `Word("jeans").singularize()` returns the
  original form.
- Compound or possessive forms pluralize a different component than expected.

### Cause

TextBlob's inflector is rule-based and includes irregular, uninflected,
uncountable, compound, possessive, and classical English rules. That is useful
for many English words but is not a domain ontology.

### Recovery

- For display text, verify the exact output against product style or domain
  vocabulary.
- For feature keys, prefer lemmatization with POS or a domain-specific mapping
  when inflection rules are too broad.
- For direct inflection functions with application-specific overrides, use the
  lower-level English inflector's `custom` mapping when appropriate:

  ```python
  from textblob.en.inflect import pluralize
  pluralize("corpus", custom={"corpus": "corpuses"})
  ```

## Stems look like non-words

### Symptom

```python
Word("wolves").stem()  # 'wolv'
```

### Cause

Stemming is not lemmatization. Porter stemming strips suffixes to create rough
feature keys and may produce strings that are not dictionary words.

### Recovery

- Use `lemmatize(pos=...)` when the output must be a dictionary word and the
  WordNet corpus is available.
- Use `stem()` only when a rough, corpus-free normalization key is acceptable.
- If you pass a custom stemmer, pass an object with a `.stem(string)` method.

## WordList count case surprises

### Symptom

```python
WordList(["monty", "Monty"]).count("monty")                 # 2
WordList(["monty", "Monty"]).count("monty", case_sensitive=True)  # 1
```

### Cause

`WordList.count` is case-insensitive by default. This differs from Python list's
case-sensitive `count` behavior.

### Recovery

- Pass `case_sensitive=True` for exact-case counting.
- Normalize the list explicitly with `.lower()` before counts when lowercased
  keys are desired.
- Use document-level `word_counts` or `np_counts` only after routing through the
  core NLP workflow that extracts `TextBlob.words` or `TextBlob.noun_phrases`.

## WordList slicing and mutation surprises

### Symptom

- `wl[:2]` is a `WordList`, not a plain `list`.
- Appending a string changes it into a `Word`.
- Appending non-strings preserves their original type.
- `WordList.lemmatize()` ignores per-token POS.

### Cause

`WordList` subclasses `list` but overrides selected behavior to preserve
TextBlob lexical objects.

### Recovery

```python
wl = WordList(["dog"])
wl.append("cat")         # Word('cat')
wl.append(("x", "NN"))  # tuple preserved, not converted
plain = list(wl)          # convert when a normal list is required
slice_is_wordlist = wl[:1]
```

For POS-aware batch lemmatization, use a list of `(token, pos)` pairs and
construct `Word(token, pos)` manually rather than using `WordList.lemmatize()`.

## Normalizing noisy keywords safely

For noisy keywords, combine correction and lemmatization only when both
uncertainties are explicit:

1. Run `Word(token).spellcheck()`.
2. Choose the suggestion only if confidence and domain allowlist rules permit.
3. Lemmatize the chosen string with explicit POS when known.
4. Preserve original token, suggestion, confidence, selected POS, and final
   normalized output.
5. If WordNet is unavailable, either skip lemmatization or use stemming as an
   explicitly lossy fallback.

This pattern prevents silent data corruption when TextBlob's spelling model or
WordNet POS default disagrees with the user's domain.

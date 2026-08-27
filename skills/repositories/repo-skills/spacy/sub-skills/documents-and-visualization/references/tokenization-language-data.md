# Tokenization, language data, and batch processing

Use this reference when you need to create docs from raw text, batch documents efficiently, customize tokenization, or define language-specific defaults.

## Choose the right entry point

| Task | Recommended API | Notes |
| --- | --- | --- |
| Process one text with the current pipeline | `nlp(text)` | Tokenizes first, then runs each pipeline component. |
| Process many texts efficiently | `nlp.pipe(texts)` | Streams docs in batches instead of one-by-one. |
| Carry metadata alongside texts | `nlp.pipe(texts, as_tuples=True)` | Input is `(text, context)` and output is `(doc, context)`. |
| Create a doc without running the full pipeline | `nlp.make_doc(text)` | Best when you only need tokenization and lexical attributes. |
| Create a blank pipeline | `spacy.blank("en")` | Use this when you do not have a pretrained package installed. |
| Load an installed pipeline package | `spacy.load("en_core_web_sm")` | Use this only when the package is already available locally. |

`nlp.pipe` is usually the fastest way to process a large stream. Use `disable=[...]` when you only need a subset of the pipeline.

## `spacy.blank` vs `spacy.load`

- `spacy.blank(lang)` creates a new language object with the default tokenizer and language data for that language code.
- `spacy.load(name_or_path)` loads a saved pipeline package or model directory and returns a `Language` object.
- If a pretrained model is not installed, do not block the workflow: use a blank pipeline and manual annotations instead.

## Tokenizer basics

The default tokenizer reads its rules from the language class defaults.

| Tokenizer feature | What it controls |
| --- | --- |
| `rules` | Special cases and exceptions. |
| `prefix_search` | Prefix stripping. |
| `suffix_search` | Suffix stripping. |
| `infix_finditer` | Internal split points such as hyphens. |
| `token_match` | Tokens that should stay intact. |
| `url_match` | URL-style token matches. |
| `faster_heuristics` | Whether the final matcher pass is limited for speed. |

Useful helper methods:

- `Tokenizer.pipe(texts)` tokenizes a stream without running a pipeline.
- `Tokenizer.explain(text)` shows which tokenizer rule produced each token.
- `Tokenizer.to_bytes` / `from_bytes` and `Tokenizer.to_disk` / `from_disk` persist tokenizer state.

### Manual doc construction

If you already have token boundaries, build a `Doc` directly:

```python
from spacy.tokens import Doc

doc = Doc(nlp.vocab, words=["Hello", ",", "world", "!"], spaces=[False, True, False, False])
```

The `spaces` list must match the words list. It controls `doc.text`, `token.idx`, `span.start_char`, and `span.end_char`.

## Custom tokenizers

You usually do not need a tokenizer subclass. Most customizations can be expressed by replacing the regex callables or by adding special cases.

Example pattern:

```python
import re
from spacy.tokenizer import Tokenizer

special_cases = {":)": [{"ORTH": ":)"}]}
prefix_re = re.compile(r"^[\[\(\"']")
suffix_re = re.compile(r"[\]\)\"']$")
infix_re = re.compile(r"[-~]")
url_re = re.compile(r"^https?://")

nlp.tokenizer = Tokenizer(
    nlp.vocab,
    rules=special_cases,
    prefix_search=prefix_re.search,
    suffix_search=suffix_re.search,
    infix_finditer=infix_re.finditer,
    url_match=url_re.match,
)
```

Language-specific notes:

- When you modify `nlp.Defaults` on a blank pipeline, the new rules are used to build the tokenizer.
- If you load a trained pipeline, change `nlp.tokenizer` directly instead of editing `Defaults`.
- `Tokenizer.add_special_case` is the easiest way to add an exception such as a contraction or acronym.
- `Tokenizer.explain` is useful when you need to see why a token was split a certain way.

## Language data basics

A custom language subclass usually defines two things:

- `lang`: the language code.
- `Defaults`: the class that provides tokenizer rules, lexical attributes, and language data.

You can also register a custom class with `@spacy.registry.languages("custom_en")` and then call `spacy.blank("custom_en")`.

Example:

```python
import spacy
from spacy.lang.en import English

class CustomEnglishDefaults(English.Defaults):
    stop_words = {"custom", "stop"}

@spacy.registry.languages("custom_en")
class CustomEnglish(English):
    lang = "custom_en"
    Defaults = CustomEnglishDefaults
```

## `nlp.pipe(as_tuples=True)`

Use `as_tuples=True` to keep metadata attached to each text.

```python
pairs = [("text one", {"id": "a"}), ("text two", {"id": "b"})]
for doc, context in nlp.pipe(pairs, as_tuples=True):
    doc._.id = context["id"]
```

This is the preferred pattern when you need efficient batch processing and per-document context.

## Optional extras and language-specific tokenizers

| Extra | What it adds | Caveat |
| --- | --- | --- |
| `lookups` | Lookup data for lemmatizers and other language tables. | Needed when you rely on lookup or rule-based lemmatization in a new pipeline. |
| `ja` | Japanese tokenizer dependency stack. | Not installed by default in this skill unless explicitly added. |
| `ko` | Korean tokenizer dependency stack. | Not installed by default in this skill unless explicitly added. |
| `th` | Thai tokenizer dependency stack. | Not installed by default in this skill unless explicitly added. |

A few practical rules:

- Do not claim the optional language-tokenizer extras are available unless they were installed.
- Use `nlp.make_doc` or `nlp.tokenizer.pipe` when you only need phrase-pattern docs and not the full pipeline.
- If a matcher or ruler depends on `LEMMA`, `POS`, or `DEP`, make sure the pattern docs were built with those annotations present.

## Fast debugging checks

- Print `[t.text for t in nlp.make_doc(text)]` to inspect tokenization.
- Use `nlp.tokenizer.explain(text)` to see which rule created each token.
- Use `doc.has_annotation("DEP")` or `doc.has_annotation("ENT_IOB")` before depending on parse or entity annotations.

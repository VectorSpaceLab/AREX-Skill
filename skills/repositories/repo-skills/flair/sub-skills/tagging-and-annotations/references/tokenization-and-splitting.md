# Tokenization and Splitting

Flair separates tokenization (`flair.tokenization`) from sentence splitting (`flair.splitter`). Tokenization controls `Token` boundaries inside a `Sentence`; splitters turn longer text into multiple `Sentence` objects and assign each sentence a `start_position` in the source text.

## Sentence construction choices

```python
from flair.data import Sentence
from flair.tokenization import NoTokenizer, SegtokTokenizer, SpaceTokenizer

# Default: SegtokTokenizer for Indo-European-style word and punctuation splitting.
s1 = Sentence("The grass is green.")

# Boolean False uses SpaceTokenizer: split on spaces only, punctuation stays attached.
s2 = Sentence("The grass is green.", use_tokenizer=False)

# Explicit tokenizer instance.
s3 = Sentence("Law §3 applies.", use_tokenizer=SegtokTokenizer(additional_split_characters=["§"]))

# Whole input as one token. Useful for classifier-only workflows that must avoid word splitting.
s4 = Sentence("do-not-split-this", use_tokenizer=NoTokenizer())

# Pre-tokenized list. Flair uses NoTokenizer internally and reconstructs text with spaces.
s5 = Sentence(["George", "Washington", "went", "home", "."])
```

Offset behavior:

- `sentence.start_position` is the offset of the sentence in a larger text.
- `token.start_position` and `token.end_position` are offsets relative to `sentence.text`, not absolute document offsets.
- Absolute document start for a token is usually `sentence.start_position + token.start_position`.
- `sentence.end_position` includes `sentence.start_position` plus the final token end/whitespace.

## Tokenizer decision map

| Tokenizer | When to use | Dependency status and caveats |
| --- | --- | --- |
| `SegtokTokenizer(additional_split_characters=None)` | Default general-purpose word/punctuation tokenization. | CPU baseline; uses `segtok`, a core Flair dependency. Optional `additional_split_characters` forces specified characters to split as separate tokens. |
| `SpaceTokenizer()` / `use_tokenizer=False` | Input is already space-separated or punctuation should remain attached to words. | CPU baseline. Multiple spaces are collapsed as separators; offsets reflect original word locations. |
| `NoTokenizer()` | Treat the whole non-empty string as one token. | CPU baseline. Useful for document classification fixtures or exact no-split behavior. |
| `StaccatoTokenizer()` | Unicode/script-aware rule-based tokenization without large NLP models. | CPU baseline when available in the installed package. Splits punctuation and CJK kanji, preserves many alphabetic runs. |
| `SpacyTokenizer(model)` | Align Flair tokenization with a spaCy model. | Optional. Requires `spacy` and the named model or a loaded `Language` object. Serialization reloads by model name. |
| `SciSpacyTokenizer()` | Biomedical tokenization with `en_core_sci_sm` and extra split heuristics. | Optional/unverified. Requires matching SciSpaCy/spaCy model install; route biomedical usage to the biomedical sub-skill. |
| `JapaneseTokenizer("mecab"|"janome"|"sudachi", sudachi_mode="A")` | Japanese tokenization through Konoha backends. | Optional/unverified. Requires `konoha` and selected backend system/Python packages. Missing dependency may exit during construction in some versions. |
| `TokenizerWrapper(function)` | Quick adapter for a Python tokenization function. | Not automatically reconstructable from serialized state; avoid it for persisted skill examples unless the function is re-created manually. |

## Sentence splitter choices

```python
from flair.splitter import (
    NewlineSentenceSplitter,
    NoSentenceSplitter,
    SegtokSentenceSplitter,
    TagSentenceSplitter,
)
from flair.tokenization import SegtokTokenizer, SpaceTokenizer

text = "First sentence. Second sentence."

# Default splitter for many plain-text cases.
sentences = SegtokSentenceSplitter().split(text)

# Use a custom tokenizer after splitting.
sentences_space = SegtokSentenceSplitter(tokenizer=SpaceTokenizer()).split(text)

# Use known document boundaries.
paragraph_sentences = NewlineSentenceSplitter(tokenizer=SegtokTokenizer()).split("line one\nline two")
xml_like = TagSentenceSplitter("<SPLIT>").split("one<SPLIT>two")

# Keep full text as one Sentence.
one = NoSentenceSplitter().split(text)
```

Splitter behavior to remember:

- `split(text, link_sentences=True)` is the default and sets previous/next sentence context links. Pass `link_sentences=False` when this context should not be attached.
- `SegtokSentenceSplitter` uses SegTok sentence segmentation and records sentence offsets using each sentence substring in the original text.
- `TagSentenceSplitter` and `NewlineSentenceSplitter` split on explicit markers and skip empty fragments.
- `NoSentenceSplitter` returns a one-element list with `start_position=0`.
- `SpacySentenceSplitter(model, tokenizer=None)` and `SciSpacySentenceSplitter()` are optional routes. Confirm `spacy`, the selected model, and any SciSpaCy model before relying on them.

## Retokenization and annotation preservation

A `Sentence` stores the tokenizer that last created its tokens. Changing `sentence.tokenizer` does not immediately retokenize; the next access to `sentence.tokens` compares the new tokenizer with the old one and retokenizes lazily.

```python
from flair.data import Sentence
from flair.tokenization import SegtokTokenizer, SpaceTokenizer

sentence = Sentence("A tokenization-sensitive sentence.", use_tokenizer=SegtokTokenizer())
_ = sentence.tokens
sentence[0:1].add_label("ner", "THING")

sentence.tokenizer = SpaceTokenizer()
# Retokenization occurs when tokens are accessed. Flair attempts to preserve
# sentence/span/relation annotations by character offsets; token-level labels are lost.
_ = sentence.tokens
```

Rules:

- Decide tokenizer/splitter before adding token-level labels or running models whenever possible.
- Span and relation annotations are captured by character offsets during retokenization and deserialization, but this can fail if new token boundaries do not cover the same character ranges.
- Token-level annotations do not have reliable preservation through retokenization. Re-run prediction or re-map labels explicitly.
- Prediction methods may set `sentence.tokenizer` to the model tokenizer when the model carries one. This can trigger lazy retokenization.

## Serialization implications

Tokenizers implement `to_dict()` and `from_dict()` for serialization. `Sentence.to_dict()` stores the tokenizer config, and `Sentence.from_dict()` imports the class by module/name and reconstructs it.

Safe no-extra-dependency tokenizers for round-trip examples:

```python
from flair.data import Sentence
from flair.tokenization import SegtokTokenizer, SpaceTokenizer, StaccatoTokenizer

for tokenizer in [SegtokTokenizer(), SpaceTokenizer(), StaccatoTokenizer()]:
    s = Sentence("This is a test.", use_tokenizer=tokenizer)
    recreated = Sentence.from_dict(s.to_dict())
    assert recreated.tokenizer.name == s.tokenizer.name
```

Avoid persisting examples that require unavailable optional dependencies. For `SpacyTokenizer`, `SciSpacyTokenizer`, or `JapaneseTokenizer`, include a dependency check and a fallback to `SegtokTokenizer` or `SpaceTokenizer` unless the environment explicitly verifies those extras.

## Practical offset checks

Use offsets as assertions when a workflow depends on exact spans:

```python
from flair.data import Sentence

sentence = Sentence("This is a sentence.", start_position=10)
assert sentence.start_position == 10
assert [(token.text, token.start_position, token.end_position) for token in sentence] == [
    ("This", 0, 4),
    ("is", 5, 7),
    ("a", 8, 9),
    ("sentence", 10, 18),
    (".", 18, 19),
]
absolute_spans = [
    (token.text, sentence.start_position + token.start_position, sentence.start_position + token.end_position)
    for token in sentence
]
```

For `RegexpTagger`, run the same kind of offset check first. If regex matches do not line up with token starts and ends, the tagger raises because it cannot create a partial-token `Span`.

## CPU-first tokenizer fallback pattern

```python
from flair.tokenization import SegtokTokenizer

try:
    from flair.tokenization import SpacyTokenizer
    tokenizer = SpacyTokenizer("en_core_web_sm")
except Exception:
    tokenizer = SegtokTokenizer()
```

Use this only when approximate fallback tokenization is acceptable. If exact alignment to a spaCy/SciSpaCy/Japanese pipeline is required, treat missing dependencies as a blocker rather than silently changing tokenization.

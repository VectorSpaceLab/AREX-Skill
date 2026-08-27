# Rule-based matching and rulers

This reference covers token matchers, phrase matchers, dependency matchers, and the rule-based entity/span rulers.

## Choose the right tool

| Tool | Best for | Input pattern type | Output target |
| --- | --- | --- | --- |
| `Matcher` | Rich token-level rules with operators and callbacks. | List of token-pattern dicts. | Match tuples or spans. |
| `PhraseMatcher` | Large terminology lists and exact phrase matching. | `Doc` objects. | Match tuples or spans. |
| `DependencyMatcher` | Relations in the dependency tree. | List of node dicts with `RIGHT_ID`, `LEFT_ID`, `REL_OP`, `RIGHT_ATTRS`. | Match tuples with token-id lists. |
| `EntityRuler` | Add entities with token or phrase patterns. | Pattern dicts with `label`, `pattern`, optional `id`. | `Doc.ents`. |
| `SpanRuler` | Add spans to `Doc.spans` and optionally `Doc.ents`. | Pattern dicts with `label`, `pattern`, optional `id`. | `Doc.spans[spans_key]` and/or `Doc.ents`. |

## `Matcher`

### Pattern structure

Each dictionary in a token pattern describes one token.

Common keys:

- `ORTH`, `TEXT`, `LOWER`, `NORM`
- `LENGTH`, `IS_ALPHA`, `IS_ASCII`, `IS_DIGIT`, `IS_LOWER`, `IS_UPPER`, `IS_TITLE`, `IS_PUNCT`, `IS_SPACE`, `IS_STOP`, `IS_SENT_START`
- `LIKE_NUM`, `LIKE_URL`, `LIKE_EMAIL`
- `SPACY`
- `POS`, `TAG`, `MORPH`, `DEP`, `LEMMA`, `SHAPE`
- `ENT_TYPE`, `ENT_IOB`, `ENT_ID`, `ENT_KB_ID`
- `_` for custom extension attributes
- `OP` for operators

Operators:

| OP | Meaning |
| --- | --- |
| `!` | Match exactly 0 times. |
| `?` | Match 0 or 1 times. |
| `+` | Match 1 or more times. |
| `*` | Match 0 or more times. |
| `{n}` | Match exactly `n` times. |
| `{n,m}` | Match between `n` and `m` times. |
| `{n,}` | Match at least `n` times. |
| `{,m}` | Match at most `m` times. |

Validation notes:

- `Matcher(..., validate=True)` validates each added pattern against the schema.
- `matcher.add("LABEL", [patterns], on_match=callback, greedy="FIRST"|"LONGEST")` is the current API shape.
- `matcher(doc)` returns `(match_id, start, end)` tuples, unless you pass `as_spans=True`.
- `allow_missing=True` can skip missing-annotation checks for pattern attributes that are not present yet.

Example:

```python
from spacy.matcher import Matcher

matcher = Matcher(nlp.vocab, validate=True)
matcher.add("HELLO_WORLD", [[{"LOWER": "hello"}, {"IS_PUNCT": True}, {"LOWER": "world"}]])
```

### Debugging no-match cases

1. Inspect tokenization first: `print([t.text for t in nlp.make_doc(text)])`.
2. Compare the pattern token count with the runtime token count.
3. If the pattern uses `POS`, `LEMMA`, `DEP`, or similar annotations, make sure the doc actually has those annotations.
4. Turn on validation while building patterns.

## `PhraseMatcher`

The `PhraseMatcher` compares `Doc` patterns rather than token dicts.

| Setting | Behavior |
| --- | --- |
| `attr="ORTH"` | Match verbatim token text. |
| `attr="LOWER"` | Case-insensitive matching. |
| `attr="SHAPE"` | Match by token shape. |
| `attr="POS"` or similar | Works when the pattern docs have that annotation. |

Recommendations:

- Use `nlp.make_doc(term)` when you only need tokenization and lexical attributes.
- Use `nlp(term)` if the chosen attribute depends on a pipeline component such as `TAG` or `LEMMA`.
- Use `validate=True` when you want a warning for unnecessary annotations on the pattern docs.

Example:

```python
from spacy.matcher import PhraseMatcher

matcher = PhraseMatcher(nlp.vocab, attr="LOWER", validate=True)
matcher.add("CITIES", [nlp.make_doc("New York")])
```

## `DependencyMatcher`

`DependencyMatcher` looks for token relations in a dependency tree.

Pattern keys:

| Key | Meaning |
| --- | --- |
| `RIGHT_ID` | Unique node name for the current token. |
| `RIGHT_ATTRS` | Token attributes for the current node. |
| `LEFT_ID` | Name of a previously defined node. |
| `REL_OP` | Relation between the left and right nodes. |

Important notes:

- The first node in a pattern is the anchor and uses only `RIGHT_ID` and `RIGHT_ATTRS`.
- A token name must be defined as `RIGHT_ID` before it can be used as `LEFT_ID`.
- `DependencyMatcher` expects a doc with dependency annotation, either from a parser or from a manually constructed `Doc` with `heads` and `deps`.
- It supports Semgrex-style operators such as `>`, `>>`, `<`, `<<`, `.`, `;`, `$+`, `$-`, and siblings/child variants.
- Use specific anchors and short paths when possible; broad patterns can become slow.

Example:

```python
from spacy.matcher import DependencyMatcher

matcher = DependencyMatcher(nlp.vocab, validate=True)
pattern = [
    {"RIGHT_ID": "anchor", "RIGHT_ATTRS": {"ORTH": "founded"}},
    {"LEFT_ID": "anchor", "REL_OP": ">", "RIGHT_ID": "subject", "RIGHT_ATTRS": {"DEP": "nsubj"}},
]
matcher.add("FOUNDED", [pattern])
```

## `EntityRuler`

The entity ruler adds entities to `Doc.ents`.

Pattern dicts use these keys:

- `label`: entity label to assign
- `pattern`: phrase string or token-pattern list
- `id`: optional entity ID that becomes `ent_id_`

Useful settings:

| Setting | Behavior |
| --- | --- |
| `validate` | Validate patterns against the matcher schema. |
| `phrase_matcher_attr` | Attribute used for phrase patterns, such as `LOWER`. |
| `overwrite_ents` | Whether new matches may overwrite overlapping predicted entities. |

Operational notes:

- If the ruler is added before `ner`, the parser/NER will respect the preset entities.
- If it is added after `ner`, it only adds non-overlapping entities unless overwrite is enabled.
- Use `to_disk` / `from_disk` to persist the ruler patterns as JSONL.

## `SpanRuler`

The span ruler is the generalization of the entity ruler for `Doc.spans`.

Default output settings:

| Setting | Behavior |
| --- | --- |
| `spans_key` | Target key in `Doc.spans`. The runtime default is `"ruler"`. |
| `annotate_ents` | Also write accepted spans to `Doc.ents`. |
| `overwrite` | Replace existing spans or entities when writing results. |
| `validate` | Validate patterns before adding them. |
| `phrase_matcher_attr` | Attribute used for phrase patterns. |
| `matcher_fuzzy_compare` | Fuzzy comparison function for token patterns. |

Important span-ruler notes:

- Overlapping matches are allowed in `Doc.spans`.
- If you want the span ruler to annotate entities, use `annotate_ents=True` and let the filter resolve overlaps for `Doc.ents`.
- Pattern files are often loaded separately and passed to `initialize(..., patterns=...)` or `add_patterns(...)`.
- Use `options={"spans_key": "ruler"}` when rendering a span ruler output with displaCy.

## Troubleshooting patterns

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| No matches at all | Tokenization mismatch | Inspect tokens and rewrite the pattern to match the runtime tokenization. |
| Validation error on add | Bad attribute name or value type | Turn on validation and fix the schema error. |
| Dependency matches never fire | No dependency annotations | Use a parsed doc or manually supply `heads` and `deps`. |
| Entity ruler misses phrase patterns | Wrong phrase attribute | Set `phrase_matcher_attr` to the attribute you actually need. |
| Span ruler output is empty | Wrong `spans_key` | Match the renderer or consumer to the configured key. |

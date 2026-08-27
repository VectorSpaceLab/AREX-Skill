# Data formats

## CoNLL-U column mapping

Stanza uses the standard 10-column CoNLL-U layout:

| Column | Field |
| --- | --- |
| 1 | `id` |
| 2 | `text` |
| 3 | `lemma` |
| 4 | `upos` |
| 5 | `xpos` |
| 6 | `feats` |
| 7 | `head` |
| 8 | `deprel` |
| 9 | `deps` |
| 10 | `misc` |

Comments are stored separately from token rows and are preserved per sentence.

## In-memory shapes

- `Document(sentences, ...)` expects a list of sentences.
- Each sentence is a list of token dictionaries in CoNLL-like form.
- `Sentence.to_dict()` returns one list of dictionaries for that sentence.
- `Document.to_dict()` returns a list of sentence lists.
- `Token.to_dict()` returns a list of dictionaries because one token can emit one MWT row plus one dictionary per word.
- `Word.to_dict()` returns a single dictionary.

Example token dictionary keys:
- `id`
- `text`
- `lemma`
- `upos`
- `xpos`
- `feats`
- `head`
- `deprel`
- `deps`
- `misc`
- `ner`
- `multi_ner`
- `manual_expansion`
- `start_char`
- `end_char`
- `coref_chains`
- `morphemes`

## Special ID forms

- normal words use integer IDs, represented internally as `(1,)` in dictionaries
- multi-word tokens use ranges such as `6-7`, represented internally as `(6, 7)`
- empty nodes use dotted IDs such as `5.1`, represented internally as `(5, 1)`

Use `ignore_gapping=False` when you want to retain empty nodes.
With `ignore_gapping=True`, empty-node rows are skipped during parse.

## Comments and metadata

Recognized sentence comments include:
- `# text = ...`
- `# sent_id = ...`
- `# doc_id = ...`
- `# newdoc id = ...`
- `# speaker = ...`
- `# sentiment = ...`
- `# constituency = ...`

`conll2multi_docs(...)` uses `# doc_id = ...` or `# newdoc id = ...` to split one file into multiple `Document` objects.

## Offsets and misc fields

The following annotations are carried through the `misc` field or dedicated token fields depending on context:
- `start_char`
- `end_char`
- `SpaceAfter` / `SpacesAfter`
- `SpacesBefore`
- `ner`
- `coref_chains`
- `Morphemes`
- `line_number` when line numbers are requested during parse

Notes:
- `start_char` and `end_char` are handled as dedicated fields on tokens and words, but they round-trip through output formatting.
- NER lives on tokens; single-word token NER is propagated to the word when exported.
- Coreference is serialized under `coref_chains`, not `ner`.
- `line_number` is internal inspection metadata and is not written back out.

## Formatting and round-trip behavior

- `{:C}` prints comments plus rows.
- `{:c}` prints rows only.
- `{:C-o}` and `{:c-o}` suppress offsets in the output.
- `CoNLL.write_doc2conll(...)` always appends the final blank line required by legal CoNLL-U output.
- `feats` and `misc` fragments are normalized and sorted during output, so exact ordering may change even when the semantic content does not.
- `CoNLL.convert_dict(doc.to_dict())` round-trips columns, but it does not preserve sentence comments.

## What survives a round trip

Preserved by `conll2doc` / `write_doc2conll`:
- token and word rows
- comments
- empty words when `ignore_gapping=False`
- multi-word token structure
- offsets, NER, and coreference annotations when present

Not preserved by `convert_dict` alone:
- sentence comments
- document split boundaries
- line-number metadata

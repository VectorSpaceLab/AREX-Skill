# API reference

Verification basis: Stanza 1.14.0 source, tests, and installed API signatures. Check the root provenance file before treating these facts as current for another checkout or package version.

Installed signatures captured from the prepared environment:

- `Document(sentences, text=None, comments=None, empty_sentences=None)`
- `Document.get(fields, as_sentences=False, from_token=False)`
- `Document.set(fields, contents, to_token=False, to_sentence=False)`
- `Document.set_mwt_expansions(expansions, fake_dependencies=False, process_manual_expanded=None)`
- `Document.get_mwt_expansions(evaluation=False)`
- `Document.to_serialized()`
- `Document.from_serialized(serialized_string)`
- `CoNLL.conll2doc(input_file=None, input_str=None, ignore_gapping=True, zip_file=None, keep_line_numbers=False)`
- `CoNLL.conll2dict(input_file=None, input_str=None, ignore_gapping=True, zip_file=None, keep_line_numbers=False)`
- `CoNLL.conll2multi_docs(input_file=None, input_str=None, ignore_gapping=True, zip_file=None)`
- `CoNLL.write_doc2conll(doc, filename, mode='w', encoding='utf-8')`

## Object constructors

- `Sentence(tokens, doc=None, empty_words=None)`
- `Token(sentence, token_entry, words=None)`
- `Word(sentence, word_entry)`
- `Span(span_entry=None, tokens=None, type=None, doc=None, sent=None)`

## Document

Use `Document` for the whole text, sentence list, entity list, and coreference list.

Common fields:
- `sentences`
- `text`
- `lang`
- `num_tokens`
- `num_words`
- `ents` / `entities`
- `coref`

Common operations:
- `doc.get(...)` returns values from words by default, or from tokens with `from_token=True`
- `doc.set(...)` writes values to words by default, or to tokens with `to_token=True`, or to sentences with `to_sentence=True`
- `doc.build_ents()` derives entity spans from token BIOES NER tags
- `doc.iter_words()` and `doc.iter_tokens()` traverse the document
- `doc.sentence_comments()` returns the per-sentence comment lists
- `doc.reindex_sentences(start_index)` resets `sent_id` values in order
- `doc.sort_features()` normalizes feature order before comparison

Multi-word token helpers:
- `doc.get_mwt_expansions()` returns source/expansion pairs for MWTs
- `doc.get_mwt_expansions(evaluation=True)` returns only the source strings
- `doc.set_mwt_expansions(...)` rewrites token/word structure after expansion
- `process_manual_expanded=True` means only manually expanded tokens are processed
- `process_manual_expanded=False` means only explicit `MWT=Yes` tokens are processed
- `process_manual_expanded=None` keeps the default mixed behavior

Serialization:
- `doc.to_serialized()` returns UTF-8 JSON bytes with text, sentences, and comments
- `Document.from_serialized(...)` accepts the current JSON format and a deprecated restricted pickle fallback

Formatting:
- `{:c}` on a `Document` or `Sentence` prints CoNLL-U rows without comments
- `{:C}` includes sentence comments above the rows
- `{:c-o}` and `{:C-o}` suppress offset fields in the output

## Sentence

`Sentence` stores one sentence worth of tokens and words.

Important fields:
- `tokens`
- `words`
- `empty_words`
- `all_words`
- `dependencies`
- `enhanced_dependencies`
- `comments`
- `sent_id`
- `doc_id`
- `speaker`
- `sentiment`
- `constituency`
- `ents` / `entities`

Use the property setters when you want the comment list kept in sync:
- setting `sent_id` adds or replaces `# sent_id = ...`
- setting `doc_id` adds or replaces `# doc_id = ...`
- setting `speaker` adds, replaces, or removes `# speaker = ...`
- setting `sentiment` adds or replaces `# sentiment = ...`
- setting `constituency` adds or replaces `# constituency = ...`

`Sentence.add_comment(...)` also recognizes those special comment forms and updates the cached properties.

## Token

`Token` is the surface token row. A token can be one row or a multi-word token.

Important fields:
- `id`
- `text`
- `misc`
- `ner`
- `multi_ner`
- `start_char`
- `end_char`
- `spaces_before`
- `spaces_after`
- `manual_expansion`
- `words`
- `line_number`

Notes:
- multi-word tokens use tuple IDs such as `(6, 7)`
- single-word tokens still keep one `Word` in `token.words`
- token-level NER and offsets are preserved separately from word-level syntax

## Word

`Word` stores the syntactic row.

Important fields:
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
- `start_char`
- `end_char`
- `manual_expansion`
- `coref_chains`
- `sent`
- `parent`

Notes:
- `deps` is the enhanced dependency view backed by the sentence graph
- `coref_chains` holds `CorefAttachment` objects when `doc.coref` is populated
- empty nodes use tuple IDs like `(5, 1)`

## Span

`Span` models entity and mention spans.

Important fields:
- `text`
- `type`
- `start_char`
- `end_char`
- `tokens`
- `words`
- `sent`
- `doc`

## StanzaObject extension hook

`Document`, `Sentence`, `Token`, `Word`, and `Span` inherit `StanzaObject`.
If you need a temporary custom field for local manipulation, use `add_property(...)` instead of mutating the class internals directly.

# Troubleshooting

## Wrong number of fields

**Symptom:** `Cannot parse CoNLL line ... expecting 10 fields`

**Cause:** a token row does not have exactly 10 tab-separated columns, or the row was converted to spaces.

**Fix:**
- make sure every token row has 10 columns
- keep comments on lines that begin with `#`
- preserve tabs in the file
- run `scripts/validate_conllu.py` to get a clear line-numbered failure

## Bad IDs or head indices

**Symptom:** `Could not process ID ...` or a dependency `IndexError`

**Cause:** the ID format is invalid, or a dependency head points outside the sentence.

**Fix:**
- use `1`, `2`, `3` for ordinary words
- use `6-7` for multi-word tokens
- use `5.1` for empty nodes
- keep dependency heads inside the sentence, with `0` reserved for root
- if you see `Word head X is not a valid word index`, the dependency tree is structurally broken

## Conflicting comments

**Symptom:** `sent_id`, `doc_id`, or `speaker` seems to change unexpectedly.

**Cause:** those properties are mirrored into the comment list, so duplicate comments may overwrite each other.

**Fix:**
- keep only one authoritative `# sent_id = ...` per sentence
- keep only one authoritative `# doc_id = ...` per sentence
- use the property setter rather than manually splicing duplicate comment lines
- use `conll2multi_docs(...)` when `# doc_id = ...` or `# newdoc id = ...` should split documents

## Multi-word tokens and empty nodes

**Symptom:** the output has fewer rows than the input, or word counts look off.

**Cause:** multi-word tokens and empty nodes are handled differently from ordinary words.

**Fix:**
- `Token` objects represent surface tokens
- `Word` objects represent syntactic words
- use `ignore_gapping=False` to keep empty nodes
- inspect `sentence.empty_words` and `sentence.all_words` when debugging gapping
- remember that `doc.num_tokens` and `doc.num_words` do not count empty nodes
- if you change token expansions, call `doc.set_mwt_expansions(...)` so dependencies are rebuilt consistently

## Text offsets are wrong

**Symptom:** entity text, token spacing, or span extraction looks misaligned.

**Cause:** `start_char` / `end_char` are missing, inconsistent, or not aligned with `Document.text`.

**Fix:**
- verify the offsets on the token rows
- remember that whitespace is reconstructed onto token `spaces_before` / `spaces_after`
- check whether the raw document text matches the offsets exactly
- if the file originated from another system, confirm that offsets are zero-based and end-exclusive as expected by Stanza

## Serialization issues

**Symptom:** a round-trip through `to_serialized()` or `from_serialized()` fails.

**Cause:** the object is outside the supported serialization scope, or an old pickle blob is being loaded.

**Fix:**
- use `Document.to_serialized()` for a supported JSON byte stream
- only load pickle blobs from trusted sources; the pickle fallback is restricted but still deprecated
- remember that serialization is for the document payload, not arbitrary Python objects
- if you only need CoNLL columns, use `CoNLL.write_doc2conll(...)` instead

## Token-vs-word confusion

**Symptom:** an annotation appears in the wrong place or disappears on write.

**Cause:** token-level fields were written as word-level fields, or vice versa.

**Fix:**
- token-level: `ner`, `multi_ner`, offsets, whitespace, `manual_expansion`
- word-level: `lemma`, `upos`, `xpos`, `feats`, `head`, `deprel`, `deps`
- use `doc.get(..., from_token=True)` for token annotations
- use `doc.set(..., to_token=True)` for token annotations
- use `to_sentence=True` only for sentence metadata

## NER and coreference fields

**Symptom:** entities or coreference chains are missing.

**Cause:** token BIOES tags were not converted into spans, or coref attachments were not populated on the words.

**Fix:**
- call `doc.build_ents()` after setting token NER tags
- check that token NER tags follow the expected BIOES scheme
- assign coreference chains through `doc.coref`
- inspect `word.coref_chains` for the per-word attachments
- remember that coref serializes through `coref_chains` in `misc`, not through the NER field

## When nothing makes sense

Start from a minimal round-trip:
1. parse with `CoNLL.conll2doc(...)`
2. inspect `len(doc.sentences)`, `doc.num_tokens`, and `doc.num_words`
3. print `{:C}` and compare it to the source
4. run `scripts/validate_conllu.py` before changing any code

# Workflows

## 1) Load and inspect a CoNLL-U file

```python
from stanza.utils.conll import CoNLL

doc = CoNLL.conll2doc(input_file="sample.conllu", ignore_gapping=False)
print(len(doc.sentences), doc.num_tokens, doc.num_words)
print(doc.sentences[0].sent_id)
print(doc.sentences[0].comments)
```

Use `ignore_gapping=False` when you want to keep empty nodes for debugging.

## 2) Edit token, word, or sentence fields

```python
# token-level annotation
ner_tags = ["O", "S-PERSON", "O"]
doc.set("ner", ner_tags, to_token=True)

# word-level syntax or morphology
lemmas = ["be", "good", "dog"]
doc.set("lemma", lemmas)

# sentence-level metadata
sentiments = ["1", "0"]
doc.set("sentiment", sentiments, to_sentence=True)
```

Common setters that stay comment-safe:
- `sentence.sent_id`
- `sentence.doc_id`
- `sentence.speaker`
- `sentence.sentiment`
- `sentence.constituency`

If you update token NER tags and want entity spans, call `doc.build_ents()` afterward.

## 3) Work with multi-word tokens

```python
expansions = doc.get_mwt_expansions()
doc.set_mwt_expansions(expansions, fake_dependencies=True)
```

Use `doc.get_mwt_expansions(evaluation=True)` when you only want the source strings.
If you are handling manually expanded tokens, choose the matching `process_manual_expanded` mode instead of forcing every token through the same path.

## 4) Attach or inspect coreference

- assign a list of `CorefChain` objects to `doc.coref`
- inspect `word.coref_chains` on the words that participate in mentions
- remember that coref attachments are word-level, while the surface annotations may still live in token output

## 5) Write validated CoNLL-U back out

```python
from stanza.utils.conll import CoNLL

CoNLL.write_doc2conll(doc, "out.conllu")
print("{:C}".format(doc))
print("{:c-o}".format(doc))
```

- `{:C}` includes comments
- `{:c}` omits comments
- `-o` suppresses offsets

## 6) Split one file into multiple documents

```python
from stanza.utils.conll import CoNLL

docs = CoNLL.conll2multi_docs(input_file="multi_doc.conllu", ignore_gapping=False)
```

Use this when the file contains `# doc_id = ...` or `# newdoc id = ...` boundaries.

## 7) Diagnose a parse failure quickly

Run the bundled validator first:

```bash
python scripts/validate_conllu.py sample.conllu
cat sample.conllu | python scripts/validate_conllu.py -
```

The validator is read-only, keeps empty nodes by default, and reports sentence, token, word, and empty-node counts.

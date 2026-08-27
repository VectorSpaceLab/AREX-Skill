# Text-model data formats

## Core call rule

DeepPavlov model calls follow the `chainer.in` list exactly.

- Each positional argument to `model(...)` or each payload key in a serving context must match one item in `chainer.in`.
- Each argument is usually a batch: a list of samples, one item per example.
- Keep all batch arguments aligned by sample count.
- When a config has a single output, the caller may see a bare value or a 1-item container depending on the helper used; check the config's `chainer.out` names.

## Common input shapes

| Shape | Example family | Notes |
| --- | --- | --- |
| `x: list[str]` | one-text classification, NER, spelling, sentence segmentation | Most single-text configs use this shape. |
| `text_a`, `text_b` / `sentence1`, `sentence2` / `question`, `passage` | paired classifiers, SuperGLUE, relation-style classifiers | Keep the argument order exactly as written in `chainer.in`. |
| `contexts_list`, `choices_list` | multiple-choice classifiers and PARus | Each sample is itself a list of choices. |
| `idx`, `query`, `passage`, `entities`, `num_examples` | ReCoRD/RuCoS-style record tasks | Do not flatten the record fields; preserve per-sample grouping. |
| `tokens`, `entity_pos`, `entity_tags` | relation extraction | `entity_pos` holds token-span indices, grouped by entity and by sample. |
| `texts`, `dataset` | few-shot classification | The support dataset stays grouped with the query batch. |
| `x_words: list[list[str]]` | joint morpho/syntax parser | This is tokenized-word input, not raw text. |

## Family-by-family output shapes

### Classification and scoring

- One-text classifiers: `model(["Dummy text"]) -> labels`
- Pair classifiers: `model(["premise"], ["hypothesis"]) -> labels`
- Multiple-choice configs: `model([["choice 1", "choice 2"]], [["option A", "option B"]]) -> labels`
- Record-style configs: `model(["0"], ["query"], ["passage"], ["entity"], [1]) -> probabilities or labels`
- Few-shot configs: `model(["text"], [dataset]) -> labels`
- Regression configs: `model(["source"], ["hypothesis"]) -> scalar scores`

Representative `chainer.in` names to expect:

- `x`
- `text_a`, `text_b`
- `sentence1`, `sentence2`
- `question`, `passage`
- `contexts_list`, `choices_list`
- `idx`, `query`, `passage`, `entities`, `num_examples`
- `texts`, `dataset`
- `source`, `hypothesis`

### NER and sentence segmentation

- Base NER: `x -> x_tokens, y_pred`
- NER with probabilities: `x -> x_tokens, tokens_offsets, y_pred, probas`
- Sentence segmentation: `x -> x_tokens, punctuated_sents`

Notes:

- NER returns token lists and BIO tags.
- If you need offsets or probabilities, use the `_probas` NER config.
- Sentence segmentation expects a token sequence in the batch, not a raw sentence string.

### Entity detection, linking, and relation extraction

- Entity detection: `x -> entity_substr, entity_offsets, entity_positions, tags, sentences_offsets, sentences, probas`
- Entity extraction: `x -> entity_substr, tags, entity_offsets, entity_ids, entity_conf, entity_pages, entity_labels`
- Relation extraction: `tokens, entity_pos, entity_tags -> wikidata_relation_id, relation_name`

Notes:

- `entity_offsets` and `sentences_offsets` are character-span style offsets.
- `entity_pos` is span metadata in token coordinates; keep nested lists per sample.
- Entity extraction is a pipeline, so the final output names are produced by both detection and linking stages.

### Spelling correction

- `x -> y_predicted`

Notes:

- Inputs are raw strings.
- Internally the config lowercases, tokenizes, generates candidates, and chooses the best spelling sequence.

### Morpho-syntax parsing

- `x -> y_prettified`
- `x_words -> y_parsed`

Notes:

- The joint parser wrapper expects `x_words`.
- The BERT-based morpho and syntax configs accept raw text `x` and return pretty-printed parsed output.

### Multitask

- `chainer.in` and `chainer.out` are multi-slot lists; preserve the order exactly.
- Example family: `x_cola`, `x_rte`, `x_stsb`, `x_copa`, `x_conll`
- Outputs may mix ids, labels, probabilities, and regression values in one call.

Notes:

- A multitask batch is a batch of batches: each task input stays aligned with the others.
- Smaller task datasets may be padded with `None` values by the multitask iterator.
- Mixed-head configs often require custom metric wiring.

### Embeddings

- Full BERT embedder: `texts -> tokens, word_emb, subword_tokens, subword_emb, max_emb, mean_emb, pooler_output`
- Sentence BERT embedder: `texts -> max_emb, mean_emb, pooler_output`

Notes:

- `bert_embedder` exposes token-level, subtoken-level, and sentence-level representations.
- `bert_sentence_embedder` keeps only the sentence-level vectors.

## Safe adaptation pattern

When adapting a text model to new data:

1. Start from the exact `chainer.in` names in the selected config.
2. Update the reader or dataset files so the raw columns land in those names.
3. Keep the output names stable unless you are also updating every downstream component.
4. For classification CSV/JSON data, remember that the basic reader defaults to `text` and `labels` columns; override them in the reader config when your file uses different names.

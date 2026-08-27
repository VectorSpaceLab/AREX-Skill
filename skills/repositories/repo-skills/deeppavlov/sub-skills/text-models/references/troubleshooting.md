# Text-model troubleshooting

Use this page for failures specific to the text-model families in this sub-skill. For shared install/import/backend/cache issues, defer to the [root troubleshooting reference](../../../references/troubleshooting.md) when it exists in the generated skill tree.

## Start here

1. Run `scripts/list_config_categories.py` to confirm the live config family and exact config name.
2. Check `references/data-formats.md` for the exact `chainer.in` / `chainer.out` shape.
3. Check `references/model-catalog.md` for the expected family and dependency set.

## Symptom -> likely cause -> fix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError`, wrong argument count, or mismatched output unpacking | The call shape does not match `chainer.in` / `chainer.out` | Rebuild the call using the exact slot order from `references/data-formats.md`. |
| Batch-length mismatch | One argument has a different batch size than the others | Keep every positional batch aligned by sample count. |
| NER or segmentation output looks wrong | Raw text was used where the config expects tokenized input | Use the right family: raw-text NER, token-based sentence segmentation, or the joint parser's `x_words` input. |
| Entity extraction fails after detection | The linker assets, spaCy wheels, or Wikidata database are missing | Install the linker dependencies and make sure both detection and linking downloads are present. |
| Spelling correction import or runtime errors | Missing `kenlm`, `lxml`, `sortedcontainers`, or `sacremoses` | Install the spelling-correction dependency set and make sure the language-model files are on disk. |
| Morpho/syntax joint parsing complains about inputs | The joint wrapper expects `x_words`, not raw `x` | Tokenize first or use the raw-text morpho/syntax configs instead of the wrapper. |
| Multitask training or inference breaks on missing fields | Task order changed or a head was dropped | Keep the exact multitask input order, and preserve `None` padding semantics from the multitask iterator. |
| GLUE or SuperGLUE configs fail to load | Missing HuggingFace dataset support or transformer dependencies | Install the registry-mapped requirements for `datasets`, `pytorch`, and `transformers`. |
| Russian SuperGLUE submission is rejected or misnamed | The benchmark task metadata does not match the config | Set the task variable correctly and use `python -m deeppavlov.utils.benchmarks.superglue <config_name> -d`. |
| Embedding config returns a different number of arrays than expected | The wrong embedder variant was selected | Use `bert_embedder` for token/subtoken/sentence vectors and `bert_sentence_embedder` for sentence-only vectors. |
| You expected retrieval or ranking behavior | The task was routed to the wrong family | Switch to `../retrieval-qa/SKILL.md`. |

## Dependency reminders

- BERT-backed classifiers, taggers, relation extraction, multitask heads, and embedders usually need `pytorch.txt` and `transformers.txt`.
- GLUE, SuperGLUE, multitask, and regression configs often need `datasets.txt` because they use HuggingFace readers/iterators.
- Some NER and syntax configs add `torchcrf.txt`, `sentencepiece.txt`, and `protobuf.txt`.
- Entity linking needs `hdt.txt`, `rapidfuzz.txt`, and the spaCy small models.
- Spelling correction needs `kenlm.txt`, `lxml.txt`, `sortedcontainers.txt`, and sometimes `sacremoses.txt`.

## Download and size caveats

- Classification and tagging checkpoints are often large; some pretrained models are in the 1-2 GB range.
- `sentiment_twitter` is especially heavy.
- Spelling correction resources can be several GB.
- Entity linking uses database plus ranker assets and can be disk-heavy.
- The fastText pretrained vectors documented in the package are 300-dimensional and also sizable.

## When to reroute

- Config syntax, nested configs, registry imports, or custom components -> [pipelines](../../pipelines/SKILL.md)
- Retrieval, ranking, FAQ, SQuAD, ODQA, or KBQA -> [retrieval-qa](../../retrieval-qa/SKILL.md)
- REST or socket serving -> [serving](../../serving/SKILL.md)

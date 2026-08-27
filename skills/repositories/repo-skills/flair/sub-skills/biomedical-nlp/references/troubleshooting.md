# Biomedical NLP Troubleshooting

Use this reference for HunFlair/HunFlair2 NER, biomedical entity linking,
optional SciSpaCy and pyab3p routes, custom dictionaries, and biomedical corpus
offset issues.

## Model or dictionary unexpectedly downloads

Symptoms:

- `Classifier.load("hunflair2")`, `Classifier.load("hunflair")`, or
  `EntityMentionLinker.load("disease-linker")` stalls or tries network access.
- Built-in `load_dictionary("disease")` or `load_dictionary("gene")` fetches
  CTD, NCBI, or taxonomy data.

What to do:

1. Ask whether downloads are allowed. If not, use an already-cached local model
   path or an exact-match in-memory dictionary.
2. Set `FLAIR_CACHE_ROOT` to a writable cache before importing Flair if the
   default user cache is not appropriate.
3. Set `FLAIR_DEVICE=cpu` for the verified CPU baseline.
4. For no-download validation, run `../scripts/biomedical_smoke.py --run-local-linker`
   from this sub-skill directory or adapt the in-memory dictionary pattern in
   [entity-linking.md](entity-linking.md).

## SciSpaCy is missing or version-mismatched

Symptoms:

- `SciSpacyTokenizer()` or `SciSpacySentenceSplitter()` raises an import/model
  error.
- The error asks for SciSpaCy and an `en_core_sci_sm` model.

Cause:

- SciSpaCy and its model are optional. The public Flair package can run without
  them, but biomedical tokenization/splitting integrations require them.

Fallbacks:

```python
from flair.data import Sentence
from flair.splitter import SegtokSentenceSplitter

sentence = Sentence("TP53-mutant cells were treated with aspirin.")
sentences = SegtokSentenceSplitter().split("TP53-mutant cells were treated with aspirin. It changed viability.")
```

Only use SciSpaCy in production instructions after the environment has verified
both the Python package and the `en_core_sci_sm` model. Different SciSpaCy/model
versions can change tokenization and therefore offsets.

## pyab3p is missing

Symptoms:

- `Ab3PEntityPreprocessor(...)` raises `ImportError`.
- Loading a prebuilt linker warns that `pyab3p` is not found and switches to a
  `-no-ab3p` variant.

What to do:

- Treat pyab3p as optional/unverified unless explicitly installed and probed.
- For custom build paths, pass `BioSynEntityPreprocessor()` to avoid the Ab3P
  dependency:

```python
from flair.models.entity_mention_linking import BioSynEntityPreprocessor

preprocessor = BioSynEntityPreprocessor()
```

- If abbreviation expansion is required, verify pyab3p first, then use
  `Ab3PEntityPreprocessor(preprocessor=BioSynEntityPreprocessor())` and test on
  sentence-local definitions such as `Wrinkly skin syndrome (WSS)`.

## Linker adds no labels

Likely causes:

- NER was not run, so there are no spans for the linker to read.
- NER labels are on a different layer than the linker's configured
  `entity_label_types`.
- Entity values do not match the expected type filter, e.g. `Gene` vs `gene`, or
  a dataset-specific fine-grained label.
- Exact-match linking did not find the processed mention in the dictionary.

Debug pattern:

```python
print(sentence.annotation_layers.keys())
for layer in sentence.annotation_layers:
    print(layer, [str(label) for label in sentence.get_labels(layer)])

# Try an explicit read layer/type filter.
linker.predict(
    sentence,
    entity_label_types={"ner": {"Gene", "Disease", "Chemical", "Species"}},
    pred_label_type="debug-link",
)
```

For exact-string-match, inspect the dictionary names/synonyms and the processed
mention. `BioSynEntityPreprocessor` lowercases and removes punctuation, but it
cannot invent missing synonyms.

## NER labels and link labels are mixed together

Symptoms:

- `sentence.get_labels()` prints both entity types and concept IDs together.
- A downstream evaluator treats ontology IDs as NER classes.

Fix:

- Always use layer-specific access: `sentence.get_labels("ner")` for NER and
  `sentence.get_labels("link")` or a custom layer for NEN.
- Set `pred_label_type` when running multiple linkers:

```python
gene_linker.predict(sentence, pred_label_type="gene-link")
disease_linker.predict(sentence, pred_label_type="disease-link")
```

- Do not train a NER model on a linking layer. NER labels and ontology IDs have
  different semantics.

## Legacy HunFlair v1 layer mismatch

Symptoms:

- Linking works with HunFlair2 but not with `Classifier.load("hunflair")` or an
  entity-specific legacy tagger.
- A warning says HunFlair v1 has labels like `diseases`, `genes`, `species`, or
  `chemical` instead of `ner`.

Fix:

1. Prefer HunFlair2 for new tasks.
2. If legacy compatibility is required, inspect layers and pass
   `entity_label_types` explicitly.
3. For an entity-specific legacy model predicted into a custom layer, pass that
   custom layer:

```python
legacy_tagger.predict(sentence, label_name="my-diseases")
disease_linker.predict(sentence, entity_label_types="my-diseases", pred_label_type="disease-link")
```

## Custom dictionary loading fails

Symptoms:

- `load_dictionary(path)` raises `ValueError` about `dataset_name`.
- A Huner dictionary file assertion fails on line format.

Rules:

- Built-in names such as `disease`, `chemical`, `gene`, `species`,
  `ctd-diseases`, `ctd-chemicals`, `ncbi-gene`, and `ncbi-taxonomy` can be
  loaded by name.
- Custom path dictionaries require `dataset_name`.
- Huner dictionary files use one concept per line in this format:

```text
concept_id||concept_name
concept_id|alternate_id||concept_name
```

For small custom dictionaries, prefer an `InMemoryEntityLinkingDictionary` built
from `EntityCandidate` objects so synonyms and additional IDs are explicit.

## Custom semantic linker build fails

Common causes:

- A saved linker was passed to `build()` instead of `EntityMentionLinker.load()`.
- A custom transformer/model string was not a supported entity-type key,
  built-in model key, or resolvable Hugging Face identifier.
- `hybrid_search=True` was requested for a model/entity combination that does
  not have a pretrained hybrid setup, and `entity_type` was omitted.
- The default build preprocessor tried to instantiate Ab3P while pyab3p was not
  installed.
- The dictionary was omitted for a custom model where Flair cannot infer one.

Safer starting points:

```python
from flair.models import EntityMentionLinker
from flair.models.entity_mention_linking import BioSynEntityPreprocessor

# Build a new no-download exact matcher or a semantic linker with a supported model id.
linker = EntityMentionLinker.build(
    "exact-string-match",
    dictionary=my_dictionary,
    dataset_name="MY-KB",
    entity_type="disease",
    hybrid_search=False,
    preprocessor=BioSynEntityPreprocessor(),
)

# Load an already-saved linker file instead of rebuilding it.
linker = EntityMentionLinker.load("path/to/saved-linker.pt")
```

## Cell-line linking expectation mismatch

Symptoms:

- A user expects `cell-line-linker` or `cellline-linker` to exist because
  HunFlair2 NER detects `CellLine` mentions.

Fix:

- Built-in linker shortcuts verified for this skill are gene, disease, chemical,
  and species. For cell-line normalization, create a custom dictionary and use a
  custom exact-match or semantic linker.
- Keep the NER `CellLine` labels on `ner` and write normalization output to a
  custom layer such as `cell-line-link`.

## Biomedical corpus offset problems

Symptoms:

- Converted CoNLL tags are shifted by one or more characters.
- A multi-token entity is split incorrectly.
- Nested entities disappear.

Checklist:

1. Verify source offsets are half-open `(start, end)` spans against the raw text:
   `text[start:end]` must match the annotation mention after any intended text
   cleanup.
2. Normalize unusual spaces consistently before conversion. The biomedical writer
   replaces several Unicode space characters and non-breaking spaces.
3. Keep tokenization stable. Switching SciSpaCy, SegTok, or space tokenization
   changes token boundaries and may alter BIO labels.
4. Expect nested/overlapping entities to be filtered for single-layer BIO output.
   If preserving nested entities is required, plan separate layers or a task
   formulation that can represent overlaps.
5. Do not use corpus downloads as a quick smoke check in constrained settings;
   many corpus classes fetch external archives or BigBio datasets on first use.

## Device and optional runtime confusion

- CPU is the baseline. Use `FLAIR_DEVICE=cpu` unless the user explicitly wants
  CUDA and the environment has been checked.
- ONNX/provider runtime acceleration is not part of the verified biomedical
  baseline. Route provider/export questions to embeddings/optimization.
- Large transformer/linker builds can allocate significant RAM during dictionary
  indexing. Reduce `batch_size` or use exact-match/custom dictionary checks for
  small deterministic tests.

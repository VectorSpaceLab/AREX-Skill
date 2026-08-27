# Biomedical Entity Linking and Normalization

Entity linking / normalization (NEN) maps a detected biomedical mention to a
knowledge-base concept identifier. In Flair this is separate from NER: NER finds
spans and their entity types, while `EntityMentionLinker` adds concept labels to
those spans.

## Core APIs

Installed signatures summarized for Flair 0.15.1:

```python
EntityMentionLinker.load(model_path)

EntityMentionLinker.build(
    model_name_or_path: str,
    label_type: str = "link",
    dictionary_name_or_path = None,
    hybrid_search: bool = True,
    batch_size: int = 128,
    similarity_metric = SimilarityMetric.INNER_PRODUCT,
    preprocessor = None,
    sparse_weight: float = 0.5,
    entity_type: str | None = None,
    dictionary = None,
    dataset_name: str | None = None,
)

EntityMentionLinker.predict(
    sentences,
    top_k: int = 1,
    pred_label_type: str | None = None,
    entity_label_types: str | Sequence[str] | dict[str, set[str]] | None = None,
    batch_size: int | None = None,
)
```

`SpanClassifier` in `flair.models.entity_linker_model` is a different, older
span classification/linking model family. For HunFlair2 biomedical entity
normalization, prefer `EntityMentionLinker` unless a task explicitly uses a saved
`SpanClassifier`/`EntityLinker` model.

## Built-in biomedical linkers and dictionaries

Preconfigured linker names:

| Entity type | Linker key | Default dictionary / KB |
| --- | --- | --- |
| Gene | `gene-linker` | NCBI Gene, human-focused |
| Disease | `disease-linker` | CTD Diseases |
| Chemical | `chemical-linker` | CTD Chemicals |
| Species | `species-linker` | NCBI Taxonomy |

The loader also recognizes `*-no-ab3p` variants. Built-in dictionaries can be
loaded by type or dictionary name:

```python
from flair.models.entity_mention_linking import load_dictionary

disease_dict = load_dictionary("disease")        # maps to ctd-diseases
chemical_dict = load_dictionary("chemical")      # maps to ctd-chemicals
gene_dict = load_dictionary("gene")              # maps to ncbi-gene
species_dict = load_dictionary("species")        # maps to ncbi-taxonomy
```

Dictionary downloads are data downloads. Do not call built-in dictionary loaders
in a no-network/no-download path unless the cache is known to be populated.

There is no built-in shortcut in the verified API facts for cell-line
normalization. If a user needs cell-line linking, build a custom dictionary and
linker, then set `entity_type` and `entity_label_types` deliberately.

## End-to-end NER then linking

```python
import os
os.environ.setdefault("FLAIR_DEVICE", "cpu")

from flair.data import Sentence
from flair.models import EntityMentionLinker
from flair.nn import Classifier

sentence = Sentence(
    "The mutation in the ABCD1 gene causes X-linked adrenoleukodystrophy, "
    "which can be exacerbated by mercury exposure in mouse populations."
)

ner = Classifier.load("hunflair2")       # may download
ner.predict(sentence)

for linker_name in ["gene-linker", "disease-linker", "chemical-linker", "species-linker"]:
    linker = EntityMentionLinker.load(linker_name)  # may download linker/dictionary/index files
    linker.predict(sentence, pred_label_type="link")

for link in sentence.get_labels("link"):
    span = link.data_point
    print(span.text, link.value, link.metadata.get("name"), link.score)
```

The similarity scores are model- and dictionary-specific. Compare scores only
within the same linker/dictionary setup.

For candidate exploration, pass `top_k` and read labels from the span, not from a
sentence-level summary. The first label is the best-ranked candidate for that
linker call:

```python
linker.predict(sentence, top_k=5, pred_label_type="disease-link")

for span in sentence.get_spans("ner"):
    candidates = [
        {"id": label.value, "name": label.metadata.get("name"), "score": label.score}
        for label in span.get_labels("disease-link")
    ]
    if candidates:
        print(span.text, candidates[0], candidates)
```

## Label-layer separation

Default linkers are configured to read NER spans from `{'ner': {'gene'}}`,
`{'ner': {'disease'}}`, and similar layer/type filters. They write to `link` by
default. Use `pred_label_type` to avoid mixing outputs:

```python
gene_linker.predict(sentence, pred_label_type="gene-link")
disease_linker.predict(sentence, pred_label_type="disease-link")

for label in sentence.get_labels("ner"):
    print("NER", label.data_point.text, label.value)
for label in sentence.get_labels("gene-link"):
    print("GENE", label.data_point.text, label.value, label.metadata.get("name"))
```

Use `entity_label_types` when the input mentions are not on the default `ner`
layer or when you need a type subset:

```python
# Read all labels on a custom layer
linker.predict(sentence, entity_label_types="my-ner", pred_label_type="my-links")

# Read only selected entity values from a layer
linker.predict(
    sentence,
    entity_label_types={"ner": {"Gene", "protein", "genes"}},
    pred_label_type="gene-link",
)
```

The linker normalizes plural legacy values such as `genes` and `diseases` to
singular internal types. Legacy HunFlair v1 models may write layers such as
`diseases`, `genes`, `species`, or `chemical` instead of a single `ner` layer;
inspect `sentence.annotation_layers` and pass `entity_label_types` explicitly.

## No-download exact-match linking with in-memory dictionaries

For offline tests, demos, and deterministic unit checks, use exact-match
candidate generation with tiny in-memory dictionaries. This avoids pretrained
model downloads and avoids built-in dictionary downloads. Prefer one linker per
entity type so type filters and output layers remain obvious.

```python
from flair.data import EntityCandidate, Sentence
from flair.datasets.entity_linking import InMemoryEntityLinkingDictionary
from flair.models import EntityMentionLinker
from flair.models.entity_mention_linking import BioSynEntityPreprocessor

# Mention source: normally this comes from NER. Here we create it manually.
sentence = Sentence("TP53 interacts with breast cancer")
sentence[0:1].add_label("ner", "Gene")
sentence[3:5].add_label("ner", "Disease")

preprocessor = BioSynEntityPreprocessor()  # no pyab3p dependency

gene_dictionary = InMemoryEntityLinkingDictionary(
    candidates=[
        EntityCandidate(
            concept_id="7157",
            concept_name="TP53",
            database_name="DEMO",
            synonyms=["tumor protein p53", "TRP53"],
        ),
    ],
    dataset_name="DEMO-GENE",
)
gene_linker = EntityMentionLinker.build(
    "exact-string-match",
    dictionary=gene_dictionary,
    dataset_name="DEMO-GENE",
    entity_type="gene",
    hybrid_search=False,
    label_type="gene-link",
    preprocessor=preprocessor,
)

disease_dictionary = InMemoryEntityLinkingDictionary(
    candidates=[
        EntityCandidate(
            concept_id="MESH:D001943",
            concept_name="Breast Neoplasms",
            database_name="DEMO",
            synonyms=["breast cancer"],
        ),
    ],
    dataset_name="DEMO-DISEASE",
)
disease_linker = EntityMentionLinker.build(
    "exact-string-match",
    dictionary=disease_dictionary,
    dataset_name="DEMO-DISEASE",
    entity_type="disease",
    hybrid_search=False,
    label_type="disease-link",
    preprocessor=preprocessor,
)

gene_linker.predict(
    sentence,
    entity_label_types={"ner": {"Gene"}},
    pred_label_type="gene-link",
    top_k=1,
)
disease_linker.predict(
    sentence,
    entity_label_types={"ner": {"Disease"}},
    pred_label_type="disease-link",
    top_k=1,
)

for layer in ["gene-link", "disease-link"]:
    for link in sentence.get_labels(layer):
        print(layer, link.data_point.text, link.value, link.metadata.get("name"), link.score)
```

Exact match applies the configured preprocessor to both dictionary names/synonyms
and mention text. If a mention has no exact processed match, no link label is
added. You can deliberately use a single dictionary/linker for mixed entity
prototypes, but then document the `entity_type`, read filter, and output layer
because built-in linkers normally assume type-specific mention filters.

## Building semantic/custom linkers

`EntityMentionLinker.build()` can build semantic dense or hybrid linkers with a
transformer document embedding model:

```python
from flair.models import EntityMentionLinker
from flair.models.entity_mention_linking import BioSynEntityPreprocessor

linker = EntityMentionLinker.build(
    "cambridgeltl/SapBERT-from-PubMedBERT-fulltext",  # may download
    dictionary=my_dictionary,
    dataset_name="MY-KB",
    entity_type="disease",
    hybrid_search=False,
    preprocessor=BioSynEntityPreprocessor(),
)
```

Important constraints:

- `build()` is safest with built-in entity-type keys, built-in model keys, or
  Hugging Face model identifier strings. Local-path behavior for building a new
  semantic linker is not part of the verified baseline; if you have a saved
  linker file, use `EntityMentionLinker.load(local_path)` and test it directly.
- `hybrid_search=True` uses dense embeddings plus character n-gram TF-IDF. For
  custom or non-hybrid models, specify `entity_type`; otherwise the builder may
  not know which entity type it is linking.
- The default preprocessor in `build()` is abbreviation-aware and requires
  pyab3p. If pyab3p is not verified, pass `BioSynEntityPreprocessor()` or an
  explicit custom `EntityPreprocessor`.
- `EntityMentionLinker` itself is not trainable; its `forward_loss()` raises
  `NotImplementedError`. Build or load a linker rather than trying to fine-tune
  it.

## Custom dictionaries

For line-based Huner dictionaries, each non-empty line must contain `||`:

```text
concept_id||concept_name
concept_id|alternate_id||concept_name
```

Load them with a dataset name:

```python
from pathlib import Path
from flair.models.entity_mention_linking import load_dictionary

dictionary = load_dictionary(Path("my-dictionary.txt"), dataset_name="MY-KB")
```

For programmatic dictionaries, prefer `InMemoryEntityLinkingDictionary` built
from `EntityCandidate` objects so canonical names, synonyms, and additional IDs
are explicit.

Custom linker plan:

1. Decide the mention source layer, for example `ner` or `my-ner`.
2. Normalize entity values to the linker filter, for example `Gene`, `Disease`,
   `Chemical`, `Species`, or a custom cell-line value.
3. Build a small `InMemoryEntityLinkingDictionary` first and validate exact
   matches with `model_name_or_path="exact-string-match"`.
4. Only after the dictionary and label layers are correct, move to a semantic
   model identifier or a saved linker, and document any model downloads.
5. Write links into a distinct layer such as `disease-link`, `gene-link`, or
   `cell-line-link`; do not reuse the NER layer.

## Abbreviation resolution and pyab3p fallback

Flair has two relevant preprocessors:

- `BioSynEntityPreprocessor`: lowercases, removes punctuation, and avoids empty
  processed strings. It has no pyab3p dependency.
- `Ab3PEntityPreprocessor`: wraps another preprocessor and resolves sentence-
  local biomedical abbreviations such as `WSS` from definitions like
  `Wrinkly skin syndrome (WSS)`. It requires `pyab3p`.

Prebuilt linker keys such as `disease-linker` may switch to a `-no-ab3p` model
variant when pyab3p is missing. Custom `EntityMentionLinker.build()` does not
silently avoid that dependency unless you pass a non-Ab3P preprocessor.

```python
from flair.models.entity_mention_linking import BioSynEntityPreprocessor

linker = EntityMentionLinker.build(
    "exact-string-match",
    dictionary=my_dictionary,
    dataset_name="MY-KB",
    entity_type="disease",
    hybrid_search=False,
    preprocessor=BioSynEntityPreprocessor(),
)
```

Use abbreviation-aware behavior only after pyab3p is installed and verified:

```python
from flair.models.entity_mention_linking import Ab3PEntityPreprocessor, BioSynEntityPreprocessor

preprocessor = Ab3PEntityPreprocessor(preprocessor=BioSynEntityPreprocessor())
```

## Evaluation notes

`EntityMentionLinker.evaluate(data_points, gold_label_type, k=1, ...)` predicts
into a temporary `predicted` layer and computes top-k matching against labels on
`gold_label_type`. It expects gold labels on spans, not separate unaligned
sentence-level labels.

For application checks, prefer assertions on:

- the expected NER layer exists before linking;
- only the intended entity types were read by the linker;
- link labels are attached to the same spans as NER labels;
- the link output layer is separate from the NER layer;
- each predicted link value belongs to the expected dictionary namespace.

# HunFlair and Biomedical Corpus Workflows

This reference covers biomedical NER, biomedical tokenization/splitting, and
biomedical corpus preparation with the public, pip-installed `flair` package. It
is self-contained and does not require opening a local development tree.

## Choosing a biomedical NER route

| Need | Flair route | Notes |
| --- | --- | --- |
| Current biomedical NER across diseases, genes/proteins, species, chemicals, and cell lines | `Classifier.load("hunflair2")` | Preferred route for new work. It may download a pretrained model unless already cached. |
| Legacy HunFlair v1 behavior | `Classifier.load("hunflair")` or entity-specific `SequenceTagger.load("hunflair-disease")`, `"hunflair-gene"`, `"hunflair-chemical"`, `"hunflair-species"`, `"hunflair-cellline"` | Legacy route is supported for compatibility, but layer names can differ from HunFlair2. |
| Custom biomedical NER training or fine-tuning | Biomedical corpus classes plus `SequenceTagger`, `PrefixedSequenceTagger`, and `ModelTrainer` | Use this reference for biomedical data choices and caveats; use `training-and-datasets` for trainer details. |
| Entity normalization / ontology IDs | NER first, then `EntityMentionLinker` | Linking is separate from NER and writes to a linking label layer. See [entity-linking.md](entity-linking.md). |

CPU baseline for NER:

```python
import os
os.environ.setdefault("FLAIR_DEVICE", "cpu")

from flair.data import Sentence
from flair.nn import Classifier

sentence = Sentence("Behavioral abnormalities in the Fmr1 KO2 Mouse Model of Fragile X Syndrome")
tagger = Classifier.load("hunflair2")  # may download if not cached
tagger.predict(sentence)

for label in sentence.get_labels("ner"):
    span = label.data_point
    print(span.text, span.start_position, span.end_position, label.value, label.score)
```

For HunFlair2, use the `ner` layer unless a model or prediction call documents
otherwise. For legacy HunFlair v1, inspect layers before assuming the input to a
linker:

```python
print(sentence.annotation_layers.keys())
for layer in sentence.annotation_layers:
    print(layer, sentence.get_labels(layer))
```

## NER is not linking

A biomedical NER label says what text span is a mention and what type it has:
`Disease`, `Gene`, `Species`, `Chemical`, or `CellLine`. A linking label says
which ontology/dictionary concept a mention maps to. Keep these layers separate:

```python
# NER layer: mention type
for ner_label in sentence.get_labels("ner"):
    print(ner_label.data_point.text, ner_label.value)

# Linking layer: ontology or KB concept identifier, added later by a linker
for link_label in sentence.get_labels("link"):
    print(link_label.data_point.text, link_label.value, link_label.metadata)
```

Use custom output layers, for example `gene-link` and `disease-link`, when a
workflow needs type-specific normalization outputs or wants to avoid mixing
candidates from multiple linkers in one `link` layer.

## Biomedical tokenization and sentence splitting

Default Flair tokenization is safe and requires no biomedical extras. Biomedical
text often benefits from SciSpaCy, but SciSpaCy is optional and unverified unless
installed and probed in the active environment.

Optional SciSpaCy route:

```python
from flair.data import Sentence
from flair.tokenization import SciSpacyTokenizer
from flair.splitter import SciSpacySentenceSplitter

sentence = Sentence(
    "Fragile X syndrome (FXS) involves FMR1.",
    use_tokenizer=SciSpacyTokenizer(),  # requires scispacy + en_core_sci_sm
)

splitter = SciSpacySentenceSplitter()  # also requires scispacy + en_core_sci_sm
sentences = splitter.split("Fragile X syndrome (FXS) involves FMR1. FXS is inherited.")
```

Fallback route when SciSpaCy is not available:

```python
from flair.data import Sentence
from flair.splitter import SegtokSentenceSplitter

sentence = Sentence("Fragile X syndrome (FXS) involves FMR1.")
sentences = SegtokSentenceSplitter().split("Fragile X syndrome (FXS) involves FMR1. FXS is inherited.")
```

When offsets matter, always inspect `start_position` and `end_position` after
choosing tokenization. A different tokenizer can change whether a model sees a
mention as one token, multiple tokens, or a punctuation-separated sequence.

## Long abstracts and full text

For an abstract or full-text chunk:

1. Split into `Sentence` objects with the chosen splitter.
2. Predict NER over the list in batches.
3. Preserve each sentence's `start_position` if you need document-level offsets.
4. Link only after NER labels exist.

```python
from flair.nn import Classifier
from flair.splitter import SegtokSentenceSplitter

abstract = (
    "Fragile X syndrome (FXS) is caused by a mutation in FMR1. "
    "FXS patients may present behavioral abnormalities."
)
sentences = SegtokSentenceSplitter().split(abstract)

tagger = Classifier.load("hunflair2")  # may download
tagger.predict(sentences, mini_batch_size=8)

for sent in sentences:
    for label in sent.get_labels("ner"):
        span = label.data_point
        print(sent.start_position + span.start_position, sent.start_position + span.end_position, span.text, label.value)
```

## Biomedical corpus families

Flair exposes many biomedical NER corpora under `flair.datasets.biomedical` and
also re-exports common datasets through `flair.datasets`. The important families
are:

- HUNER entity-specific multi-corpora: `HUNER_CELL_LINE`, `HUNER_CHEMICAL`,
  `HUNER_DISEASE`, `HUNER_GENE`, `HUNER_SPECIES`.
- HUNER single or all-entity corpora such as `HUNER_ALL_CDR`,
  `HUNER_DISEASE_NCBI`, `HUNER_SPECIES_LINNEAUS`, `HUNER_GENE_BC2GM`,
  `HUNER_CHEMICAL_CHEMDNER`, `HUNER_ALL_BIORED`, `HUNER_GENE_NLM_GENE`,
  `HUNER_GENE_GNORMPLUS`, and `HUNER_CHEMICAL_NLM_CHEM`.
- BioBERT-style evaluation split corpora such as `BIOBERT_DISEASE_NCBI`,
  `BIOBERT_DISEASE_BC5CDR`, `BIOBERT_CHEMICAL_BC5CDR`,
  `BIOBERT_GENE_BC2GM`, `BIOBERT_GENE_JNLPBA`, `BIOBERT_SPECIES_LINNAEUS`,
  and `BIOBERT_SPECIES_S800`.
- BigBio-backed HUNER corpora derive from a `BIGBIO_NER_CORPUS` adapter and may
  require the `datasets` package plus network/cache access unless pre-cached.

Common canonical entity tags in the biomedical module are:

```python
CELL_LINE_TAG = "CellLine"
CHEMICAL_TAG = "Chemical"
DISEASE_TAG = "Disease"
GENE_TAG = "Gene"
SPECIES_TAG = "Species"
```

Do not assume every upstream dataset uses these exact strings. Biomedical
adapters often map dataset-specific names such as `gene_or_gene_product`,
`chemicalentity`, `diseaseorphenotypicfeature`, `organismtaxon`, `cell_line`, or
`protein` to canonical HunFlair labels.

## Offsets, nested entities, and CoNLL conversion

Biomedical source corpora frequently begin as BioC, BRAT, PubTator, BigBio, XML,
or custom tabular annotations. Flair's biomedical conversion path represents
entities internally as character spans, then writes CoNLL rows with a token, a
BIO-style `ner` tag, and often a whitespace-after column.

Key caveats:

- Character offsets are half-open spans: start inclusive, end exclusive.
- `CoNLLWriter` aligns entity spans to the tokenization selected by the sentence
  splitter. Changing SciSpaCy vs SegTok vs space tokenization can change emitted
  labels.
- Nested or overlapping entities cannot be represented faithfully in one BIO
  sequence. The biomedical writer applies a nested-entity filter before writing,
  keeping an independent set of intervals and warning when entities are removed.
- Some dataset converters repair small offset mismatches or strip unusual
  whitespace. Recheck example text slices before trusting custom conversion.

Minimal no-download conversion pattern for a tiny in-memory dataset:

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from flair.datasets.biomedical import CoNLLWriter, Entity, InternalBioNerDataset
from flair.splitter import NoSentenceSplitter
from flair.tokenization import SpaceTokenizer

text = "TP53 regulates breast cancer"
dataset = InternalBioNerDataset(
    documents={"doc1": text},
    entities_per_document={
        "doc1": [
            Entity((text.index("TP53"), text.index("TP53") + len("TP53")), "Gene"),
            Entity((text.index("breast cancer"), text.index("breast cancer") + len("breast cancer")), "Disease"),
        ]
    },
    entity_types=["Gene", "Disease"],
)

with TemporaryDirectory() as tmp:
    out = Path(tmp) / "tiny.conll"
    writer = CoNLLWriter(NoSentenceSplitter(tokenizer=SpaceTokenizer()))
    writer.write_to_conll(dataset, out)
    print(out.read_text())
```

Use this only for small local construction checks. For training on real corpora,
prefer the packaged corpus classes and route trainer configuration to the
training/datasets sub-skill.

## Custom biomedical NER planning

For a custom biomedical NER model:

1. Decide whether the model predicts one entity type or multiple entity types.
2. Build a corpus with `ner` labels and a label dictionary:
   `corpus.make_label_dictionary(label_type="ner", add_unk=False)` for a closed
   NER label set.
3. For multi-entity biomedical models, consider `PrefixedSequenceTagger` with
   `EntityTypeTaskPromptAugmentationStrategy` so entity-type prompts can combine
   corpora with different entity subsets.
4. Use biomedical or scientific transformers only after checking model download,
   device, and cache constraints.
5. Keep future linking separate: train NER labels on `ner`, then normalize
   predicted spans with an `EntityMentionLinker` into a linking layer.

See the training/datasets and embeddings/optimization sub-skills for actual
`SequenceTagger`, `PrefixedSequenceTagger`, `TransformerWordEmbeddings`, and
`ModelTrainer` recipes.

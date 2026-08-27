# Workflows

## Purpose

Use this when you need to load, build, or query a scispaCy linker.

## 1) Add a built-in linker to a spaCy pipeline

```python
import spacy
import scispacy.abbreviation
from scispacy.linking import EntityLinker

nlp = spacy.load("en_core_sci_sm")
nlp.add_pipe("abbreviation_detector")
nlp.add_pipe(
    "scispacy_linker",
    config={"resolve_abbreviations": True, "linker_name": "umls"},
)
```

Use `linker_name` values from the built-in set:

- `umls`
- `mesh`
- `go`
- `hpo`
- `rxnorm`

This is the standard path when the request is about biomedical mention linking rather than custom KB construction.

## 2) Build a custom linker from a local KB

```python
from scispacy.linking_utils import KnowledgeBase
from scispacy.candidate_generation import create_tfidf_ann_index, CandidateGenerator
from scispacy.linking import EntityLinker

kb = KnowledgeBase("/path/to/kb.jsonl")
concept_aliases, tfidf_vectorizer, ann_index = create_tfidf_ann_index("/tmp/linker-index", kb)
linker = EntityLinker.from_kb(kb, ann_index_out_dir="/tmp/linker-index")
```

Notes:

- If you only need a smoke test or a one-off build, pass `out_path=None` to keep the ANN artifacts in memory.
- The `out_path` directory stores the vectorizer, ANN index, sparse vectors, and alias mapping.
- `EntityLinker.from_kb` is the easiest path when you already have a fully prepared KB object.

## 3) Query candidates directly

Use `CandidateGenerator` when you want to inspect the raw candidates before the linker thresholding step.

```python
candidates = CandidateGenerator(ann_index, tfidf_vectorizer, concept_aliases, kb)
print(candidates(["Dipalmitoylphosphatidylcholine"], 10))
```

## 4) Work with UMLS utilities

The UMLS helpers are used when converting raw UMLS files into a JSON/JSONL KB or when loading the semantic type tree from the UMLS TSV export.

Typical path:

1. Read `MRCONSO.RRF` into `concept_details`.
2. Read `MRSTY.RRF` and `MRDEF.RRF` into the same dictionary.
3. Convert the resulting records into JSONL or pass them directly into `KnowledgeBase`.

## 5) End-to-end smoke

The bundled `scripts/smoke_scispacy.py --mode linker` command builds a tiny KB in memory, constructs the ANN index, and checks that candidate generation returns results.

Use that smoke before launching a large KB build or a remote download.

## When to stop and check troubleshooting

Read the troubleshooting reference if you see:

- a missing `nmslib`/`scipy`/`scikit-learn` dependency,
- a warning about CPU instructions,
- an empty or useless candidate set from a tiny KB,
- a cache or download failure,
- or `resolve_abbreviations=True` not taking effect.

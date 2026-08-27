# BEIR Generation Workflows

Use these workflows to reason about BEIR generation without requiring real model downloads. Real `QGenModel` and `TILDE` runs can be expensive and may require model downloads, network access, GPU memory, and optional dependencies.

## Offline Smoke Check

Run the bundled helper before modifying generation logic or diagnosing layout assumptions:

```bash
python scripts/generation_smoke.py
```

It uses fake model objects and verifies three generated files:

```text
<output>/
  gen-queries.jsonl
  gen-qrels/
    train.tsv
  gen-corpus.jsonl
```

Use `--keep-output` to inspect the generated fixture:

```bash
python scripts/generation_smoke.py --keep-output beir-generation-smoke-output
```

## Generate Synthetic Queries and Qrels

```python
from beir.datasets.data_loader import GenericDataLoader
from beir.generation import QueryGenerator
from beir.generation.models import QGenModel

corpus = GenericDataLoader("dataset").load_corpus()
model = QGenModel("BeIR/query-gen-msmarco-t5-base-v1")
generator = QueryGenerator(model=model)

generator.generate(
    corpus=corpus,
    output_dir="dataset",
    ques_per_passage=3,
    prefix="gen",
    batch_size=64,
)
```

Expected generated files:

```text
dataset/gen-queries.jsonl
dataset/gen-qrels/train.tsv
```

`ques_per_passage` controls how many raw sequences the model must return per document. Higher values can improve diversity but can also produce duplicates. BEIR de-duplicates only within each source passage, so the final number of saved queries can be smaller than `len(corpus) * ques_per_passage` even when the model returned the required raw count.

## Load Generated Query Data

Route schema validation and loading details to data-loading. The core loading pattern is:

```python
from beir.datasets.data_loader import GenericDataLoader

corpus, gen_queries, gen_qrels = GenericDataLoader(
    data_folder="dataset",
    prefix="gen",
).load(split="train")
```

Prefix mode means:

- query file: `gen-queries.jsonl`
- qrels folder: `gen-qrels/`
- split file: `gen-qrels/train.tsv`
- corpus file: still `corpus.jsonl`

If the user generated an expanded corpus with `PassageExpansion`, pass `corpus_file="gen-corpus.jsonl"` explicitly or rename/copy the expanded corpus intentionally.

## Generate Passage Expansions

```python
from beir.datasets.data_loader import GenericDataLoader
from beir.generation import PassageExpansion
from beir.generation.models import TILDE

corpus = GenericDataLoader("dataset").load_corpus()
expander = PassageExpansion(model=TILDE("ielab/TILDE"))

expander.expand(
    corpus=corpus,
    output_dir="dataset",
    prefix="tilde-exp",
    top_k=200,
    max_length=350,
    batch_size=64,
)
```

Expected generated file:

```text
dataset/tilde-exp-corpus.jsonl
```

The expanded corpus preserves document ids and titles. Each text becomes the original document text plus the separator and generated expansion terms. Use a custom `sep` if downstream tokenization needs a delimiter other than a single space.

## Use a Custom No-Download Model

A query generator model can be any object that returns exactly `len(corpus) * ques_per_passage` strings for each batch:

```python
class MyQueryModel:
    def generate(self, corpus, ques_per_passage, max_length, top_p, top_k):
        queries = []
        for doc in corpus:
            base = doc.get("title") or doc.get("text") or "document"
            for index in range(ques_per_passage):
                queries.append(f"synthetic question {index + 1} about {base}?")
        return queries
```

An expansion model can be any object that returns one expansion string for each input document:

```python
class MyExpansionModel:
    def generate(self, corpus, max_length, top_k):
        return ["expanded terms" for _ in corpus]
```

Use this protocol for unit tests and for adapters around API models, local inference servers, or non-Transformers generators. Keep API credentials and network-only setup outside bundled smoke tests.

## Multi-Process Query Generation

Use multi-process generation only for large query generation jobs. The BEIR example pattern is:

```python
from beir.generation import QueryGenerator
from beir.generation.models import QGenModel

if __name__ == "__main__":
    model = QGenModel("BeIR/query-gen-msmarco-t5-base-v1")
    pool = model.start_multi_process_pool(target_devices=["cuda:0", "cuda:1"])
    try:
        QueryGenerator(model=model).generate_multi_process(
            corpus=corpus,
            pool=pool,
            output_dir="dataset",
            ques_per_passage=3,
            prefix="gen-3",
            batch_size=64,
            chunk_size=5000,
        )
    finally:
        model.stop_multi_process_pool(pool)
```

Important operational details:

- Protect multi-process code with `if __name__ == "__main__":` because PyTorch uses spawn-style workers.
- `start_multi_process_pool()` returns a dictionary with `input`, `output`, and `processes` keys for `QGenModel`.
- If `target_devices` is omitted, BEIR uses all CUDA devices or four CPU workers when CUDA is unavailable.
- `chunk_size=None` lets `QGenModel` choose `min(ceil(len(corpus) / len(pool["processes"]) / 10), 5000)`.
- Always stop the pool in a `finally` block for long-running scripts.

## Generation Then Training Boundary

A common BEIR loop is:

1. Generate synthetic queries and `gen-qrels/train.tsv` with this sub-skill.
2. Load them with data-loading using `GenericDataLoader(data_folder=..., prefix="gen").load(split="train")`.
3. Route model fine-tuning to the training sub-skill.
4. Route first-stage retrieval and metrics to retrieval-evaluation.

Do not treat this sub-skill as owning dense encoder fine-tuning or metric interpretation. It owns the generated dataset layout and generation model protocol.

## Real-Model Run Checklist

Before running real `QGenModel` or `TILDE` generation, check:

- The dataset has a valid BEIR `corpus.jsonl`; query generation only needs corpus loading.
- The output prefix does not collide with existing generated files unless overwriting is intended.
- Model downloads and Hugging Face cache access are allowed.
- GPU/CPU memory and runtime are acceptable for the corpus size, `batch_size`, and `ques_per_passage`.
- `nltk` stopwords are available for `TILDE`.
- Multi-process scripts are guarded and pool cleanup is guaranteed.

## Provenance Notes

The source examples demonstrate real model downloads, dataset downloads, multi-GPU generation, TILDE passage expansion, and training on generated data. This sub-skill adapts their output-layout and API patterns into self-contained docs plus a fake-model smoke helper; it does not bundle download-heavy real-model scripts.

---
name: training-and-datasets
description: "Routes Flair corpus loading, label dictionaries, model training
  and fine-tuning, checkpoints, storage modes, TARS, multitask, and safe NER CLI
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Flair Training and Datasets

Use this sub-skill when a task needs custom corpora, label dictionaries, trainable Flair model construction, trainer configuration, output/checkpoint planning, or a safe NER fine-tuning preflight with the public pip-installed `flair` package. The verified baseline is CPU execution against installed Flair 0.15.1 APIs. CUDA, ONNX/provider runtimes, SciSpaCy, `pyab3p`, model downloads, prepared dataset downloads, and two-or-more-GPU training are optional and unverified unless the active environment proves them.

## Route here for

- Loading local corpora with `ColumnCorpus`, `MultiFileColumnCorpus`, `ClassificationCorpus`, `CSVClassificationCorpus`, `JsonlCorpus`, `MultiFileJsonlCorpus`, CoNLL-U / `UniversalDependenciesCorpus`, explicit custom split files, `MultiCorpus`, split sampling, and `Corpus.downsample(...)`.
- Building label dictionaries with `corpus.make_label_dictionary(label_type=..., min_count=..., add_unk=..., add_dev_test=...)`.
- Constructing or planning training for `SequenceTagger`, `TextClassifier`, `SpanClassifier`, `RelationClassifier`, `RelationExtractor`, `TARSClassifier`, `TARSTagger`, `MultitaskModel`, and `flair.nn.multitask.make_multitask_model_and_corpus(...)`.
- Choosing `ModelTrainer.train(...)` versus `ModelTrainer.fine_tune(...)`, `embeddings_storage_mode`, `mini_batch_chunk_size`, file logs, loss files, final/best/periodic models, checkpoint-like outputs, and output directory ownership.
- Running the bundled adapted NER CLI with safe `--help`, `--list-datasets`, and `--dry-run` paths before any real training.
- Planning optional multi-GPU execution with `flair.distributed_utils.launch_distributed(...)` and `multi_gpu=True`, only after CUDA and at least two GPUs are explicitly verified.

Use `../tagging-and-annotations/` for prediction-only workflows, annotation extraction, label inspection on already-loaded sentences, tokenization/sentence splitting, serialization, visualization, and regex tagging. Use `../embeddings-and-optimization/` for embedding-family selection, transformer/cache/provider optimization, language-model training, and vector or storage debugging. Use `../biomedical-nlp/` for HunFlair/HunFlair2, biomedical dictionaries, entity linking, abbreviation handling, SciSpaCy-heavy workflows, and biomedical corpus caveats.

## Safe start checklist

1. **Pin the resource policy first.** CPU is the verified baseline. For deterministic CPU behavior, set `FLAIR_DEVICE=cpu` before importing `flair` or set `flair.device = torch.device("cpu")` immediately after import.
2. **Control caches before downloads.** If public model or prepared dataset downloads are allowed, set a deliberate `FLAIR_CACHE_ROOT` before importing `flair`. If downloads are not allowed, use local corpus files and local model paths or already-proven cache entries only.
3. **Prefer local corpus readers for reproducible work.** Prepared dataset constructors can resolve public resources when data is absent. Treat them as download-capable unless cache state is already verified.
4. **Inspect labels before model construction.** Print split lengths and a few example labels. Build the label dictionary for the exact layer to predict, such as `"ner"`, `"upos"`, `"topic"`, `"sentiment"`, `"relation"`, or `"nel"`.
5. **Start with a safe preflight.** `--help` does not import Flair. `--list-datasets` imports Flair but does not instantiate datasets. `--dry-run` can inspect local corpora without constructing transformer embeddings or training.
6. **Write outputs to caller-owned paths.** A Flair trainer directory may contain `final-model.pt`, `best-model.pt`, `training.log`, `loss.tsv`, split evaluation TSV files, periodic saved models, optimizer state, and serialized model metadata.

## Core workflow

1. **Map files to a corpus reader.** Use [Dataset formats](references/dataset-formats.md) for `ColumnCorpus`, `MultiFileColumnCorpus`, JSONL, FastText-style classification, CSV/TSV classification, CoNLL-U, custom splits, `sample_missing_splits`, `downsample`, and `MultiCorpus`.
2. **Create the dictionary intentionally.** For closed NER/POS/chunking label sets, usually pass `add_unk=False`. For open-ended span or linking labels, keep `add_unk=True` only when unknown labels are part of the contract.
3. **Select the model family.** Use [Training recipes](references/training-recipes.md) to route the task to sequence tagging, document classification, span classification, relation modeling, TARS, or multitask training.
4. **Choose the trainer method.** Prefer `ModelTrainer.fine_tune(...)` for trainable transformer workflows, low learning rates, small batches, and `embeddings_storage_mode="none"`. Use `ModelTrainer.train(...)` for classic frozen-feature or randomly initialized-head workflows with larger learning rates and annealing.
5. **Plan outputs and memory.** Decide whether to write logs/loss files, save final models, save best or periodic models, retain optimizer state, or store embeddings on `"none"`, `"cpu"`, or optional `"gpu"`.
6. **Preflight before training.** For local NER data:

```bash
python scripts/fine_tune_ner.py --help
python scripts/fine_tune_ner.py --list-datasets
python scripts/fine_tune_ner.py --dry-run --data-folder data/ner --column-format '{"0":"text","1":"ner"}' --output-dir outputs/ner
```

7. **Train only after approval.** If the selected model or dataset may download resources, require explicit cache/download approval before leaving dry-run mode.

## Bundled script

- [scripts/fine_tune_ner.py](scripts/fine_tune_ner.py) is a safe-by-default NER fine-tuning helper for local `ColumnCorpus` or JSONL data, or explicitly approved public Flair dataset constructors. It supports `--help`, `--list-datasets`, `--dry-run`, `--report-json`, explicit split files, `sample_missing_splits`, `downsample`, storage modes, trainer output settings, and an optional `--multi-gpu` flag that must be paired with the distributed-launch pattern documented in [Multi-GPU](references/multi-gpu.md).

## Read these references

- [Dataset formats](references/dataset-formats.md): corpus reader contracts, examples, custom splits, label dictionaries, downsampling, split sampling, `MultiCorpus`, CoNLL-U, and JSONL import fallback.
- [Training recipes](references/training-recipes.md): model family recipes, trainer method selection, output files, storage modes, checkpoints, relation/span/TARS/multitask patterns, and post-training validation.
- [Multi-GPU](references/multi-gpu.md): optional distributed training conditions, `launch_distributed(...)`, `multi_gpu=True`, batch-size accounting, and explicit CUDA/2+ GPU verification requirement.
- [Troubleshooting](references/troubleshooting.md): common corpus, label, trainer, cache, memory, checkpoint, relation, TARS, JSONL, CoNLL-U, and multi-GPU failures.

## Practical rules for future agents

- Keep all guidance self-contained for public pip-installed `flair`; do not require project-local package files.
- If direct import of `JsonlCorpus` or `MultiFileJsonlCorpus` from `flair.datasets` fails, import them from `flair.datasets.sequence_labeling`.
- `MultiFileColumnCorpus` is normally imported from `flair.datasets.sequence_labeling`.
- Do not infer a label layer from a file name alone. Inspect loaded examples or the dictionary.
- Prefer `embeddings_storage_mode="none"` when fine-tuning transformers. Use `"cpu"` mainly for classic static embedding workflows with enough host memory. Use `"gpu"` only with proven CUDA memory headroom.
- `ModelTrainer.train(...)` and `ModelTrainer.fine_tune(...)` both expose `multi_gpu`, but `multi_gpu=True` only belongs inside `flair.distributed_utils.launch_distributed(...)` with verified CUDA and at least two GPUs.

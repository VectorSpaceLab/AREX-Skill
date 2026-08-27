# PAWS-X Task Contracts

This file distills the benchmark-specific task dictionary, cache layout, and
model wiring for the PAWS-X workflow.

## Dataset contract

- Languages: `en`, `zh`, `de`, `es`
- Input files: `train-<lang>.tsv`, `dev-<lang>.tsv`, `test-<lang>.tsv`
- Cache files: `cached_feature_<split>_<lang>_<model>_<max_length>`

## Processor contract

- `PawsxProcessor` reads the TSV files and produces `InputExample` objects.
- `DataloaderSC(...)` tokenizes the examples, writes cache files, and returns
  per-language dataloaders.
- The loader uses `bert-base-multilingual-cased` by default.

## Task dictionary shape

Each language task uses:

- `metrics=['Acc']`
- `metrics_fn=AccMetric()`
- `loss_fn=SCLoss(label_num=len(labels))`
- `weight=[1]`

## Model wiring

- Encoder: `BertModel.from_pretrained('bert-base-multilingual-cased',
  add_pooling_layer=True)`
- Decoder: `Dropout(0.1)` plus `Linear(768, len(labels))` per language
- Optimizer: `AdamW(..., lr=2e-5, eps=1e-8)` in the benchmark trainer

## Runtime notes

- The workflow is multi-input: each language gets its own dataloader.
- The benchmark is CUDA-backed.
- The raw preprocessing helpers are legacy-sensitive and depend on older
  `networkx` behavior.

# PAWS-X Workflow

This reference covers the multilingual sentence classification benchmark.

## Workflow launch pattern

Use the PAWS-X benchmark runner with a CUDA-capable environment and a
`transformers` release that still exports `AdamW`.

## Typical command pattern

```bash
python main.py --weighting EW --arch HPS --dataset_path /path/to/data --gpu_id 0 --multi_input --mode train --save_path /tmp/libmtl-pawsx
```

Important runtime notes:

- `bert-base-multilingual-cased` is used by default and may download a model
  cache the first time it is used.
- The workflow loads four languages: English, Chinese, German, and Spanish.
- The loader builds cached feature files so repeated runs are faster.

## Shared pipeline

1. Read TSV input files for each language.
2. Tokenize sentence pairs with a multilingual tokenizer.
3. Cache the resulting features on disk.
4. Build one dataloader per language.
5. Train or evaluate with the shared LibMTL trainer.

## Workflow checks

1. Confirm the `pawsx` dataset folder exists.
2. Confirm the TSV files exist for the supported languages and splits.
3. Confirm the cache directory is writable.
4. Confirm the installed `transformers` version still exports `AdamW`.
5. Confirm CUDA is available before running the trainer.

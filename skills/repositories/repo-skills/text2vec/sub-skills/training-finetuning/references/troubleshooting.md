# Troubleshooting Training and Fine-tuning

## Pre-flight checklist

1. Validate custom pair data with `scripts/validate_text_matching_data.py`.
2. Validate BGE triples with `scripts/validate_bge_jsonl.py --train-group-size <N>`.
3. Decide whether labels are binary class ids or STS-style scores.
4. Use a fresh `output_dir` per run.
5. Enable `bf16` and `data_parallel` only after confirming hardware support.

## Common failures

| Symptom | Likely cause | Fix |
|---|---|---|
| JSONL parser errors or rows disappear | Malformed JSONL or rows are not JSON objects. The package JSONL helper prints an error and continues. | Fix the bad lines; run `validate_text_matching_data.py --format jsonl` before training. |
| TSV rows are skipped with a line-size warning | Rows do not have exactly three tab-separated fields, or text contains a tab. | Normalize to `text1<TAB>text2<TAB>label`; remove embedded tabs or switch to JSONL. |
| JSONL rows silently drop from text-matching/CoSENT training | Row lacks a complete `text1`/`text2` or `sentence1`/`sentence2` pair. | Normalize field names. Mixed schemas are allowed across rows, but every row needs one complete pair and `label`. |
| A row has both `text1`/`text2` and `sentence1`/`sentence2` | Loader precedence chooses `text1`/`text2`; the other pair is ignored. | Remove duplicate schemas or ensure both pairs are equivalent. The validator reports ambiguous rows. |
| `CrossEntropyLoss` index/range errors | `SentenceBertModel` or `BertMatchModel` received labels outside the configured class count, often STS scores with default `num_classes=2`. | Use binary labels, ensure path-based STS conversion happens intentionally, or construct the model with matching `num_classes`. |
| Float labels are truncated | Text-matching train loaders cast labels with `int(label)`. | For continuous scores, use CoSENT or pre-binarize labels yourself. The validator warns about non-integer labels under `--task text-matching`. |
| STS scores behave like binary labels | Local file path contains `STS`, so `load_text_matching_train_data` and `load_cosent_train_data` convert scores with `int(score > 2.5)`. | Keep the `STS` filename when binary conversion is desired. Rename/use a custom loader if CoSENT should keep raw 0-5 rankings. |
| Validation/test metrics compare different label scales | Train loaders may binarize STS labels, but test loaders keep labels as provided for Spearman/Pearson. | This is expected in source recipes. Document the train/eval label scales in experiment notes. |
| Training starts with zero examples or fails early | Missing train file: pair loaders warn and return an empty list; BGE loader may fall back to dataset-name loading and then return `[]` on error. | Check the path exists from the training process CWD; run the validator on the exact path. |
| Hugging Face dataset failures | `use_hf_dataset=True`, dataset-name BGE loading, or data-building recipes require network/cache. | Prefer local TSV/JSONL for reproducible/offline runs, or pre-populate the HF cache and pass local model/data paths. |
| Model load hangs or downloads unexpectedly | `model_name_or_path` is an HF id not present in cache. | Use a local Transformers-compatible model directory for offline work. |
| CUDA OOM | Batch size, sequence length, or BGE passage group is too large. | Reduce `batch_size`, `max_seq_length`, BGE `passage_max_len`, or `train_group_size`; use gradient accumulation if needed. |
| `bf16` autocast errors or unstable loss | Hardware/PyTorch build lacks bfloat16 support. | Disable `bf16`; use fp32. Use bf16 only on supported CUDA hardware. |
| `data_parallel` fails or does not speed up training | Set on CPU, MPS, one GPU, or without `torchrun`; multi-GPU path expects CUDA devices and `LOCAL_RANK`. | Disable `data_parallel` unless `torch.cuda.device_count() > 1` and launch with `torchrun --nproc_per_node <N>`. |
| BERT-match multi-card run raises an attribute-style error | The cross-encoder implementation has a separate wrapper from sentence-model trainers, so its data-parallel path is more fragile. | Prefer single-device BERT-match runs, or use CoSENT/SBERT/BGE for multi-card fine-tuning unless the BERT-match multi-card path is patched and smoke-tested. |
| Old files appear in a new experiment | `output_dir` reused from a previous run; checkpoints and `training_progress_scores.csv` are overwritten or mixed. | Use a unique output directory per experiment and archive/delete stale checkpoints deliberately. |
| BGE training quality is poor despite valid JSONL | Too few or weak negatives; `BgeTrainDataset` repeats `neg` values when `len(neg) < train_group_size - 1`. | Add more negatives, lower `train_group_size`, or run optional hard-negative mining. The BGE validator reports rows that will duplicate negatives. |
| Hard-negative mining fails at import or runtime | Optional `faiss`, `faiss-gpu`, model weights, or enough RAM/GPU are missing. | Treat hard-negative mining as optional preprocessing. Start with valid random negatives, then add FAISS/model dependencies when budget allows. |

## Difficult cases

### Mixed JSONL schemas before CoSENT

A file can combine rows using `sentence1`/`sentence2` and rows using `text1`/`text2`. The loaders handle this row-by-row, but rows with incomplete pairs are skipped. Run:

```bash
python scripts/validate_text_matching_data.py --input-file mixed_pairs.jsonl --format jsonl --task cosent
```

Check `schema_counts`, `records_invalid`, and `warnings` in the JSON summary before training.

### BGE triples with too few negatives

For `train_group_size=8`, every row ideally has at least seven negatives. If a row has only two negatives, the dataset repeats that two-item list and samples seven entries, so the batch contains duplicated negatives. Run:

```bash
python scripts/validate_bge_jsonl.py --input-file bge_train.jsonl --train-group-size 8
```

If `rows_needing_negative_duplication` is non-zero, add more negatives, lower `train_group_size`, or accept that negative diversity is reduced.

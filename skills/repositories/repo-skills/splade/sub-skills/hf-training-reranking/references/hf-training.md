# HuggingFace Trainer Workflows

SPLADE includes a HuggingFace Trainer path for training SPLADE and dense DPR-style variants with multiple hard negatives and distributed launch. The entry point is `python -m splade.hf_train`; for multi-process training use `torchrun --nproc_per_node N -m splade.hf_train`.

## How SPLADE Maps Hydra to HF Dataclasses

`python -m splade.hf_train` loads a Hydra config, initializes SPLADE's classic config, then converts selected fields into HF-style dataclasses:

| HF dataclass | Important fields | Source of truth |
| --- | --- | --- |
| `ModelArguments` | `model_name_or_path`, `max_length`, `shared_weights`, `splade_doc`, `model_q`, `dense_pooling`, `dense`, `tokenizer_name_or_path` | `init_dict.*`, `config.max_length`, `config.tokenizer_type`, `hf.model.*`, dense/siamese train model settings |
| `DataTrainingArguments` | `training_data_type`, `training_data_path`, `document_dir`, `query_dir`, `qrels_path`, `n_negatives`, `n_queries` | `hf.data.*`, with classic `train/data` fallback for hard-negative datasets and triplets |
| `LocalTrainingArguments` | `output_dir`, `resume_from_checkpoint`, `fp16`, `learning_rate`, `per_device_train_batch_size`, `seed`, `logging_dir`, `training_loss`, `l0d`, `l0q`, `T_d`, `T_q`, `top_d`, `top_q`, `lexical_type` | `hf.training.*`, `config.checkpoint_dir`, `config.lr`, `config.train_batch_size`, `config.regularizer.*` |

The final trained model is saved to `config.checkpoint_dir/model`. The entry point also writes `model_args.json`, `data_args.json`, and `training_args.json` there from the world-zero process.

## Common Config Families

- Sparse SPLADE templates include config names such as `config_hf_splade_sigir23_32neg_distil`, `config_hf_splade_sigir23_32neg_nodistil`, and main-config templates like `hf/splade` or `hf/splade_distill`.
- Dense/DPR-style templates use `hf.model.dense=true` and include examples such as `config_hf_dense_sigir23_32neg_distil`, `config_hf_dense_sigir23_32neg_nodistil`, `hf/dense_distill_vienna`, and `hf_baselines_dense/retromae`.
- Baseline variants change train model/config defaults and include examples like `hf_baselines/distilbert`, `hf_baselines/distilbert_mse`, `hf_baselines/ccmarco_doc`, `hf_baselines/ppsd_lexical`, and `hf_baselines_contrastive/distilbert`.
- Reranker training uses `python -m splade.hf_train_reranker`; see `reranking.md`.

Use config names without `.yaml` on Hydra's `--config-name` flag unless the local launch convention explicitly includes the suffix.

## Sparse SPLADE Training Pattern

Use this pattern for SPLADE lexical models:

```bash
torchrun --nproc_per_node 2 -m splade.hf_train \
  --config-name=config_hf_splade_sigir23_32neg_distil \
  config.checkpoint_dir='<CHECKPOINT_DIR>' \
  config.index_dir='<INDEX_DIR>' \
  config.out_dir='<OUT_DIR>' \
  hf.data.training_data_type=json \
  hf.data.training_data_path='<HARD_NEGATIVES_JSON>' \
  hf.data.document_dir='<COLLECTION_RAW_TSV>' \
  hf.data.query_dir='<QUERIES_RAW_TSV>' \
  hf.data.qrels_path='<QRELS_JSON>' \
  hf.data.n_negatives=4
```

Notes:

- `hf.model.dense=false` selects the SPLADE masked-LM model path.
- `hf.model.shared_weights=true` means the query and document encoders reuse one HF masked-LM model.
- `hf.model.shared_weights=false` uses a separate query encoder; `init_dict.model_type_or_dir_q` can supply the query model.
- `hf.model.splade_doc=true` switches the query side to a bag-of-words `SpladeDoc` encoder while the document side remains a masked-LM SPLADE encoder.
- `hf.training.lexical_type` can be `none`, `document`, `query`, or `both`; it masks representations with token bag-of-words constraints during training.
- Regularization fields are mapped from classic config to HF arguments: document FLOPS lambda becomes `l0d`; query L1/FLOPS lambda becomes `l0q`; schedules map to `T_d` and `T_q`.

## Dense/DPR Training Pattern

Dense mode selects `DPR` over `SPLADE`:

```bash
torchrun --nproc_per_node 2 -m splade.hf_train \
  --config-name=config_hf_dense_sigir23_32neg_distil \
  config.checkpoint_dir='<CHECKPOINT_DIR>' \
  config.index_dir='<INDEX_DIR>' \
  config.out_dir='<OUT_DIR>' \
  hf.model.dense=true \
  hf.model.shared_weights=true \
  hf.model.dense_pooling=cls \
  hf.data.training_data_type=json \
  hf.data.training_data_path='<HARD_NEGATIVES_JSON>' \
  hf.data.document_dir='<COLLECTION_RAW_TSV>' \
  hf.data.query_dir='<QUERIES_RAW_TSV>' \
  hf.data.qrels_path='<QRELS_JSON>' \
  hf.data.n_negatives=4
```

Dense pooling accepts the code paths `cls` and `mean`. Dense mode does not add SPLADE FLOPS/L1/anti-zero regularization logs.

## Training Losses and Negatives

`hf.training.training_loss` controls which loss terms are active. Common values are:

- `contrastive`
- `kldiv`
- `mse_margin`
- `kldiv_mse_margin_with_weights`
- `kldiv_mse_margin_without_weights`
- `kldiv_contrastive_without_weights`
- `kldiv_contrastive_with_weights`

`n_negatives` controls how many negatives per query are sampled from the training run/hard-negative file. The model/trainer reshape batches as `1 positive + n_negatives`, while in-batch negatives are also used in contrastive scoring. For `training_data_type=triplets`, `n_negatives` must be `1` because each row contains exactly one negative.

## Distributed and Resume Behavior

- Use `torchrun --nproc_per_node N -m splade.hf_train` for distributed data parallel training.
- `hf.training.ddp_find_unused_parameters` should be `true` for some dense/separate-encoder variants and `false` for standard shared SPLADE templates.
- `hf.training.resume_from_checkpoint=true` makes SPLADE call `get_last_checkpoint(config.checkpoint_dir)` and pass that checkpoint to `trainer.train`.
- If resuming, ensure `config.checkpoint_dir` already contains a valid Trainer checkpoint; the final saved model still lands in `config.checkpoint_dir/model`.
- If starting fresh in a non-empty output directory, set `resume_from_checkpoint=false` and manage `overwrite_output_dir` according to the local Transformers version.

## Post-Training Handoff

HF training only trains. After the final model exists under `config.checkpoint_dir/model`, hand indexing and retrieval to the Hydra pipeline sub-skill:

```bash
python -m splade.index --config-name=<SAME_OR_COMPATIBLE_CONFIG> \
  config.checkpoint_dir='<CHECKPOINT_DIR>' \
  config.index_dir='<INDEX_DIR>'

python -m splade.retrieve --config-name=<SAME_OR_COMPATIBLE_CONFIG> \
  config.checkpoint_dir='<CHECKPOINT_DIR>' \
  config.index_dir='<INDEX_DIR>' \
  config.out_dir='<OUT_DIR>'
```

Do not invent indexing-specific overrides from HF training alone; route to `../hydra-pipelines/SKILL.md` for full index/retrieve configuration semantics.

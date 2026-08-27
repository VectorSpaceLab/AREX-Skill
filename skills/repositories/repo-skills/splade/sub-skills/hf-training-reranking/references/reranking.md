# Reranker Training and Application

SPLADE has two reranker entry points:

- `python -m splade.hf_train_reranker` trains a reranker with HuggingFace Trainer and SPLADE-style hard-negative data.
- `python -m splade.rerank` applies a trained or pretrained reranker to one or more SPLADE output runs, then optionally evaluates if qrels are configured.

## Train a Reranker

Typical launch:

```bash
python -m splade.hf_train_reranker \
  --config-name=config_rerank_train_T5_3b \
  config.checkpoint_dir='<RERANKER_CHECKPOINT_DIR>' \
  config.out_dir='<RERANKER_TRAIN_OUT_DIR>' \
  config.reranker_type=rankT5 \
  init_dict.model_type_or_dir='<BASE_OR_LOCAL_RERANKER_MODEL>' \
  config.tokenizer_type='<TOKENIZER_OR_MODEL>' \
  hf.data.training_data_type=json \
  hf.data.training_data_path='<TRAIN_RUN_OR_HARD_NEGATIVES_JSON>' \
  hf.data.document_dir='<COLLECTION_RAW_TSV>' \
  hf.data.query_dir='<TRAIN_QUERIES_RAW_TSV>' \
  hf.data.qrels_path='<TRAIN_QRELS_JSON>' \
  hf.data.n_negatives=1
```

Training behavior:

- `rankT5` uses SPLADE's `RankT5EncoderFix` wrapper.
- Other training-time reranker types use `AutoModelForSequenceClassification.from_pretrained(init_dict.model_type_or_dir)`.
- `RerankerCollator` tokenizes query-document pairs, optionally with `hf.data.prompt_q` and `hf.data.prompt_d` templates.
- The trained model is saved under `config.checkpoint_dir/model`.
- `hf: training_rerank` style defaults commonly use `training_loss=kldiv`, `n_negatives=1`, `learning_rate=1e-4`, and epoch checkpointing.

## Apply a Reranker

Typical launch:

```bash
python -m splade.rerank \
  --config-name=config_reranker_toy \
  config.out_dir='<RERANK_OUT_DIR>' \
  config.reranker_type=minilm \
  config.tokenizer_type='<TOKENIZER_OR_MODEL>' \
  init_dict.model_type_or_dir='<RERANKER_MODEL_OR_CHECKPOINT>' \
  data.path_run='[<RUN_JSON_OR_TREC_PATH>]' \
  data.run_name='[<RUN_NAME>]' \
  data.document_dir='[<COLLECTION_RAW_TSV_OR_IR_DATASETS_ID>]' \
  data.query_dir='[<QUERIES_RAW_TSV>]' \
  data.EVAL_QREL_PATH='[<QRELS_JSON_OR_EMPTY>]'
```

`data.path_run`, `data.run_name`, `data.document_dir`, `data.query_dir`, and `data.EVAL_QREL_PATH` are lists zipped together. Keep the same number of entries in each list.

## Reranker Types

| `config.reranker_type` | Model path | Dataset/evaluator path | Dependency and hardware notes |
| --- | --- | --- | --- |
| `rankT5` | `RankT5EncoderFix`, loads checkpoint from `config.checkpoint` or `config.checkpoint_dir/model/pytorch_model.bin` | Standard rerank dataset and evaluator, with `restore=false` | Needs a trained SPLADE RankT5 checkpoint; can use `DataParallel` when multiple GPUs are visible. |
| `monoT5` | `AutoModelForSeq2SeqLM.from_pretrained` | `EvalDatasetMonoT5` and seq2seq scoring | Usually large; expect GPU memory pressure and model downloads unless checkpoint is local. |
| `duoT5` | `AutoModelForSeq2SeqLM.from_pretrained` | `EvalDatasetMonoT5` with duo scoring branch | Usually large; check batch size and model size. |
| `PairwisePrompt` | `AutoModelForSeq2SeqLM.from_pretrained(..., trust_remote_code=True)` | Pairwise prompt dataset/dataloader/evaluator | Trusts remote code if model is remote; requires prompt config and more careful security review. |
| Any other string, such as `minilm` or `debertav3` | `TransformerRank` at rerank time; sequence classification at train time | Standard rerank dataset/evaluator | Needs tokenizer/model compatible with pair classification/ranking. |

`config.return_token_type_ids=true` is useful for BERT/DeBERTa-like pair classifiers. T5-style models usually do not use token type IDs.

## Reranking Data Inputs

At apply time the reranker iterates over each run and collection/query/qrel tuple:

- `data.path_run`: one or more input run files.
- `data.run_name`: names used in output subdirectories.
- `data.document_dir`: raw TSV collection path or an `ir_datasets` dataset id when `data.docs_ir_dataset=true`.
- `data.query_dir`: raw TSV query file.
- `data.EVAL_QREL_PATH`: qrels path; when the first entry is truthy, SPLADE calls evaluation after reranking.
- `config.top_k`: number of top documents per query reranked.
- `config.eval_batch_size`, `config.max_length`, and `config.tokenizer_type`: batching/tokenization settings.

When `data.docs_ir_dataset=true`, SPLADE sets `IR_DATASETS_HOME` from `ir_datasets.dataset_path` and imports `ir_datasets`. Avoid this path unless the environment is prepared for that optional dependency and dataset storage.

## Rerank Output and Evaluation

For each dataset/run pair, SPLADE appends a retrieval name shaped like `<dataset_name>/<run_name>/<top_k>` and evaluates into `config.out_dir/<dataset_name>/<run_name>/<top_k>`. If `data.EVAL_QREL_PATH[0]` is non-empty, it calls `splade.evaluate.evaluate`, which requires evaluation dependencies such as `pytrec_eval`.

## Builder Examples

Train a reranker command without launching training:

```bash
python skills/splade/sub-skills/hf-training-reranking/scripts/splade_hf_command_builder.py hf-train-reranker \
  --config-name config_rerank_train_T5_3b \
  --checkpoint-dir '<RERANKER_CHECKPOINT_DIR>' \
  --out-dir '<RERANKER_TRAIN_OUT_DIR>' \
  --reranker-type rankT5 \
  --model-or-checkpoint '<BASE_T5_OR_LOCAL_MODEL>' \
  --training-data-type json \
  --training-data-path '<TRAIN_RUN_JSON>' \
  --document-path '<COLLECTION_RAW_TSV>' \
  --query-path '<TRAIN_QUERIES_RAW_TSV>' \
  --qrels-path '<TRAIN_QRELS_JSON>' \
  --n-negatives 1
```

Apply a reranker command without launching inference:

```bash
python skills/splade/sub-skills/hf-training-reranking/scripts/splade_hf_command_builder.py rerank \
  --config-name config_reranker_toy \
  --out-dir '<RERANK_OUT_DIR>' \
  --reranker-type minilm \
  --model-or-checkpoint '<RERANKER_MODEL_OR_CHECKPOINT>' \
  --path-run '<RUN_JSON_OR_TREC_PATH>' \
  --run-name '<RUN_NAME>' \
  --document-path '<COLLECTION_RAW_TSV>' \
  --query-path '<QUERIES_RAW_TSV>' \
  --qrels-path '<QRELS_JSON>' \
  --top-k 100
```

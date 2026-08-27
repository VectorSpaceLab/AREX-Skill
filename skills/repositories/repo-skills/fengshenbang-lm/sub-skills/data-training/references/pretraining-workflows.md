# Pretraining workflows

This reference is for turning an existing training shell script into a safe, resource-aware plan. Separate data preparation, runtime, optimizer, and checkpoint policy before you edit anything.

## Resource-aware command categories

| Category | Typical flags or env | What to decide |
|---|---|---|
| Data prep | `data_dir`, `train_data_path`, `datasets_name`, `train_file`, `val_file`, `test_file`, `train_split_size`, `preprocessing_num_workers`, `dataset_num_workers` | Where the corpus comes from, how it is split, and whether it must be cached first. |
| Collator / task shape | `max_seq_length`, `max_enc_length`, `max_dec_length`, `masked_lm_prob`, `permute_sentence_ratio`, `decode_type`, `formator`, `prompt` | How text becomes model inputs and what the model is expected to predict. |
| Optimization | `learning_rate`, `weight_decay`, `warmup_steps`, `warmup_ratio`, `scheduler_type`, `adam_beta1`, `adam_beta2`, `adam_epsilon` | Which schedule and optimizer the run should use. |
| Runtime / distribution | `gpus`, `num_nodes`, `strategy`, `precision`, `accumulate_grad_batches`, `replace_sampler_ddp` | How expensive the run is allowed to be and whether custom samplers must stay active. |
| Checkpoint policy | `monitor`, `mode`, `save_top_k`, `save_last`, `every_n_train_steps`, `save_ckpt_path`, `load_ckpt_path`, `resume_from_checkpoint` | What to save, what to resume, and how much history to keep. |
| Environment plumbing | `PL_DEEPSPEED_CONFIG_PATH`, `--deepspeed`, `TORCH_EXTENSIONS_DIR` | Which runtime configuration is externalized instead of being part of the model or data. |

## BERT-style pretraining

### Data shape

The raw corpus is line-delimited JSON with a `text` field:

```json
{"text": "原始长文本..."}
```

### Typical flow

1. Split huge source files into smaller JSONL shards when they are too large to preprocess comfortably.
2. Sentence-split long paragraphs into shorter `{"text": ...}` records.
3. Build cached dataset shards so repeated runs do not re-read the raw corpus.
4. Feed the cached data into the pretraining data module and collator.

### What the code is doing

- `BertDataGenerate` / `preprocessing.py` create sentence-level JSONL and cached HF shards.
- `DataCollate` in the BERT pretraining script performs whole-word masking and n-gram masking.
- The training target is masked-LM only; the script does not rely on an NSP objective.

### Safe command reading

Treat these flags as categories, not as one blob:

- data prep: `datasets_name`, `num_workers`, `train_batchsize`
- runtime: `gpus`, `num_nodes`, `strategy`, `precision`, `replace_sampler_ddp=False`
- optimizer: `learning_rate`, `weight_decay`, `warmup`
- checkpoint: `monitor`, `save_top_k`, `save_last`, `every_n_train_steps`, `dirpath`

## Megatron BERT / indexed pretraining

Megatron-style helpers use indexed datasets and can blend multiple corpora.

### Input contract

- `data_prefix` is a weight/prefix pair list such as `0.7 corpus_a 0.3 corpus_b`.
- `splits_string` can use commas or slashes, for example `949,50,1` or `9/1/0`.
- `dataset_type` selects the masking objective: `standard_bert`, `bert_cn_wwm`, `bart`, `coco_lm`, `t5`, or `ict`.

### What to preserve when editing a script

- the indexed-dataset prefix and split string
- the chosen `dataset_type`
- the `replace_sampler_ddp=False` choice if the sampler must stay custom
- any deepspeed environment variable or config path

## Unsupervised T5 pretraining

### Data shape

Unsupervised T5 works on a text column, usually `text`, from a cached or raw dataset. The loader can either:

- read a dataset path and use the `train` split, or
- load a preprocessed cached dataset and slice the split directly.

### Workflow notes

- `train_split_size` determines whether the loader creates an internal train/test split.
- `tokenizer_type` decides whether the loader uses MT5 tokens or a BERT tokenizer fallback.
- `new_vocab_path` and `keep_tokens_path` are used when the tokenizer vocab is being resized.

### Resource note

The preprocessing step is CPU-heavy but parallelizable; the actual pretraining run is the GPU-heavy stage. Keep them separate when you are converting a script into resource tiers.

## Randeng / BART denoising pretraining

### Data shape

The collator expects a source field such as `text` and performs sentence permutation and span masking inside the batch step.

### Workflow notes

- `masked_lm_prob` controls text infilling.
- `permute_sentence_ratio` controls sentence shuffling.
- `max_seq_length` is the final padded sequence length.
- The collator creates `decoder_input_ids` by shifting labels to the right.

### Good edits

If you are rewriting a shell script, keep these categories distinct:

- `sample_content_key` and `max_seq_length` are data shape settings.
- `learning_rate`, `weight_decay`, and `warmup_ratio` are optimizer settings.
- `save_ckpt_path` and `load_ckpt_path` are checkpoint settings.

## Sequence-tagging and downstream fine-tuning workflows

For sequence tagging, choose the `decode_type` first and then match the label file to that choice.

| Family | Data contract | Typical runtime note |
|---|---|---|
| `linear` / `crf` | full tag inventory in `labels.txt` and BMES/BIOES lines in the corpus files | `replace_sampler_ddp=False` is often kept for custom batching. |
| `span` / `biaffine` | entity types in `labels.txt` and spans derived from the labels | `max_seq_length` must match the collator’s expected padding. |

For LCSTS, QA, and dialog-style seq2seq fine-tuning, the same optimization and checkpoint categories still apply. The only thing that changes is the record shape and collator.

## Resume-safe checklist

- Keep the dataset split or cache path stable.
- Keep the tokenizer / vocab resize inputs stable.
- Keep the checkpoint path and `consumed_samples` accounting aligned.
- Keep the sampler mode and `replace_sampler_ddp` setting aligned.
- Do not treat `--deepspeed` or `PL_DEEPSPEED_CONFIG_PATH` as data flags; they are runtime configuration.

## Related references

- [data-formats.md](data-formats.md)
- [training-arguments.md](training-arguments.md)
- [distributed-training.md](distributed-training.md)
- [metrics-and-validation.md](metrics-and-validation.md)

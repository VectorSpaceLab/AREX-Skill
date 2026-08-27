# Classification/regression troubleshooting

## Quick diagnosis matrix

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ValueError: Task not found: ...` | `--task_name` is not one of the built-in processor keys. | Use `mnli_matched`, `mnli_mismatched`, `sts-b`, `imdb`, or `yelp5`; otherwise reshape data or add a new processor in the caller's working copy. |
| `At least one of do_train, do_eval, do_predict ... must be True` | No mode flag was enabled. | Generate a command with `--mode train`, `eval`, `predict`, or `train_eval`. |
| STS-B logs `eval_accuracy` or crashes on labels | Missing `--is_regression=True` or reused classification TFRecords. | Add `--is_regression=True`; remove stale TFRecords or use a fresh `output_dir`/`--overwrite_data=True`. |
| `could not convert string to float` for STS-B | Score column is missing or nonnumeric. | Check STS-B TSV column 9 and header handling. |
| Many `Incomplete line, ignored` warnings | TSV rows do not have required text/label columns. | Confirm GLUE column layout: MNLI text columns 8/9; STS-B text columns 7/8 and score 9. |
| Label mapping error or `KeyError` | Labels do not match processor labels. | Use exact labels: MNLI `contradiction/entailment/neutral`, IMDB `neg/pos`, Yelp `1..5`; STS-B labels must be floats. |
| Yelp header row fails | `Yelp5Processor` does not skip headers. | Remove CSV header rows before training/eval. |
| IMDB examples missing | Directory names or file extensions do not match. | Use `train/neg/*.txt`, `train/pos/*.txt`, `test/neg/*.txt`, `test/pos/*.txt`. |
| Prediction crashes with missing/invalid `predict_dir` | `--do_predict=True` but `--predict_dir` omitted. | Provide a dedicated prediction output directory. |
| Prediction with IMDB/Yelp and `--eval_split=test` fails | Those processors do not implement a separate unlabeled test reader. | Use default `--eval_split=dev` for their labeled `test` data, or add a processor with `get_test_examples`. |
| Eval finds no checkpoints or crashes parsing step | `model_dir` does not contain normal `model.ckpt-<step>.index` files. | Point `model_dir` at the fine-tuned Estimator directory; do not point it at raw released artifacts unless they follow the expected checkpoint naming. |
| Eval-all-checkpoints evaluates the wrong state | `model_dir` and `init_checkpoint` roles were mixed. | For eval, scan fine-tuned `model_dir` and usually omit `init_checkpoint`. Keep released model artifacts separate. |
| TensorFlow reports missing `spiece.model`, config, or checkpoint files | Path points at the wrong released model directory or incomplete checkpoint prefix. | Confirm `spiece.model`, `xlnet_config.json`, and checkpoint prefix plus shard files exist. The checkpoint flag is the prefix, not only the `.index` file. |
| Preprocessing reuses old data | TFRecord filename only encodes SentencePiece basename, sequence length, split, and mode. | Use a clean `output_dir` or `--overwrite_data=True` after changing raw data, task, labels, SentencePiece model content, or regression/classification mode. |
| GPU out-of-memory | `max_seq_length`, per-GPU `train_batch_size`, or model size is too high. | Reduce `train_batch_size`; reduce `max_seq_length`; use XLNet-Base; use more GPUs with the same per-GPU batch; or switch to TPU for long-sequence large-model runs. |
| Multi-GPU eval gives suspicious metrics | The documented code treats multi-GPU evaluation as tricky. | Train with multiple GPUs if needed, then evaluate with `num_core_per_host=1` and one visible GPU. |
| `weight_decay > 0` fails on multi-GPU | Source explicitly rejects weight decay with non-TPU multi-GPU training. | Set `--weight_decay=0` for multi-GPU, use single GPU, or modify optimizer code deliberately. |
| TPU cannot read paths or stalls during preprocessing | Some paths are local and some are cloud storage; preprocessing runs locally. | Keep `data_dir` and `spiece_model_file` locally accessible for preprocessing; place `model_dir`, `output_dir`, and checkpoints where the TPU job can access them. |
| Abseil help prints then exits nonzero under an environment wrapper | Abseil/TensorFlow help handling and wrapper exit propagation. | Treat printed help text as successful flag discovery; do not classify this alone as a broken CLI. |
| `DuplicateFlagError` when importing several scripts in one Python process | Repo CLI modules define overlapping absl flags. | Inspect one CLI module per process; do not import `run_classifier.py`, `run_squad.py`, and other flag modules together. |

## Unsupported task names

The processor map is fixed in `run_classifier.py`:

```text
mnli_matched, mnli_mismatched, sts-b, imdb, yelp5
```

There are no built-in processors for QNLI, QQP, RTE, SST-2, MRPC, CoLA, Yelp-2, DBpedia, Amazon, or arbitrary TSV column names in this checkout. To run such data, reshape into a supported format only when labels and task semantics match, or add a new `DataProcessor` and map entry in the caller's code.

## STS-B regression checklist

Before running STS-B:

- `--task_name=sts-b`.
- `--is_regression=True` in train, eval, and predict.
- TSV score labels are numeric floats in column 9 for train/dev.
- `output_dir` does not contain stale classification TFRecords.
- Eval command scans fine-tuned `model_dir`; it does not reinitialize from the released checkpoint directory.
- Interpret best result by `eval_pearsonr`, not `eval_accuracy`.

## Directory separation checklist

Use this separation unless deliberately resuming from a fine-tuned checkpoint:

```text
released_model_dir/
  spiece.model
  xlnet_config.json
  xlnet_model.ckpt.index
  xlnet_model.ckpt.meta
  xlnet_model.ckpt.data-00000-of-00001

raw_task_data/          # data_dir
proc_data/<task>/       # output_dir: generated TFRecords
exp/<task>/             # model_dir: fine-tuned checkpoints/events
pred/<task>/            # predict_dir: generated predictions
```

`--init_checkpoint` should be the checkpoint prefix, for example `released_model_dir/xlnet_model.ckpt`; `--model_dir` should be the training output directory, for example `exp/sts-b`.

## GPU memory triage

Memory use grows quickly with model size and `max_seq_length`. The README's 16GB GPU table reported much smaller single-GPU capacities for XLNet-Large than XLNet-Base, especially at sequence length 512. For practical classification runs:

1. Lower `--train_batch_size` first. In multi-GPU mode this is per GPU.
2. Lower `--max_seq_length` if the task tolerates truncation.
3. Use XLNet-Base instead of XLNet-Large.
4. Increase GPU count for training by setting `num_core_per_host` and visible devices, but still evaluate on one GPU.
5. For IMDB sequence length 512 with XLNet-Large, prefer a TPU-class recipe if exact README performance is required.

## Eval-all-checkpoints without corrupting checkpoint roles

A safe STS-B eval-all-checkpoints command has these properties:

- `--do_train=False --do_eval=True`.
- `--eval_all_ckpt=True`.
- `--is_regression=True`.
- `--model_dir` points to fine-tuned checkpoints, for example `exp/sts-b`.
- `--init_checkpoint` is omitted unless intentionally evaluating a special initialized graph.
- `--output_dir` points to the same preprocessing cache used for STS-B or to a fresh cache with the same `max_seq_length` and SentencePiece model.

If eval suddenly reports no checkpoints, inspect `model_dir` for `*.index` files and ensure their names end in `-<step>.index`.

# Pipelines and CLI Troubleshooting

## Fast triage

1. Identify whether the user is using the console command or a programmatic class.
2. For console use, confirm the shape is exactly `fengshen-pipeline <pipeline_name> predict|train ...`.
3. Run a safe parser check:

   ```bash
   python scripts/inspect_pipeline_cli.py --pipeline text_classification
   python scripts/inspect_pipeline_cli.py --pipeline sequence_tagging
   ```

4. If real prediction/training is requested, confirm whether model and dataset downloads are allowed. If not, require local model/data paths.
5. Route model-class errors to `model-zoo`; route Trainer/checkpoint/deepspeed/CUDA/data-loader internals to `data-training`.

## Failure matrix

| Symptom | Likely cause | Fix |
|---|---|---|
| `args len < 3` | Console command missing pipeline name or method. | Use `fengshen-pipeline text_classification predict --help` or `fengshen-pipeline text_classification train ...`. |
| `cmd not support, now only support {predict, train}` | Method is not `predict` or `train`. | The console has only those two methods. Use Python APIs for other workflows. |
| `ModuleNotFoundError: fengshen.pipelines.<name>` | Unsupported or misspelled pipeline name. | Use `text_classification` for the main console route; `sequence_tagging` is parser/help-only for most tasks. UniMC/UniEX/TCBert/Ubert are programmatic routes. |
| Import fails with missing `LongformerModel`, `pytorch_lightning`, `deepspeed`, or similar before help prints. | Installed dependency stack is missing or incompatible. | Treat this as environment/import failure, not a model failure. Inspect installed versions, use an isolated compatible environment, and avoid claiming the pipeline name is unknown until module availability is checked. |
| Help works but prediction starts downloading. | Real `predict` initializes model/config/tokenizer from `--model`. | Use a local model directory, pre-populate the cache, or ask for network approval. |
| Help works but `train` downloads AFQMC or another dataset. | Console `train` calls `datasets.load_dataset(args.datasets)`. | For local JSONL, use the Python route in [text-classification.md](text-classification.md), not `--datasets IDEA-CCNL/AFQMC`. |
| Text classification batch fails on `sentence`/`sentence2`/`label`. | Data fields do not match `--texta_name`, `--textb_name`, `--label_name`, or labels are strings. | Rename fields or set parser args; map string labels to integer ids for `TextClassificationPipeline`. |
| Pair classification ignores second sentence. | `textb_name` is absent or empty in rows. | Ensure the second field exists and set `--textb_name` correctly. For prediction-only console, the README-style route uses `[SEP]` inside `--text`. |
| `sequence_tagging` console train raises a `TypeError`. | Generic CLI passes a dataset object, but `SequenceTaggingPipeline.train()` takes no dataset argument and loads from `args.data_dir`. | Use the programmatic sequence-tagging route with `SequenceTaggingPipeline(model_path=..., args=args)`. |
| Sequence tagging initialization fails opening `labels.txt`. | `args.data_dir` is missing or does not contain `labels.txt`. | Generate/check the layout with `scripts/make_sequence_tagging_fixture.py`; pass `--data_dir`. |
| Sequence tagging fails on `train.all.bmes` or `dev.all.bmes`. | Expected NER data files are missing or named differently. | Create `<mode>.all.bmes` files with blank-line-separated token/tag rows. |
| Sequence tagging entities look wrong. | Decode type and label scheme do not match; span/biaffine expect entity types derived from tag suffixes. | Choose `linear`/`crf` for token labels; choose `span`/`biaffine` only with matching checkpoints and labels. |
| Original `fengshen.pipelines.test.py` or `test_tagging.py` fails. | Original tests use hard-coded local model/data paths and CUDA settings. | Do not run them as portable checks; use bundled fixture/helper scripts. |
| TCBert parser helper not found. | The package method is misspelled. | Call `TCBertPipelines.piplines_args(parser)`. |
| TCBert initialization missing arguments. | `TCBertPipelines(args, model_path, nlabels)` requires model path and number of prompt labels. | Pass `model_path='...'` and `nlabels=len(prompt_label)`. |
| Ubert/UniEX schema rejected. | Ubert uses `choices`; UniEX uses `choice`; task-specific list keys differ. | Check [unimc-uniex-ubert.md](unimc-uniex-ubert.md) and normalize field names. |
| CUDA/GPU error from `cuda=True`, `--gpus`, or `--strategy`. | Optional GPU/Trainer/deepspeed path is selected without a compatible backend. | Use CPU flags (`cuda=False`, `--gpus 0` or `--device -1`) for safe checks; route full backend preparation to `data-training`. |

## Diagnosing an unknown pipeline import failure

Use the helper with the exact pipeline name:

```bash
python scripts/inspect_pipeline_cli.py --pipeline unknown_name
```

Interpretation:

- If import fails for `fengshen.pipelines.unknown_name`, the name is not a package pipeline module unless the installed package differs.
- If import fails for a dependency while importing a valid module, the pipeline may exist but the environment cannot import it. Fix dependencies before changing names.
- If import succeeds but there is no `Pipeline` alias or no `add_pipeline_specific_args`, the class is programmatic-only for this package version.

## Safe local data adaptation checklist

For pair classification without downloading AFQMC:

1. Run `python scripts/make_classification_fixture.py --out-dir ./local-cls`.
2. Confirm your rows have `sentence`, `sentence2`, `label`, and `id`, or choose matching field names.
3. Ensure `label` values are integer ids.
4. Use `datasets.load_dataset('json', data_files=...)` in Python and then `TextClassificationPipeline.train(datasets)`.

For sequence tagging:

1. Run `python scripts/make_sequence_tagging_fixture.py --out-dir ./local-ner`.
2. Confirm `labels.txt`, `train.all.bmes`, and `dev.all.bmes` exist.
3. Choose `--decode_type` to match the checkpoint.
4. Initialize `SequenceTaggingPipeline(model_path=..., args=args)` from Python.

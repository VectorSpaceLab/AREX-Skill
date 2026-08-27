# HF Training and Reranking Troubleshooting

Use this page to diagnose command construction problems before launching expensive SPLADE training or reranking jobs.

## Invalid `training_data_type`

Symptoms:

- Assertion failure in the config conversion step.
- `NotImplementedError: training_data_type must be in [saved_pkl, pkl_dict, trec, json]` from `L2I_Dataset`.

Fix:

- Use exactly one of `saved_pkl`, `pkl_dict`, `trec`, `json`, or `triplets`.
- Use `triplets` only with `python -m splade.hf_train`, not generic non-triplet dataset loading.
- For non-triplet data, provide `hf.data.training_data_path`, `hf.data.document_dir`, `hf.data.query_dir`, and `hf.data.qrels_path`.

## Triplets and Multiple Negatives

Symptoms:

- Assertion failure in conversion when `training_data_type=triplets`.
- Shape errors later in model/trainer code.

Fix:

- Set `hf.data.n_negatives=1` for triplets.
- Ensure each triplet row is raw text with exactly three tab-separated fields: `query`, `positive`, `negative`.
- Do not pass hard-negative JSON/TREC assumptions to triplet mode.

## Missing Query, Document, Qrel, or Score Paths

Symptoms:

- File-not-found while preloading documents or queries.
- Empty query list followed by assertion failure.
- Key errors when qrels reference document/query IDs not present in TSV files.

Fix:

- Confirm TSV lines use `ID<TAB>TEXT` and IDs match qrels/run IDs after string conversion.
- Confirm qrels are JSON shaped as `{QID: {DID: relevance}}` with at least one relevance value `>= 1` per query.
- Confirm the training hard-negative/run file has candidates for qids present in qrels.
- For `pkl_dict`, remember integer IDs are cast to strings and queries without enough candidates can be filtered.

## `shared_weights`, `model_q`, `splade_doc`, and `dense`

Symptoms:

- Unexpected separate query model loading.
- Missing `query/` subdirectory when loading or saving separate encoders.
- Dense model output or regularization logs differ from sparse SPLADE expectations.

Fix:

- `hf.model.dense=true` selects `DPR` over sparse `SPLADE`; sparse FLOPS/L1/anti-zero regularization is skipped.
- `hf.model.shared_weights=true` shares one encoder for query and document.
- `hf.model.shared_weights=false` creates a separate query encoder from `init_dict.model_type_or_dir_q` when present, otherwise from the document model path.
- `hf.model.splade_doc=true` uses bag-of-words query representations with masked-LM document representations.
- `hf.model.dense_pooling` should be `cls` or `mean` for dense mode.
- Match `hf.training.ddp_find_unused_parameters` to the architecture; dense/separate encoders may need `true`, while standard shared SPLADE configs often use `false`.

## Reranker Type and Optional Dependencies

Symptoms:

- `warning: could not load pygaggle` during rerank dataset import.
- `pytrec_eval` import or build failure during evaluation.
- Out-of-memory errors when using T5-style rerankers.
- Remote-code security concerns with pairwise prompt models.

Fix:

- Install `pytrec_eval` before commands that evaluate reranked output; omit qrels or skip evaluation if it is unavailable.
- Treat `pygaggle` warnings as relevant for mono/duo T5-style rerank data paths; install it when the selected path requires pygaggle `Query`/`Text` objects.
- For `monoT5`, `duoT5`, `rankT5`, and `PairwisePrompt`, check GPU memory, model size, `eval_batch_size`, and whether the model is local or must be downloaded.
- `PairwisePrompt` uses `trust_remote_code=True`; only use trusted model sources and document that decision.
- For `rankT5`, confirm the checkpoint exists at `config.checkpoint` or `config.checkpoint_dir/model/pytorch_model.bin`.

## `resume_from_checkpoint` and `output_dir`

Symptoms:

- Resume attempts fail because no last checkpoint exists.
- Training writes checkpoints somewhere unexpected.
- Final model not found after training.

Fix:

- SPLADE maps HF `output_dir` to `config.checkpoint_dir` during conversion.
- `resume_from_checkpoint=true` calls `get_last_checkpoint(config.checkpoint_dir)`, then passes that path to `trainer.train`.
- The final model is saved to `config.checkpoint_dir/model`, not directly to the root checkpoint directory.
- For fresh runs, use an empty checkpoint directory or set resume behavior intentionally. If the Transformers version complains about a non-empty output directory, manage `overwrite_output_dir` explicitly.

## Hydra Override Pitfalls

Symptoms:

- Overrides appear ignored.
- Lists such as `data.path_run` parse incorrectly.
- Shell expands brackets, commas, or braces.

Fix:

- Use `key=value` Hydra overrides after the module command, for example `hf.data.n_negatives=4`.
- Quote list overrides: `data.path_run='[<RUN_PATH>]'`.
- Quote paths with spaces or special characters.
- Keep config names and config groups distinct: `--config-name=config_reranker_toy` selects a config file, while `config.reranker_type=rankT5` overrides a field.

## Safe Preflight Checks

Before expensive runs:

```bash
python -m splade.hf_train --help
python -m splade.hf_train_reranker --help
python -m splade.rerank --help
```

These checks should only inspect CLI/Hydra help. They may still import optional modules, so missing optional dependencies can surface early. If help fails on an optional dependency that the requested workflow does not use, record the dependency gap and avoid claiming the full workflow was verified.

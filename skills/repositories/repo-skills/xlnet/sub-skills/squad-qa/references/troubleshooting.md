# SQuAD troubleshooting

## Missing `--output_dir`

Symptoms:

- Preprocessing fails before writing TFRecords.
- Training cannot find `*.train.tf_record` files.
- Prediction cannot create or reuse eval cache.

Fix:

- Always set `--output_dir` to a real feature-cache directory.
- Keep `--output_dir` separate from `--model_dir` and `--predict_dir`.
- For TPU mode, make `--output_dir` a GCS path unless the TPU runtime can read your custom path.

## Missing `--predict_dir`

Symptoms:

- Prediction attempts to create an empty or invalid directory.
- `predictions.json`, `nbest_predictions.json`, or `null_odds.json` are missing after a prediction run.

Fix:

- Always set `--predict_dir` when `--do_predict=True`.
- Use a new `--predict_dir` per dataset/checkpoint if you need to keep old outputs.
- For TPU workflows, use a GCS `--predict_dir` or a path your TPU host can write.

The bundled command builder requires `--predict-dir` for `gpu-base`, `tpu-large`, and `predict-only` modes to avoid this failure.

## Missing or incompatible SentencePiece model

Symptoms:

- `sp_model.Load(...)` fails.
- Token ids look inconsistent with the checkpoint.
- Answer span alignment becomes poor after preprocessing.

Fix:

- Set `--spiece_model_file` to the `spiece.model` from the same XLNet checkpoint family as `--model_config_path` and `--init_checkpoint`/`--model_dir`.
- Do not mix cased and uncased assets. Keep `--uncased=False` for cased XLNet checkpoints.
- Recreate preprocessing/eval cache after changing the SentencePiece model.

## Missing model config or checkpoint

Symptoms:

- `XLNetConfig(json_path=...)` fails.
- Training starts from random or unexpected variables.
- Prediction-only produces no checkpoint or cannot restore variables.

Fix:

- Training needs `--model_config_path`, `--spiece_model_file`, and `--init_checkpoint`.
- Prediction-only needs `--model_config_path`, `--spiece_model_file`, and a fine-tuned checkpoint under `--model_dir`.
- Do not rely on `--init_checkpoint` for prediction-only; the model function logs that it is not used in predict mode.
- Keep model size consistent: a base config must pair with a base checkpoint, and a large config must pair with a large checkpoint.

## Invalid SQuAD 2.0 or SQuAD 1.1 training fields

Symptoms:

- `KeyError: 'is_impossible'` during preprocessing/training.
- `ValueError: For training, each question should have exactly 1 answer.`
- Unanswerable questions are treated as answerable.

Fix:

- For SQuAD 2.0 training, each QA needs `is_impossible`.
  - Answerable: `"is_impossible": false`, exactly one answer with `text` and `answer_start`.
  - Unanswerable: `"is_impossible": true`, empty `answers` list.
- For SQuAD 1.1 training, add `"is_impossible": false` to every QA before preprocessing.
- Do not keep multiple annotated answers in the training file. The training reader accepts exactly one answer for answerable examples.

## Stale or mismatched feature cache

Symptoms:

- Prediction uses examples from an older `--predict_file`.
- Tensor shapes mismatch after changing sequence/query length.
- Metrics do not change after replacing input data.

Cause:

- Prediction reuses `<spiece_basename>.slen-*.qlen-*.eval.tf_record` and `*.eval.features.pkl` from `--output_dir` when both files exist and `--overwrite_data=False`.

Fix:

- Pass `--overwrite_data=True` when changing `--predict_file`, `--spiece_model_file`, `--max_seq_length`, `--max_query_length`, or `--doc_stride`.
- Or delete the eval cache files in `--output_dir` before prediction.

## Long preprocessing and multiprocessing

Symptoms:

- Preprocessing appears slow or CPU-bound.
- A single training TFRecord shard takes a long time to finish.

Cause:

- The code accurately maps raw character positions to SentencePiece token positions for every answer and long-context window.

Fix:

- Use `--num_proc N` and launch one preprocessing command per `--proc_id` from `0` to `N-1`.
- Keep all workers on the same `--train_file`, `--spiece_model_file`, sequence/query/stride settings, and `--output_dir`.
- Check that every expected `proc_id` shard exists before training.
- Avoid using `N` much larger than available CPU cores or storage bandwidth.

## GPU out-of-memory

Symptoms:

- CUDA OOM during training or prediction.
- OOM appears after increasing `start_n_top`, `end_n_top`, or sequence length.

Fixes in order:

1. Reduce `--train_batch_size` for training.
2. Reduce `--predict_batch_size` for prediction.
3. Keep `--max_seq_length=512` only if memory allows; lower values reduce memory but may reduce long-context accuracy.
4. Keep `--start_n_top` and `--end_n_top` at the default 5 unless a task truly needs wider beams.
5. Use the GPU base recipe rather than TPU large when running locally, and treat `--num_core_per_host` as the number of GPUs.

## TPU/GCS path mismatch

Symptoms:

- TPU workers cannot read checkpoints or TFRecords.
- Local files work during preprocessing but training fails on TPU.
- Permission errors for `gs://...` paths.

Fix:

- Use GCS paths for TPU `--output_dir`, `--init_checkpoint`, `--model_dir`, and `--predict_dir`.
- Ensure the TPU service account can read the checkpoint bucket and write model/prediction buckets.
- Keep local raw SQuAD JSON only if the host-side code can access it before/while launching the TPU job; otherwise stage prediction/training JSON where the runtime can read it.
- If TPU/GCS is not configured, switch to the GPU base fallback instead of forcing the TPU large recipe.

The command builder blocks non-GCS TPU output/checkpoint/model/predict paths by default. Use `--allow-non-gcs-tpu-paths` only for a known custom TPU setup.

## No predictions or missing question ids

Symptoms:

- `squad_utils` prints `Missing prediction for <qid>`.
- Metrics are lower than expected or total count looks wrong.

Fix:

- Confirm every `qas[].id` in `--predict_file` is unique.
- Confirm `--predict_file` matches the eval cache in `--output_dir`; use `--overwrite_data=True` after changing files.
- Do not evaluate predictions generated from a different dataset.

## No-answer threshold confusion

Symptoms:

- `predictions.json` contains non-empty answers for unanswerable questions.
- User expects final answers to already apply a no-answer threshold.

Explanation:

- `write_predictions` stores the best non-null span in `predictions.json`.
- `null_odds.json` stores the no-answer score.
- SQuAD 2.0 threshold metrics (`best_f1`, `best_exact`, and thresholds) are computed from predictions plus `null_odds.json`.

Fix:

- Use the logged best-threshold metrics for evaluation.
- If a downstream consumer needs thresholded predictions, post-process `predictions.json` with the chosen threshold from `best_f1_thresh` or `best_exact_thresh` and `null_odds.json`.

## Abseil flag collisions during inspection

Symptoms:

- `DuplicateFlagError` when importing multiple XLNet CLI modules in one process.

Fix:

- Run `run_squad.py --help` or import `run_squad` in its own Python process.
- Do not import `run_classifier.py`, `run_race.py`, and `run_squad.py` together in the same long-lived process.

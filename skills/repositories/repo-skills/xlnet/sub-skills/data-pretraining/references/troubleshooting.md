# Troubleshooting

| Symptom | Likely cause | What to check | Fix |
| --- | --- | --- | --- |
| SentencePiece load fails or masking looks wrong | `sp_path` is missing, unreadable, or trained without the repo’s special symbols | Confirm the file exists and that the model recipe includes `<cls>`, `<sep>`, `<pad>`, `<mask>`, `<eod>`, and `<eop>` | Rebuild the model with the README SentencePiece recipe |
| Preprocessing finds no files | `input_glob` matches nothing, or `task` is outside the shard range | Check the glob expansion and `task < num_task` | Fix the glob or worker indexing before rerunning |
| Raw text treats paragraphs incorrectly | `<eop>` is missing, malformed, or the tokenizer recipe does not preserve it | Verify `<eop>` appears as a line suffix in raw text | Keep `<eop>` at the end of the sentence line and include it as a user-defined symbol |
| Id-mode preprocessing fails on parse | A line contains non-integer tokens, text, or a literal `<eop>` marker | Run the bundled validator in `--mode ids` | Convert the corpus to integer ids or switch back to raw-text mode |
| Training cannot find the record-info files | `record_info_dir` points to the wrong directory, or preprocessing and training fingerprints differ | Compare `seq_len`, `reuse_len`, `bi_data`, `mask_alpha`, `mask_beta`, `num_predict`, `uncased`, and `split` | Point `record_info_dir` at the directory containing `record_info-*.json` that matches the preprocessing run |
| Record-info naming looks inconsistent across workers or passes | `num_task`, `task`, and `pass_id` were mixed up | Confirm each worker has a unique `task`, the same `num_task`, and an intentional `pass_id` sequence | Re-run preprocessing with a stable worker index plan |
| `perm_size` or sequence-layout assertions fail | `perm_size`, `reuse_len`, and `seq_len` are not compatible | Check `reuse_len < seq_len - 3`, `perm_size <= reuse_len`, and `perm_size <= seq_len - reuse_len` | Lower `perm_size` or adjust the sequence layout |
| GPU training crashes when saving checkpoints | `save_steps` was omitted, or `train_batch_size` is not divisible by `num_core_per_host` | Inspect the generated GPU command | Add `--save_steps=...` and align the batch size with the tower count |
| TPU training import fails in a CPU-only legacy env | `train.py` still depends on `tensorflow.contrib.tpu.proto` through `tpu_estimator.py` | Read the import error; it is an environment limitation, not a data issue | Use a TPU-capable TensorFlow 1.x environment or switch to the GPU entrypoint |
| Training reruns keep overwriting source checkpoints | `model_dir` and `init_checkpoint` were pointed at the same location | Compare the two paths before training | Keep the output directory separate from the checkpoint source |
| Long-run jobs are hard to resume | Legacy TensorFlow 1.x pretraining is slow and stateful | Check whether the command builder included the right `save_steps` and `model_dir` | Save into a stable `model_dir` and resume from the latest checkpoint |

## Fast preflight checklist

- Validate the corpus with the bundled validator first.
- Confirm the SentencePiece model exists and preserves the required symbols.
- Confirm preprocessing and training use the same `seq_len`, `reuse_len`, `bi_data`, `mask_alpha`, `mask_beta`, `num_predict`, and `uncased`.
- Keep `model_dir` distinct from `init_checkpoint`.
- For TPU runs, make sure the environment actually supports the legacy TF1 TPU stack.

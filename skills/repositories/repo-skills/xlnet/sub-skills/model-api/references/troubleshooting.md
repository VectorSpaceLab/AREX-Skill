# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `KeyError` or missing-field failure while loading `xlnet_config.json` | The config JSON is missing one of the required keys, often `untie_r`. | Run `scripts/inspect_xlnet_config.py` and add all eight required keys: `n_layer`, `d_model`, `n_head`, `d_head`, `d_inner`, `ff_activation`, `untie_r`, and `n_token`. Make sure the config matches the checkpoint you are loading. |
| Config loads, but a custom head crashes on shape mismatch | You picked the wrong XLNet output for the head or forgot the `[len, bsz]` tensor layout. | Use `get_pooled_out()` for sequence-level heads and `get_sequence_output()` for token/span heads. Remember that downstream feature tensors are usually transposed before calling `XLNetModel`. |
| `AttributeError: module tensorflow has no attribute contrib` or similar import errors | The codebase is legacy TensorFlow 1.x graph code, not TensorFlow 2.x code. | Use a TensorFlow 1.x runtime, ideally the same legacy family as the repo. Do not expect TF2-only environments to work unchanged. |
| `Descriptors cannot be created directly` or another protobuf descriptor error | The protobuf package is too new for the legacy generated descriptors used by TF1.x. | Pin `protobuf==3.20.x`. If you need a last-resort workaround, set `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python`, knowing that it is slower. |
| `DuplicateFlagError` when importing more than one CLI module | Several CLI modules define overlapping absl flags in the same interpreter. | Import or inspect those modules in separate Python processes. Do not bulk-import `run_classifier`, `run_squad`, `run_race`, or `train_gpu` in one process. |
| SentencePiece load failure or tokenization helper errors | `spiece.model` is missing, unreadable, or pointing at the wrong file. | Use the SentencePiece model from the released zip and confirm the file exists before calling `encode_pieces()` or `encode_ids()`. |
| Restore uses the wrong files or starts from scratch | `model_dir` and `init_checkpoint` were confused. | Keep `model_dir` as the output workspace and `init_checkpoint` as the source checkpoint prefix. |
| `train.py` or `tpu_estimator` import fails in the CPU-only inspection environment | The TPU-only contrib pieces are not available in that runtime. | Treat TPU pretraining as an optional backend path. The model API sub-skill should still work for CPU inspection, config validation, and tokenization. |
| `model_utils.get_train_op()` raises about multi-GPU weight decay | The helper forbids `weight_decay > 0` on multi-GPU non-TPU training. | Turn off weight decay, switch to TPU, or implement a custom optimizer path. |

## Quick diagnosis order

1. Validate the config JSON with `scripts/inspect_xlnet_config.py`.
2. Check that the checkpoint prefix, model directory, and SentencePiece model all point to the right files.
3. Confirm the runtime is TensorFlow 1.x if you see `tf.contrib` or `tf.app` import errors.
4. Check protobuf and absl-flag issues before debugging the model graph itself.
5. Only then investigate head shapes, pooling choice, or checkpoint variable-name mismatches.

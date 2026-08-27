# Conversion and Deployment Troubleshooting

| Symptom / error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `No module named tensorflow.contrib.lite` | TensorFlow build/version lacks TF1 contrib-lite path. | Use a compatible TensorFlow 1.x environment; verify with execution-config runtime probe. |
| No `.meta` file found | Model directory is incomplete or not the evaluation checkpoint directory. | Run `check_conversion_artifacts.py`; point `--model_dir` at the directory containing `model.ckpt.meta` and checkpoint shards. |
| Input/output collection index error | Graph lacks expected `images_final` or `logits_final` collections. | Use graph collection editing only after identifying correct tensor names; pass `--input_coll`/`--output_coll` if custom names exist. |
| `unable to determine data_format` | Graph does not contain a recognizable Conv2D op or graph import failed. | Verify the checkpoint was produced by a supported model helper and conversion is not pointed at an unrelated graph. |
| TFLite converter fails on unsupported op | Model graph contains ops unsupported by the old TFLite converter. | Replace/drop unsupported training-only ops, try post-quantization or a simpler export path, or keep PB deployment. |
| Dropout remains in exported graph | Training graph was exported without replacing/dropout identity swap. | Use the export path that replaces dropout layers or rebuild eval graph without dropout. |
| Channel-pruned export does not shrink model | Kernels are not actually zeroed/pruned or `--enbl_chn_prune` was not selected. | Confirm the checkpoint came from a pruning learner and inspect pruned variables before export. |
| Quantized export has accuracy drop | Post-training quantization or mismatched calibration/default ranges. | Prefer `uniform-tf` quantization-aware training when possible; record mean/std/default ranges. |
| Benchmark script cannot find input/output tensor | Names omit `:0`, include import prefix mismatch, or use wrong graph artifact. | Inspect graph tensors and pass exact names expected by the benchmark utility. |

## Safe debugging order

1. Validate model directory structure with the bundled checker.
2. Verify TensorFlow 1.x and `tf.contrib.lite` import.
3. Inspect or set input/output collection names.
4. Run conversion on a copy of model artifacts.
5. Test PB/TFLite outputs with a tiny known input before mobile deployment.
6. Benchmark only after functional correctness is established.

## Stop conditions

Stop before deleting checkpoints, rewriting graph collections in-place, running conversion on the only copy of a model directory, downloading model artifacts, or building a mobile app unless the user explicitly asks for that action.

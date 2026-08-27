# Troubleshooting

Use this as a symptom-to-recovery checklist.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `tensor name not found` or predictor builds but fetches the wrong tensor | `input_names` / `output_names` do not match the graph, or you are using an op name where a tensor name is needed | Expose the endpoint with `tf.identity(..., name='...')`, verify the exact graph tensor name, and normalize names with `get_op_tensor_name(name)`. |
| Predictor expects the wrong number of inputs | The config and tower signature do not agree, or the input signature names changed | Re-check `PredictConfig(input_signature=..., input_names=...)`, keep input names unique, and confirm the built tower actually consumes those tensors. |
| Checkpoint load fails with missing variables | Variable names in the graph and checkpoint are not identical | Inspect the checkpoint with `scripts/inspect_checkpoint.py`, then rename the graph variables or remap the checkpoint keys before calling `SmartInit`. |
| Checkpoint load fails with shape mismatch | The restored tensor shape differs from the graph variable shape | Fix the architecture first. Only use `ignore_mismatch=True` or relaxed restore behavior when the reshape / cast is truly intentional. |
| Restore warns about unused / missing names | The graph and checkpoint only partially overlap | Verify whether this is expected transfer learning. If not, compare the variable lists and make the inference graph match the checkpoint names exactly. |
| Importing a training metagraph causes duplicate nodes, name clashes, or bizarre fetch failures | A training metagraph was imported on top of a non-empty graph | Do not use the training metagraph for inference. Rebuild a clean inference graph and restore only the needed weights. |
| `export_compact()` fails during optimization | TensorFlow graph transformation could not prune or freeze the graph cleanly | Retry with `optimize=False`. If that still fails, use `export_serving()` or keep the checkpoint and run inference from a clean graph. |
| SavedModel export works but serving integration is still awkward | You need a very specific deployment contract that TensorFlow Serving does not match | Keep the export boundary at SavedModel and document the rest outside Tensorpack. Do not try to make this sub-skill own the full serving stack. |
| Caffe conversion fails with import or proto errors | Caffe Python bindings, `protoc`, or the model files are missing | Install the Caffe runtime, ensure the `.prototxt` and `.caffemodel` exist, and rerun `python -m tensorpack.utils.loadcaffe ...`. |
| Inference scripts crash on image display calls | The environment has no `DISPLAY` / GUI backend | Use file outputs only (`cv2.imwrite`, `np.save`) and avoid interactive windows or notebook-only viewers. |
| TensorFlow graph code breaks under eager execution | The runtime is using TF 2 eager mode instead of graph mode | Switch to `tensorpack.tfv1` / `tf.compat.v1` style graph mode and disable eager before building the graph. |

## Fast recovery pattern

1. Inspect the checkpoint or `.npz` file with `scripts/inspect_checkpoint.py`.
2. Build a clean inference graph with the exact tensor names you want to fetch.
3. Load weights with `SmartInit`.
4. If export fails, fall back from compact graph to SavedModel.
5. If the task needs Caffe or a GUI, check the dependency note before assuming the script is broken.

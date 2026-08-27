# Troubleshooting

This page gathers serving-specific failures for the TensorFlow Serving clients, the minimal benchmark helper, and the legacy HTTP wrapper.

## Connection and server issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `UNAVAILABLE`, `Connection refused`, or a deadline/timeout error | The serving process is not running, the host/port is wrong, or a firewall/forwarding issue blocks the port. | Confirm the server command, verify the port, and retry with `scripts/predict_dense.py --dry-run` or `scripts/predict_sparse.py --dry-run` first. |
| Response arrives but the prediction looks wrong | `model_name`, `model_version`, or `signature_name` does not match the export. | Check the export command in the training sub-skill and compare the request contract in `references/python-grpc-client.md`. |
| Sparse request fails on `indexs`, `ids`, `values`, or `shape` | Dense and sparse tensor names were mixed, or the sparse coordinate lengths do not match. | Rebuild the request from the sparse contract and confirm `nnz == len(ids) == len(values)`. |
| Dense request shape mismatch | The feature rows do not match the exported feature width. | Check the dense contract and the model's expected `feature_size`. |

## Request-construction mistakes

- Dense requests must keep `keys` as `int32` and `features` as `float32`.
- Sparse requests must keep the source spelling `indexs`; do not rename it to `indices` when talking to the exported graph.
- `model_version` is optional. If the server should use the latest version, leave it unset.
- `signature_name` is only needed when the export exposes multiple signatures or the default signature is not the right one.

## Source-client quirks

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `python_predict_client/predict_client.py --help` exits with `Unknown command line flag 'help'` | The source script uses `tf.app.flags` and runs its main logic immediately. | Use the bundled `scripts/predict_dense.py` or `scripts/predict_sparse.py`, which provide a proper help surface and dry-run mode. |
| Source sparse or dense clients rely on generated local `pb2` files | The original scripts were coupled to the checkout's generated protobuf files. | Use the bundled helpers, which import the public `tensorflow_serving.apis` modules instead. |

## Minimal benchmark issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Local benchmark output is much faster than gRPC benchmark output | The benchmark path changed from local NumPy/TensorFlow math to live serving. | Make sure the report names the benchmark mode (`local-latency`, `grpc-latency`, or `grpc-qps`). |
| `grpc-latency` or `grpc-qps` fails | The server is not listening or the model contract is wrong. | Reuse the dense/sparse dry-run helpers to confirm the payload before contacting the server. |

## Legacy HTTP wrapper issues

- `No model found, exit now` means the checkpoint directory or `.meta` file is missing for the Django wrapper.
- JSON field mismatches usually mean the checkpointed graph collections no longer match the code.
- Treat the Django wrapper as a legacy pattern; TensorFlow Serving is the preferred serving path.

## Alternate client and toolchain issues

- Java/Scala/Spark examples need Maven, Scala, Spark, and often Hadoop classpaths.
- Go examples need `protoc` and Go protobuf/gRPC plugins.
- C++ examples need Bazel and the TensorFlow Serving build tree.
- Android and iOS examples need their native mobile toolchains.

If the user only wants to understand request shape, stay in the Python helpers and avoid describing the external build systems as if they were part of the generated runtime skill.

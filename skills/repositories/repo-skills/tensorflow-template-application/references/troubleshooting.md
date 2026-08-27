# Troubleshooting

This page covers cross-cutting issues that affect multiple sub-skills.

## TensorFlow 1 vs TensorFlow 2

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `AttributeError: module 'tensorflow' has no attribute 'contrib'` | A TensorFlow 2.x install was used. | Pin `tensorflow==1.15.5` in a fresh environment and rerun the smoke check. |
| Missing `tf.app`, `tf.Session`, or `tf.python_io` | The environment is not the TF1-era stack this repo expects. | Install the TF1-compatible package set from `references/installation.md`. |

## Import-time flag conflicts

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `DuplicateFlagError` when importing both dense and sparse trainers | Both trainers register global `tf.app.flags` on import. | Run them in separate Python processes and use the bundled command builder instead of importing both in one program. |
| `Unknown command line flag 'help'` in the source serving client | The source client uses `tf.app.flags` and does not provide a standard argparse help path. | Use the bundled Python serving helpers instead of the original client scripts. |

## Data and shape mismatches

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `FixedLenFeature` or tensor shape errors in dense training | The CSV/TFRecord width does not match `feature_size`. | Inspect the records with the data-preparation sub-skill and confirm the converter used the right schema. |
| Sparse `ids` and `values` lengths differ | The sparse LIBSVM conversion or request construction is malformed. | Rebuild the sparse TFRecords or request payload and confirm the sparse contract. |
| Dense and sparse fields are mixed | A record was inspected with the wrong schema. | Use the correct dense or sparse inspector helper before training or serving. |

## Checkpoints, exports, and paths

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `The model exists in path` during export | The export version directory already exists. | Choose a new version or remove the stale export directory. |
| `No checkpoint found` before inference/export | Training has not produced a checkpoint yet. | Restore from a real checkpoint or train first. |
| Relative path errors in the old HTTP wrapper | The wrapper assumes a relative checkpoint layout from the repo checkout. | Prefer the TensorFlow Serving path or the bundled gRPC helpers. |

## Serving failures

- `UNAVAILABLE`, `Connection refused`, or `deadline exceeded` usually means the serving process is not listening on the requested host/port.
- A successful connection with a bad prediction usually means the model name, version, signature, or input tensor shapes are wrong.
- For the sparse client, the source spelling of the coordinate tensor is `indexs`; do not rename it when talking to the exported graph.
- If the live request is failing, first run the serving helper in dry-run mode to confirm the request contract.

## Optional dependency gaps

- `tensorflow-serving-api` and `grpcio` are needed for the Python serving helpers' live gRPC path.
- `Django` and `pydicom` are only needed for the legacy reference workflows.
- Java, Go, C++, Android, and iOS examples depend on external toolchains and are intentionally reference-only in the generated skill.

## When to escalate

If a failure falls outside these patterns, route to the nearest sub-skill troubleshooting page:

- `sub-skills/data-preparation/references/troubleshooting.md`
- `sub-skills/training-and-export/references/troubleshooting.md`
- `sub-skills/serving-and-clients/references/troubleshooting.md`

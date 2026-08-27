# Model Export Troubleshooting

## When To Read

Read this when freezing fails, the frozen PB cannot be converted, the MNN runtime cannot open the converted model, or output tensors/config fields are not found. For the normal workflow, read [mnn-export.md](mnn-export.md) first.

## Quick Diagnostic Order

1. Confirm a valid checkpoint prefix exists. If not, route to [../../training/SKILL.md](../../training/SKILL.md).
2. From this sub-skill directory, run the bundled helper's help or node-name check without building a graph:

   ```bash
   python scripts/freeze_lanenet_model.py --help
   python scripts/freeze_lanenet_model.py --print-node-names
   ```

3. Run the freeze command from [mnn-export.md](mnn-export.md#what-the-freeze-does) with `--repo-root <lanenet-repo-root>` so imports and config loading resolve correctly.
4. Only attempt PB-to-MNN conversion after the `.pb` exists and an external `MNNConverter` binary is available.

## Checkpoint Restore Or Moving Average Mismatch

The freeze helper restores `ExponentialMovingAverage` variables, matching the repository training/export graph. If restore errors mention missing moving-average keys, shape mismatches, or absent variable names, verify that the checkpoint was produced from the same LaneNet configuration and inspect it with `tf.train.list_variables(<checkpoint-prefix>)` in a TensorFlow 1.x environment before changing any export node names.

## Failure Matrix

| Symptom or error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `Checkpoint was not found`, `Not found: Key`, or TensorFlow cannot open a path | User passed a missing checkpoint, the checkpoint state file named `checkpoint`, a `.meta` file, or a prefix outside the current machine. | Pass the checkpoint prefix such as `model.ckpt-10000`. A trailing `.index` is acceptable because the bundled helper strips it. If no checkpoint exists, create one via [../../training/SKILL.md](../../training/SKILL.md). |
| `Key ... ExponentialMovingAverage not found`, `Assign requires shapes of both tensors to match`, or many variables are missing on restore | The freeze graph restores moving-average variables. The checkpoint may have been saved without EMA variables, from a different front-end/config, or from a modified model scope. | Prefer a checkpoint produced by the matching LaneNet training workflow. Inspect variables with `tf.train.list_variables(<checkpoint-prefix>)` in a TensorFlow 1.x environment. Do not rename output nodes to work around restore mismatch; fix the checkpoint/model compatibility first. |
| `No module named tensorflow`, `AttributeError` from TensorFlow APIs, or protobuf descriptor errors | The freeze helper requires TensorFlow 1.x-compatible APIs; TensorFlow 1.15 with protobuf `<=3.20.x` is the verified runtime family. | Use a TensorFlow 1.15-compatible Python environment. If TensorFlow imports fail after dependency resolution, pin protobuf to a 3.20.x release. CPU freezing is acceptable once the checkpoint exists; CUDA is mainly needed for validated training. |
| `Config file: ./config/tusimple_lanenet.yaml, can not be read`, `No module named lanenet_model`, or `No module named local_utils` | The repo config loader reads the YAML file relative to the current working directory, and LaneNet modules must be importable. | Use the bundled helper with `--repo-root <lanenet-repo-root>`. If writing a custom script, change to the repo root and put that root on `PYTHONPATH` before importing LaneNet modules. |
| Frozen PB was written but MNN conversion reports unsupported ops or malformed graph | The external converter version may not support the TensorFlow graph or the PB was not produced from the expected LaneNet test graph. | Confirm the frozen nodes are the fixed names from [mnn-export.md](mnn-export.md#what-the-freeze-does). Re-run conversion with the local converter's documented TensorFlow flags. If the converter still rejects the graph, treat it as an external MNN/toolchain limitation. |
| `MNNConverter: command not found`, missing converter build directory, or converter flag errors | The MNN converter is not part of this generated skill tree and was not verified in the Python environment. | Install or build the MNN converter externally, then run its `--help`. Use the command shape in [mnn-export.md](mnn-export.md#pb-to-mnn-converter-shape) only after adapting binary name/flags to that version. |
| MNN runtime cannot find `lanenet/final_binary_output` or `lanenet/final_pixel_embedding_output` | The graph was frozen with different node names, conversion pruned/renamed outputs, or the C++ runtime queries names that are absent from the converted model. | Freeze with the bundled helper without changing output-node names. Use `python scripts/freeze_lanenet_model.py --print-node-names` as the source of truth. If a converter optimization renames tensors, update the C++ runtime and config expectations together instead of only editing docs. |
| `Construct lanenet mnn interpreter failed` or the runtime immediately reports initialization failure | `model_file_path` in the MNN config points to a nonexistent or unreadable `.mnn` file, or the process cannot expand the path. | Set `model_file_path` to a path the C++ process can open. Avoid unexpanded `~` unless the application expands it. Confirm file permissions and that conversion produced a non-empty `.mnn` file. |
| Lane masks are empty, too sparse, or over-merged in the MNN runtime | DBSCAN config values are too strict/loose for the converted model or target camera domain. | Keep `pix_embedding_feature_dims=4`. Tune `dbscan_neighbor_radius` and `dbscan_core_object_min_pts` in small steps. Lower `dbscan_core_object_min_pts` can recover sparse lanes; increasing it can suppress noise. |
| C++ compilation, OpenCV/MNN include, DBSCAN header, or mobile package errors | Full C++/mobile build integration is outside this skill; the repo evidence only establishes config keys, tensor names, preprocessing, and runtime postprocess expectations. | Verify the external MNN application/toolchain independently. Use this sub-skill only to supply the frozen graph, converter command shape, config fields, node names, and preprocessing contract. |

## Stop Conditions

Stop and ask for environment/toolchain work instead of retrying the freeze when:

- There is no LaneNet checkpoint and the user has not asked to train one.
- TensorFlow 1.x cannot be installed or imported in the available environment.
- `MNNConverter` is unavailable and the user specifically needs `.mnn` output rather than only a frozen `.pb`.
- The user asks for full C++ build/mobile packaging beyond tensor names, config fields, preprocessing, and DBSCAN expectations.

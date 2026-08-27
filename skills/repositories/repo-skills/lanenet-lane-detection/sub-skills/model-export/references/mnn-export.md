# LaneNet Frozen PB and MNN Export

## When To Read

Read this when a user has a LaneNet TensorFlow checkpoint and asks for a frozen `.pb`, a `.mnn` model, mobile deployment preparation, MNN output tensor names, or MNN runtime configuration. For failed exports, pair this with [troubleshooting.md](troubleshooting.md).

## What The Freeze Does

The freeze helper builds the LaneNet test graph, restores a checkpoint through the moving-average restore map, converts variables to constants, and writes a frozen TensorFlow GraphDef.

Verified function and CLI contract:

- Python API: `convert_ckpt_into_pb_file(ckpt_file_path, pb_file_path)`
- Bundled helper: [../scripts/freeze_lanenet_model.py](../scripts/freeze_lanenet_model.py)
- Required checkpoint: a checkpoint prefix compatible with the LaneNet training graph, preferably one created by the training workflow with moving-average variables.
- Graph input shape: batch `1`, height `256`, width `512`, channels `3` (`NHWC`).
- Frozen nodes:
  - `lanenet/input_tensor`
  - `lanenet/final_binary_output`
  - `lanenet/final_pixel_embedding_output`

Typical command from this sub-skill directory:

```bash
python scripts/freeze_lanenet_model.py \
  --repo-root <lanenet-repo-root> \
  --weights_path <checkpoint-prefix> \
  --save_path <output.pb>
```

Notes for future agents:

1. Use a checkpoint prefix such as `model.ckpt-10000`; do not pass only the checkpoint state file named `checkpoint`. The bundled helper strips a trailing `.index` suffix if a user supplies it.
2. The helper changes into `--repo-root` before importing LaneNet modules because the repo config loader reads the YAML config relative to the current working directory.
3. TensorFlow 1.15 with protobuf `<=3.20.x` is the verified runtime family. Freezing can run on CPU after a checkpoint exists, although the verified training environment used CUDA.
4. If the checkpoint does not contain moving-average variables, the default restore map may fail. See [troubleshooting.md](troubleshooting.md#checkpoint-restore-or-moving-average-mismatch).

## PB To MNN Converter Shape

The MNN converter is external and is not bundled. After producing `<output.pb>`, use the converter binary from a local MNN toolchain. The command shape is:

```bash
MNNConverter -f TF \
  --modelFile <output.pb> \
  --MNNModel <lanenet.mnn> \
  --bizCode MNN
```

Treat this as a reference recipe, not a verified local command. The converter name and flags can vary by MNN release; confirm against the installed converter's `--help` before running. Do not use the repository's old shell wrapper as a runtime dependency, because it hardcodes converter and checkpoint assumptions.

## MNN `config.ini` Fields

The optional MNN runtime expects a `LaneNet` section with these fields:

```ini
[LaneNet]
model_file_path=<path-to-lanenet.mnn>
pix_embedding_feature_dims=4
dbscan_neighbor_radius=0.4
dbscan_core_object_min_pts=500
```

| Field | Meaning | Practical guidance |
| --- | --- | --- |
| `model_file_path` | Path passed to the MNN interpreter to load the converted model. | Use a path the C++ process can open. Avoid relying on shell-only `~` expansion unless the application explicitly expands it. |
| `pix_embedding_feature_dims` | Pixel embedding vector dimension consumed by DBSCAN. | Keep `4` for the exported LaneNet graph; the C++ code assumes four-channel embedding output. |
| `dbscan_neighbor_radius` | DBSCAN neighborhood radius/epsilon for embedding clustering. | Increase/decrease cautiously for mobile data; too small can fragment lanes, too large can merge lanes. |
| `dbscan_core_object_min_pts` | Minimum neighbor count for a DBSCAN core object. | Lower values are more permissive on sparse masks; higher values reject noise but can drop thin lanes. |

## C++ Runtime Expectations

The evidence-backed C++ runtime flow is:

1. Read a `LaneNet` config section containing the four fields above.
2. Create an MNN interpreter from `model_file_path` and a CPU session with four threads and high precision/power settings.
3. Fetch tensors by the exact names `lanenet/input_tensor`, `lanenet/final_binary_output`, and `lanenet/final_pixel_embedding_output`.
4. Preprocess each image by converting to float, resizing to the graph input size, dividing by `127.5`, then subtracting `1.0`.
5. Convert the binary output to an 8-bit mask by multiplying by `255`.
6. Interpret the pixel embedding output as four-channel floating-point features, normalize gathered foreground samples, and cluster them with DBSCAN using the config fields.

This sub-skill does not provide C++ build instructions, MNN headers/libraries, DBSCAN headers, OpenCV linking, or mobile packaging steps. If a user asks for full C++ integration, state that the LaneNet repo contains only evidence for the expected config, tensor names, preprocessing, and postprocess behavior; the external MNN application/toolchain must supply the rest.

## Limitations

- No pretrained weights or checkpoint are bundled. Route checkpoint creation to the [training sub-skill](../../training/SKILL.md).
- MNN conversion is reference-only unless `MNNConverter` is present and verified in the user's environment.
- The frozen graph is tied to the LaneNet test graph and fixed node names above; changing model front-end, embedding dimensions, or output node scopes can invalidate MNN runtime assumptions.
- The optional C++ runtime and MNN build are not part of this generated skill tree.

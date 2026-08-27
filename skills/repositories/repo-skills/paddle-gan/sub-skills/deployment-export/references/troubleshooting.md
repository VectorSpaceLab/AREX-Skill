# Troubleshooting

## Export problems

### Checkpoint keys do not match
Symptoms:
- a branch is missing from the export,
- the exported file tree contains only one prefix,
- the checkpoint came from a different model family.

Typical fixes:
- confirm the model family and checkpoint source match,
- for CycleGAN, ensure both `netG_A` and `netG_B` are present,
- for Wav2Lip, ensure the `netG` path is the one being loaded,
- re-check the export prefix with the bundled checker.

### `inputs_size` parsing fails
Symptoms:
- the export wrapper rejects the size string,
- semicolons or commas are misread by the shell.

Typical fixes:
- keep the string quoted when semicolons are used,
- use comma-separated integers inside each shape,
- make sure the number of shapes matches the export layout,
- remove trailing separators.

### Exported files are missing
Symptoms:
- `.pdmodel` or `.pdiparams` are absent,
- the output prefix is empty,
- one branch appears to have overwritten another.

Typical fixes:
- confirm the output directory exists and is writable,
- check whether a forced shared prefix would clobber a multi-net base export,
- use the default per-net naming when the model uses the generic export loop,
- inspect the generated tree with `scripts/check_exported_model.py`.

### Serving export tree is missing
Symptoms:
- the static files exist but `serving_client/` and `serving_server/` do not,
- a Serving deployment request arrives before the export was regenerated.

Typical fixes:
- re-run export with Serving enabled,
- confirm the Serving runtime is installed before trying to consume the tree,
- keep Serving work as reference-only unless the task explicitly authorizes it.

## Static inference problems

### `model_path` points to the wrong thing
Symptoms:
- the inference helper cannot open `.pdmodel` or `.pdiparams`,
- the model path looks like a directory instead of a prefix.

Typical fixes:
- pass the prefix without the file suffix,
- confirm the prefix exists after export,
- re-run the bundled checker on the prefix.

### `model_type` does not match the export
Symptoms:
- inference starts but the data branch crashes,
- the input keys do not line up with the selected model family.

Typical fixes:
- choose the branch that matches the exported family,
- use the config that defines the same dataset/test layout,
- do not expect a generic image branch to work for a sequence or audio branch.

### Optional benchmark logging fails
Symptoms:
- the CycleGAN inference branch complains about optional benchmark tooling,
- the core predictor is fine but the benchmark logger is missing.

Typical fixes:
- treat the optional logger as non-essential for export validation,
- keep the run on a simpler branch if you only need artifact checks,
- install the optional benchmark logger only if that path is required.

## TensorRT problems

### The wheel or library is not TRT-enabled
Symptoms:
- the runtime reports missing TensorRT symbols or operators,
- the model works in fluid mode but not in TRT mode.

Typical fixes:
- fall back to `fluid`,
- only request TRT after confirming the Paddle build includes it,
- check CUDA, cuDNN, and TensorRT version compatibility.

### Dynamic-shape errors
Symptoms:
- `some trt inputs dynamic shape info not set`,
- unsupported subgraph warnings,
- batch-axis slice warnings.

Typical fixes:
- increase `min_subgraph_size`,
- provide dynamic-shape ranges for every relevant feed name,
- use `fluid` when the model or backend does not justify TRT.

## Serving / Lite / C++ problems

### Serving cannot start
Symptoms:
- the service tree exists but the server import fails,
- the runtime version is too old,
- the client config does not match the exported names.

Typical fixes:
- confirm Paddle Serving 0.6+,
- confirm the generated feed/fetch names match the exported tree,
- keep server startup out of the default drafting flow.

### Lite conversion or mobile prep fails
Symptoms:
- `.nb` conversion is missing,
- the Android toolchain is incomplete,
- the mobile route asks for operators that the build does not include.

Typical fixes:
- confirm Paddle-Lite, Android NDK, and the extra CV operators are available,
- keep Lite as reference-only unless a mobile task is explicitly requested.

### C++ build or runtime fails
Symptoms:
- OpenCV or Paddle Inference headers are missing,
- GPU builds fail because the CUDA/cuDNN libraries do not match,
- the demo starts but cannot open the input video.

Typical fixes:
- confirm the C++ runtime prerequisites before trying to compile,
- use the exported model prefix and video path expected by the demo,
- keep C++ work reference-only unless a native deployment task is explicitly authorized.

## Entry point caveat

Some checkouts ship with a broken legacy console entry point.
If that happens, do not depend on it for routing; use the bundled helper scripts instead.

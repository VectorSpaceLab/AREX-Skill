# Model Artifacts

## Purpose

Read this before diagnosing missing weights, staging model files, or explaining what the repository's download scripts would have fetched. The bundled checker [../scripts/check_model_artifacts.py](../scripts/check_model_artifacts.py) validates file presence without making network requests.

## Expected model files

| Relative path | Workflow | Role |
| --- | --- | --- |
| `models/reference_model/model.caffemodel` | Caffe local-hints GUI and barebones notebook | Main colorization and distribution-prediction Caffe weights for the reference model. |
| `models/global_model/global_model.caffemodel` | Caffe global histogram transfer | Colorization model conditioned by a global color histogram. |
| `models/global_model/dummy.caffemodel` | Caffe global histogram transfer | Dummy weights used with `global_stats.prototxt` to extract a reference-image global color distribution. |
| `models/pytorch/pytorch_trained.pth` | PyTorch local-hints variant | PyTorch-trained weight file listed by the root fetch script. |
| `models/pytorch/caffemodel.pth` | PyTorch local-hints GUI/Docker default | Converted Caffe model weights used by the PyTorch GUI path. |

The repository includes prototxt/config files such as `models/reference_model/deploy_nodist.prototxt`, `models/reference_model/deploy_nopred.prototxt`, `models/global_model/deploy_nodist.prototxt`, and `models/global_model/global_stats.prototxt`; those are not substitutes for the large weight files above.

## Original download intent

The repository's historical fetch script lists HTTP URLs at `colorization.eecs.berkeley.edu/siggraph/models/` for the model artifacts. The generated skill does not bundle those model weights and does not download them automatically because downloads are network side effects and the weight files may be large.

If a user asks for exact acquisition, prefer this safe pattern:

1. Explain the expected relative target paths from the table above.
2. Tell the user to use the project's documented model source or a trusted mirror they approve.
3. After download, run the bundled checker to confirm all files needed for the selected workflow exist.
4. Do not claim model inference is verified until the selected Caffe or PyTorch runtime loads the file and runs a small inference.

## Workflow-specific requirements

### Local-hints PyTorch

Minimum expected file: `models/pytorch/caffemodel.pth` for the default PyTorch GUI path. The `--pytorch_maskcent` flag changes mask centering behavior for some PyTorch checkpoints; do not enable it blindly for the converted Caffe model unless the checkpoint source expects it.

### Local-hints Caffe

Minimum expected file: `models/reference_model/model.caffemodel`, plus the reference deploy prototxts. `ColorizeImageCaffe` may set in-gamut cluster centers in the prediction layer and set upsampling kernels after loading the Caffe net.

### Global histogram transfer

Minimum expected files: `models/global_model/global_model.caffemodel` and `models/global_model/dummy.caffemodel`, plus the global deploy and stats prototxts. This workflow is Caffe-only in this repository.

## Common symptoms

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| Caffe raises an error opening `model.caffemodel` | Reference Caffe weight is missing or staged in the wrong relative path | Run the bundled checker with the path to the user's checkout or staged artifact root. |
| PyTorch raises `FileNotFoundError` for `caffemodel.pth` | Converted PyTorch weight was not downloaded | Stage `models/pytorch/caffemodel.pth` and retry. |
| Global histogram notebook fails at `global_model.caffemodel` or `dummy.caffemodel` | Global weights were not fetched | Stage both global model files, not only the local-hints reference weight. |
| Prototxt exists but model load still fails | Weight file missing, incompatible backend, or stale relative path | Check both prototxt and caffemodel/pth files; then verify backend imports. |

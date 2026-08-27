# iGAN Cross-cutting Troubleshooting

Read this when an iGAN task fails before it clearly belongs to one sub-skill, or
when a failure mentions legacy dependencies, model/data artifacts, display, CUDA,
or command wiring.

## Legacy runtime stack

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ImportError: No module named theano`, `theano.sandbox.cuda`, or `dnn_conv` | The original code targets legacy Theano CUDA APIs. | Treat native generation/projection/training as unavailable until a compatible legacy Theano + CUDA/cuDNN stack is prepared. Use the relevant command builder for a reproducible handoff. |
| Python syntax/import works but runtime import fails in modern Python | The repo is Python2-era and imports deprecated packages/APIs. | Do not keep patching blindly. Record Python version, failing import, and whether the task only needs a dry plan or true native execution. |
| `ImportError: PyQt4` or `qdarkstyle` during UI launch | UI dependencies are missing; PyQt4 is often a system/legacy package. | If the user only needs non-UI generation, route to `constraint-generation`. If true UI is required, prepare a display-capable legacy environment first. |
| `cv2.cv.CV_DIST_L2` or OpenCV constant errors | Code predates newer OpenCV APIs. | For native UI use, pin an OpenCV version compatible with the legacy code or patch the constant after confirming the user's goal. Dry helpers avoid OpenCV. |
| `lasagne`, `scipy`, `PIL`, `fuel`, `h5py`, or `tqdm` missing | Projection or training extras are not installed. | Route to `image-projection` or `training-data` and install only the workflow-specific extras if native execution is required. |

## CUDA, cuDNN, and GPU checks

The documented runtime used a GPU-oriented Theano setup. A modern GPU alone is
not enough: the Theano version, CUDA runtime, cuDNN library, compiler, and Python
version must match. A CPU import check is not proof that generation, projection,
or training can run.

Before launching native code, confirm:

- The command includes intentional `THEANO_FLAGS` such as `device=gpu0` and
  `floatX=float32`, or the user explicitly chose a CPU/diagnostic path.
- A compatible model or dataset artifact is present.
- The task owner accepts compile time and possible GPU memory use.
- For UI tasks, a display or remote desktop session is available.

## Missing artifacts

| Artifact | Used by | Planner |
| --- | --- | --- |
| `*.dcgan_theano` model file | sample generation, UI, constraints, projection | `sub-skills/model-inference/scripts/igan_artifact_urls.py` |
| `caffe_reference_<layer>.pkl` AlexNet file | projection feature loss | `sub-skills/image-projection/scripts/igan_alexnet_urls.py` |
| `*.hdf5` dataset | training and batchnorm/predictor workflows | `sub-skills/training-data/scripts/igan_dataset_urls.py` |

Do not auto-download these files unless network use, external URLs, and disk
space are explicitly approved. The dataset archives range from tens of megabytes
to several gigabytes.

## Command and path mistakes

- The model file convention is `models/<model_name>.<model_type>`, usually
  `models/<model_name>.dcgan_theano`.
- Projection output defaults to the input image name with `_<solver>.png` before
  the extension when no output path is supplied.
- Constraint generation uses three separate images: color RGB image, color mask,
  and edge image. Use the constraint validator before native execution.
- The legacy training shell recipe contains a typo: it calls
  `batchnorm_precit_z.py`. The correct script name is `batchnorm_predict_z.py`.

## When to stop

Stop and ask for a narrower scope or a prepared environment when the requested
result requires actual generated images, UI interaction, projection output,
training checkpoints, or packed models but the runtime lacks the required
legacy dependencies, artifacts, GPU, display, or approved downloads. A dry-run
helper output is a plan, not a native result.

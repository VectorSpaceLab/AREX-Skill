# Cross-cutting troubleshooting

| Symptom | Likely cause | Next action |
|---|---|---|
| Ordinary Python import fails in `utils.Animation` | Legacy `numpy.core.umath_tests` dependency is incompatible with modern NumPy | Use bundled standalone format validators, or explicitly prepare and validate a pinned/modified numerical environment before relying on model code. |
| `torch.cuda.is_available()` is false or allocation fails | CPU-only framework, missing driver, occupied GPU, or incompatible wheel | Run the environment probe, select an available device, and treat CPU neural runs as partial verification rather than silently claiming CUDA coverage. |
| `bpy` is missing | Blender scripts were invoked with ordinary Python | Use a compatible Blender executable and the extra `--` separator; do not install arbitrary `bpy` into the research environment. |
| A script cannot find a file | The repository's legacy launchers assume a particular current directory and relative data layout | Use explicit absolute input/output/checkpoint/data paths and the bundled dry-run wrappers; never fix this by copying data into the source tree without review. |
| Model imports but inference cannot start | Checkpoint, `para.txt`, normalization NPZ, YAML, rest skeleton, or dataset split is missing/mismatched | Run the owning sub-skill's preflight and confirm the model/data version before changing code. |
| Results are overwritten or deleted | Legacy demo/evaluation/cleanup scripts use fixed result directories or shell `rm/cp` | Use a new output directory, inspect commands, preserve inputs and raw outputs, and opt into execution explicitly. |
| A format check passes but motion is wrong | BVH topology, rest pose, rotation order, coordinate system, scale, or contact joints disagree | Compare hierarchy/offsets/frame time and keep raw artifacts; parser success is not semantic validation. |

## Installation posture

There is no supported package metadata or one universal requirements file in the
source snapshot. Install only the dependencies for the selected route. Keep
Blender, OpenPose, datasets, checkpoints, and external FBX assets as explicit
user-provided prerequisites. TensorBoard, plotting, and probe dependencies are
optional unless the selected workflow needs them.

# Configuration and Model Troubleshooting

- **`ModuleNotFoundError: spconv`**: this is an environment/model-family
  dependency problem, not a config syntax error. Follow `runtime-ops`; do not
  replace it with a CPU claim.
- **Unknown registry type**: verify the component's import/registration path,
  exact case-sensitive `type`, and whether the package's model `__init__` has
  imported the defining module.
- **Class/task mismatch**: compare the number and order of `tasks`, class names,
  anchors, and head outputs. Dataset classes and checkpoint metadata must agree.
- **Shape or channel mismatch**: inspect voxel/pillar dimensions, reader output,
  backbone stage channels, neck inputs, and head input channels together.
- **Config parses but build fails**: parsing only executes config Python. Build
  failures may come from compiled ops, optional SDKs, or incompatible torch/CUDA.
- **Checkpoint loads but evaluation is wrong**: verify checkpoint class metadata,
  dataset split, coordinate convention, preprocessing, and score/NMS settings.

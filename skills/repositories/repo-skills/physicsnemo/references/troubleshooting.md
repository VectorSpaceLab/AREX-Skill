# Troubleshooting

## Install and import

- `ImportError` at `import physicsnemo`: verify the package is installed and `pip check` is clean.
- Missing module inside a family subpackage: the family may need an optional extra; inspect the relevant sub-skill’s dependency notes.
- Old Modulus import or renamed class: use the migration guidance and the model-selection sub-skill to map to the current import path.

## CUDA and backend issues

- A CPU import does not prove a CUDA workflow works.
- For distributed/domain-parallel routes, verify an actual CUDA-capable environment and the right torch backend before claiming success.
- If an optional backend such as NATTEN, Transformer Engine, RAPIDS, or DALI is absent, document the limitation and route to a workflow that does not need it.

## Data and config issues

- Many example workflows require external datasets, statistics, checkpoints, or generated fixtures. Do not treat those examples as smoke tests unless the needed assets are present.
- Datapipe failures often come from wrong file patterns, missing TensorDict keys, or a mismatch between sample layout and transform expectations.
- Mesh failures often come from non-simplicial inputs, bad cell ranks, duplicate vertices, or invalid topology.

## Long-example overrun

- If a workflow would launch a long training run, large download, or benchmark sweep, stop and route to the distilled reference instead of running it by default.
- For tiny validation, prefer bundled smoke scripts and small generated fixtures.

## Common PhysicsNeMo-specific mistakes

- Assuming every model family is imported from `physicsnemo.models` root.
- Assuming `validate_mesh` or other validation helpers live at the mesh root.
- Treating `ShardTensor` as a model-wide replacement instead of an input-scatter / domain-parallel mechanism.
- Using the active-learning driver for ordinary fixed-dataset training.
- Treating ONNX runtime inference as required for export; `onnxscript` may be needed for export, while `onnxruntime` is only needed for inference checks.

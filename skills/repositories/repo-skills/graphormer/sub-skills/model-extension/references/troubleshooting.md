# Graphormer model-extension troubleshooting

Use this guide when a model, architecture, task, or criterion extension does not appear in fairseq registries or fails at import/build time.

## Duplicate module names

Symptom examples:

- `Failed to import --user-dir=... because the corresponding module name (...) is not globally unique`
- Registries come from an unexpected Graphormer package or installed package.

Causes:

- The user-dir basename is already present in `sys.modules` from another path.
- A previous registry check imported a different package with the same module name.
- Multiple working trees or packages use the same top-level package name in a single long-lived process.

Fixes:

- Run registry checks in a fresh Python process.
- Use one intended user-dir per process.
- If developing a separate plugin, give its directory a unique Python package basename and update imports accordingly.

## `--user-dir` omitted or wrong

Symptoms:

- `--arch graphormer_base` or `--arch graphormer3d_base` is rejected.
- `--task graph_prediction` or `--criterion l1_loss` is missing from fairseq choices.
- The registry helper reports missing Graphormer models, tasks, architectures, or criterions.

Fixes:

- Pass `--user-dir <graphormer-package-dir>` to fairseq commands.
- For Python checks, call `fairseq.utils.import_user_module` before reading registries.
- Ensure the user-dir is the package directory containing `models/`, `tasks/`, and `criterions/`, not just a parent directory.

## Architecture not imported

Symptoms:

- The model name is present but a new `--arch` value is missing.
- `Cannot register model architecture for unknown model type` appears during import.
- An architecture file exists but its decorator never runs.

Causes and fixes:

- The file is private or skipped: rename files that start with `_` or `.`.
- The file has an import error before the decorator executes: run the registry helper and inspect its import error.
- The architecture is registered before the model is registered: import the model module first or register the architecture in a module that imports the base model.
- The architecture name duplicates an existing fairseq architecture: choose a unique name.
- You edited code in a process that already imported the user-dir: restart the Python process.

## Missing `num_classes`

Symptom:

- `Must set task.num_classes`
- Output projection size is invalid or equals a sentinel value.

Cause:

- `graph_prediction` defaults `num_classes` to `-1` and asserts that real runs set it to a positive value.

Fixes:

- Set `--num-classes 1` for scalar regression or binary logits.
- Set `--num-classes <class-count>` for multiclass classification.
- When building models programmatically, populate `cfg.num_classes` or `args.num_classes` before `setup_task` and `build_model`.

## Output shape or head mismatch

Symptoms:

- Criterion indexing fails at `logits[:, 0, :]`.
- Binary/multiclass loss reports target/logit shape mismatch.
- Checkpoint loading fails for `embed_out.weight` or output-layer bias.

Model facts:

- Graph-level criterions expect a model output shaped like `batch x tokens x num_classes` and use token `0` as the graph output.
- GraphMLP-style custom models can return `batch x 1 x num_classes` if they provide only graph-level predictions.
- The standard output head is a linear projection from `encoder_embed_dim` to `num_classes` plus a learned scalar bias.
- `share_encoder_input_output_embed=True` is not implemented in this model path.
- Pretrained output layers should be loaded only when the target task output shape is intentionally compatible.

Fixes:

- Return `logits.unsqueeze(1)` for graph-only custom models.
- Verify `num_classes` matches target dimensionality.
- For transfer learning, disable pretrained output-layer loading unless output dimensions match.
- If using a removed head or hidden-state output, use a compatible criterion or add an explicit output projection.

## `masked_tokens` not implemented

Symptom:

- Passing `masked_tokens` to `GraphormerEncoder.forward` raises `NotImplementedError`.

Fixes:

- Do not reuse masked-language-model fairseq code paths directly with this Graphormer encoder.
- Implement and test masked-token projection explicitly before exposing a masked objective.
- Route ordinary graph prediction to graph-token output criterions instead.

## FLAG perturbation mismatch

Symptoms:

- `graph_prediction_with_flag` fails because the model lacks `encoder_embed_dim`.
- Perturbations are created but do not affect the forward pass.
- Custom criterion ignores `sample["perturb"]`.

Fixes:

- Set `model.encoder_embed_dim` to the node hidden dimension.
- Accept `perturb=None` in the model/encoder forward method.
- Add perturbation to node features with shape `(batch, nodes, encoder_embed_dim)`, not to the graph token.
- Use a `_with_flag` criterion implementation that passes perturbation through to the model.

## Graphormer3D tensor shape failures

Symptoms:

- Tensor rank errors in distance, edge-type, or node-head operations.
- Energy loss works but node displacement loss has mask/broadcast errors.
- Tag or atom embeddings throw index errors.

Expected shapes:

- `atoms`: `(batch, nodes)` integer tensor with `0` padding.
- `tags`: `(batch, nodes)` integer tensor compatible with three tag embeddings.
- `pos`: `(batch, nodes, 3)` float tensor.
- `real_mask`: `(batch, nodes)` boolean-like tensor.
- Model return: `(eng_output, node_output, node_target_mask)` where `node_output` is `(batch, nodes, 3)` and `node_target_mask` is `(batch, nodes, 1)`.

Fixes:

- Validate padding and mask shapes before model invocation.
- Keep `atoms` within the model's atom embedding range.
- Keep `tags` within the tag embedding range.
- Ensure `targets.deltapos` is shaped `(batch, nodes, 3)` for `mae_deltapos`.

## Cython or compiled dependency import pitfalls

Symptoms:

- Registry import fails before custom code is reached.
- Errors mention Cython, `algos`, NumPy headers, `torch_geometric`, `dgl`, `ogb`, `lmdb`, or old fairseq/torch symbols.

Causes:

- Graphormer task imports pull in data wrappers and compiled graph preprocessing helpers.
- The fairseq user-dir stack is version-sensitive.
- Optional 3D and dataset packages may be absent in a minimal environment.

Fixes:

- First run the registry helper to identify the earliest import error.
- Install or activate a Graphormer-compatible inspection environment before blaming extension code.
- If a new extension does not need dataset imports, still remember that fairseq user-dir import may import tasks and therefore data dependencies.
- Keep generated helpers and diagnostics import-only; do not run native training or dataset download scripts while debugging registry visibility.

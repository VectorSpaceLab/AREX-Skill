# ShapeNetPart Troubleshooting

Use this table before reopening the source repository. The issues below are specific to the part segmentation scripts and their ShapeNetPart loaders.

## ROOT_DIR and stale `test.py` visualization path

`part_seg/test.py` contains a known `ROOT_DIR` bug: it appends `os.path.join(ROOT_DIR, 'data_prep')` and builds `DATA_PATH` from `ROOT_DIR`, but `ROOT_DIR` is never defined. It also appends `BASE_DIR/models` and `BASE_DIR/utils`, while the repository's `models/` and `utils/` directories are siblings of `part_seg/`, not children.

Other stale assumptions in the same script:

- it imports `PartDataset`, which expects `points/` and `points_label/` subdirectories, while the README's normal ShapeNetPart download uses one `.txt` file per shape with XYZ, normals, and labels;
- it hardcodes `NUM_CLASSES = 4`, but `pointnet2_part_seg` emits 50 global part logits;
- it does not restrict predictions through `seg_classes[category]` the way `evaluate.py` does;
- visualization uses `show3d_balls`, which may require a compiled renderer and a usable display/OpenCV setup.

Recommended fix pattern for a future agent:

1. Define `ROOT_DIR = os.path.dirname(BASE_DIR)`.
2. Append `ROOT_DIR/models` and `ROOT_DIR/utils`, not `BASE_DIR/models` and `BASE_DIR/utils`.
3. Choose the correct loader: `PartNormalDataset` for the normal README dataset, or `PartDataset` only for a real legacy `points/points_label` dataset.
4. Keep logits as 50-channel global labels, then restrict to the selected category's valid labels listed in [data-formats.md](data-formats.md#global-part-label-ranges).
5. Treat visualization as optional; if rendering fails, save arrays or colors first and debug `show3d_balls` separately.

Do not tell a user that the raw `test.py` command is verified runnable without these changes.

## ShapeNetPart split JSON and directory layout mismatches

Symptoms:

- dataset length is zero for `trainval` or `test`;
- `os.listdir` fails for a category directory;
- files exist but are ignored by the loader;
- a chosen single category has no samples even though other categories do.

Causes and actions:

| Cause | Why it happens | Action |
|---|---|---|
| Wrong dataset root | Source scripts hard-code `data/shapenetcore_partanno_segmentation_benchmark_v0_normal` relative to repo root | Symlink/copy data there or patch `DATA_PATH`; validate the exact target root |
| Split JSON token mismatch | Loaders use `d.split('/')[2]` as the shape id | Inspect JSON entry depth and basename; regenerate or patch split parsing if entries are not three-part paths |
| Normal vs legacy layout confusion | `PartNormalDataset` wants `<synset>/<id>.txt`; `PartDataset` wants `<synset>/points/<id>.pts` and `<synset>/points_label/<id>.seg` | Use `--format normal` or `--format legacy-points` with the validator |
| Empty selected category/split | Layout can be complete but split JSON may not include the requested category's ids | Run validator with `--class-choice` and without `--allow-empty-split` to make this an error |
| Malformed sample columns | Normal files need XYZ, normals, and label; legacy files need matching `.pts` and `.seg` rows | Let the validator sample files with `--strict-labels` |

## Category-label conditioning mistakes for the one-hot variant

The one-hot trainer uses `PartNormalDataset(..., return_cls_label=True)` and feeds `cls_labels_pl` into `pointnet2_part_seg_msg_one_hot.get_model(pointclouds, cls_labels, ...)`. The model one-hot encodes category ids at depth 16 and concatenates that signal into the final feature-propagation stage.

Common mistakes:

- using `pointnet2_part_seg_msg_one_hot` with `evaluate.py`; the evaluator expects only two placeholders and calls the plain model signature;
- filtering to a single category while expecting the all-category one-hot class-id behavior to remain meaningful;
- constructing category ids alphabetically or from an external table instead of the loader's `self.classes` mapping;
- restoring a one-hot checkpoint into the plain model or a plain checkpoint into the one-hot model.

Recovery:

1. For training, use `train_one_hot.py --model pointnet2_part_seg_msg_one_hot`.
2. For evaluation, either rely on the test evaluation inside `train_one_hot.py` or patch a separate evaluator to instantiate and feed `cls_labels_pl`.
3. Keep `synsetoffset2category.txt` stable between training and any adapted inference/evaluation code.
4. Use the command builder's `train-one-hot` workflow; it rejects the plain evaluator for one-hot models.

## Legacy Python 2 syntax and checkpoint-heavy execution

The part segmentation scripts use Python-2-style `print` statements and TensorFlow 1.x APIs. On modern Python/TF2 environments, syntax or import errors can appear before any dataset or model logic runs.

Typical symptoms:

- `SyntaxError: Missing parentheses in call to 'print'`;
- `AttributeError` for TensorFlow 1.x symbols such as sessions, summaries, or old utility APIs;
- restore errors from checkpoint/model mismatch;
- long runtime or large GPU memory use even for evaluation because the full PointNet++ graph and custom ops are needed.

Actions:

- Use a Python 2.7 or carefully ported Python 3 + TensorFlow 1.x-compatible runtime for native source scripts.
- Before launching training, validate commands and data with bundled scripts that do not import TensorFlow.
- Keep `--log_dir` separate for plain and one-hot runs; source scripts copy model/trainer files and write checkpoints into that directory.
- For native verification, use tiny fixtures and reduced `--num_point`, `--batch_size`, and `--max_epoch` only after the backend/custom-op path is proven ready.

## Optional GPU/custom-op backend missing

PointNet++ part segmentation models call set-abstraction and feature-propagation helpers that depend on custom TensorFlow operators. CPU-only import/data checks do not prove that model execution can run.

Symptoms:

- import errors for `tf_sampling`, `tf_grouping`, or `tf_interpolate`;
- `NotFoundError` or ABI errors when loading `*_so.so` files;
- CUDA/nvcc not found while compiling ops;
- graph builds but session execution fails at the first custom op.

Actions:

1. Separate **static/data work** from **native model execution**. The command builder and dataset validator are safe without custom ops.
2. For training/evaluation, check TensorFlow 1.x, CUDA toolkit/nvcc, compiler ABI, and compiled custom-op `.so` compatibility.
3. If custom ops are unavailable, report the backend as optional-blocked for ShapeNetPart native runs rather than claiming the model was verified.
4. Cross-route detailed custom-op diagnosis to the generated `model-apis-and-custom-ops` sub-skill when present.

## Command-generation pitfalls

| Pitfall | Why it matters | Safer behavior |
|---|---|---|
| Running `part_seg/train.py` from repo root | The script copies `train.py` with a relative shell command, which can copy the wrong file | Use `cd part_seg && python train.py ...` |
| Omitting `--model` for plain training | `train.py` default is the literal module name `model`, which does not exist in this repo | Always pass `--model pointnet2_part_seg` |
| Reusing one log directory for multiple variants | Checkpoints and copied model files can overwrite each other | Use distinct `log`, `log_msg_one_hot`, and `log_eval` directories |
| Treating original shell snippets as foreground commands | Source snippets redirect output and background the process | Decide explicitly whether to use `--background` and `--redirect-log` in the command builder |
| Evaluating one-hot with the plain evaluator | Placeholder/model signatures differ | Patch evaluator or use train-time evaluation |

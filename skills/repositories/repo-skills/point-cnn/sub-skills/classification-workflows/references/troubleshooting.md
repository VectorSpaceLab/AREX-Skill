# Classification troubleshooting

## `train_val_cls.py --help` fails during import

- **Likely cause:** the environment is missing TensorFlow 1.x-compatible imports or a dependency such as `h5py`, `plyfile`, `transforms3d`, or the legacy NumPy API expected by the checkout.
- **Recovery:** use the repository's legacy Python/TensorFlow environment; run the generic environment check from the root skill; then retry `python3 train_val_cls.py --help`. Do not replace `tf.contrib` or `tf.layers` ad hoc in a smoke run. The inspected environment imported TensorFlow 1.15 and exposed those APIs, but this is not a promise for another machine.
- **Boundary:** CPU import is not a GPU execution proof. Segmentation FPS has a separate custom-op requirement; classification itself does not call FPS.

## `FileNotFoundError` or an HDF5 open error

- **Likely cause:** a file list is missing, empty, or a line names a file that is not beside the list. `load_cls` uses the basename of each line and joins it to the file-list directory.
- **Recovery:** run `validate_classification_inputs.py` on both lists. Keep generated HDF5 files and their list in the same directory, and use one basename per line (for example `./train_0.h5`). Do not assume the current working directory controls resolution.
- **Related route:** use `data-preparation` for generating or repairing lists; this sub-skill does not download or rewrite datasets.

## `KeyError: 'data'`, `KeyError: 'label'`, or concatenation failure

- **Likely cause:** the file is a segmentation HDF5, has different key names, or has inconsistent sample counts. Classification expects `data` and `label`; `data` is rank 3 and `label` has one label per sample.
- **Recovery:** inspect keys and shapes read-only. Remove segmentation lists from the classification command. For normals, require `normal.shape[:2] == data.shape[:2]`; the loader appends normal channels before checking the selected setting.

## Data width or normal-feature mismatch

- **Symptom:** a split error around `setting.data_dim`, a graph shape error, or a model that receives no expected feature tensor.
- **Likely cause:** effective width is `data.shape[-1] + normal.shape[-1]` when `normal` exists. The trainer expects first three channels to be XYZ. `data_dim=4` is used by MNIST; most other checked-in settings use width 6.
- **Recovery:** select the setting matching the prepared representation. For normals, use a ModelNet/TU-Berlin-style 6-channel setting; for MNIST use 4-channel XYZ+pixel; for ScanNet/CIFAR use 6-channel XYZ+RGB. Do not fix this by changing `data_dim` without checking model feature semantics and checkpoint compatibility.

## Labels have the wrong range or class count

- **Symptom:** validator rejects labels, graph loss/metrics fail, or restore reports incompatible logits/variables.
- **Likely cause:** labels are not integer class ids in `[0, setting.num_class)`, or a checkpoint was trained with another class count.
- **Recovery:** verify conversion label remapping and the setting's class count: ModelNet40=40, ScanNet objects=17, TU-Berlin=250, Quick Draw=345, MNIST=10, CIFAR-10=10. Start a new output directory and use the matching setting for a checkpoint. Never reinterpret class ids merely to satisfy restore.

## `ImportError` or `ModuleNotFoundError` for `-m` / `-x`

- **Likely cause:** command was launched outside the project root, the model name is not importable, or the requested setting does not exist. The README's old ScanNet example names a setting absent from this checkout.
- **Recovery:** run from the project root, use `-m pointcnn_cls`, and choose a file actually present under `pointcnn_cls`, such as `scannet_x2_l4`. Run `py_compile` before training. For custom settings, place a self-contained module beside the model and verify every field listed in `configurations.md`.

## `AttributeError` for `rotation_order` in Quick Draw

- **Likely cause:** `quick_draw_full_x2_l6.py` defines `order`, but the trainer reads `rotation_order`.
- **Recovery:** treat Quick Draw as blocked at this source revision. In a controlled copy, rename/add the setting field to `rotation_order = 'rxyz'`, record the change, compile it, and only then use a bounded fixture. This is a source compatibility patch, not a benchmark result. Also ensure `num_parallel_calls` and the NPZ `categories.txt`/category files are present.

## A tiny fixture produces zero batches or hangs at input setup

- **Likely cause:** `keep_remainder=False` drops a dataset smaller than `batch_size`; a `map_fn` performs expensive Python work; or the setting's sample count is much larger than the fixture's point count.
- **Recovery:** use a setting with `keep_remainder=True`, override `--batch_size` to a small positive value, and make each sample have at least three coordinates and enough points for the selected smoke. Do not lower architecture `sample_num` by editing a production setting unless the fixture is explicitly a local test copy. Stop bounded tests rather than waiting on a full dataset.

## Checkpoint restore fails with shape, missing, or unexpected variables

- **Likely cause:** model/setting, class count, feature width, X-transformation choice, or architecture depth differs from the checkpoint. A checkpoint prefix must be supplied without an accidental wrong suffix/path.
- **Recovery:** validate inputs and setting first; use the exact model/setting pair that created the checkpoint; point `--load_ckpt` to the matching `ckpts/iter-<step>` prefix; or start a fresh output folder without `--load_ckpt`. Do not force partial restore in the stock trainer.

## Checkpoint or summary files are missing

- **Likely cause:** no training batch ran, the process was killed, the output folder was not writable, or the run wrote into a timestamped child different from the inspected folder.
- **Recovery:** inspect stdout/log for the printed root folder and training batch count. Confirm `ckpts/` and `summary/` under that root. For smoke tests, use a new writable folder and `--no_timestamp_folder --no_code_backup --log -`; keep `--epochs 1` and a small batch. Artifact meaning and TensorBoard inspection route to `evaluation-and-artifacts`.

## Timestamp/code-backup side effects surprise a smoke test

- **Likely cause:** timestamping and code backup are enabled by default; the trainer creates a new directory and copies its containing code tree before opening the session.
- **Recovery:** use a disposable output directory and explicitly pass `--no_timestamp_folder --no_code_backup`. Do not point `--save_folder` at the source or an existing valuable run. These flags change write behavior only; they do not make a run safe for untrusted data or prove correctness.

## Graph-mode or GPU runtime failure

- **Likely cause:** TensorFlow 2 eager execution, incompatible CUDA/cuDNN/driver ABI, unsupported compiler build, or a legacy op/runtime issue.
- **Recovery:** use TensorFlow 1.x graph mode and the environment plan; verify `tf.disable_eager_execution` is not being omitted in a custom harness. Keep classification tests separate from FPS tests. The inspected TensorFlow 1.15 import and A100 visibility were successful, while minimal GPU execution/custom-op smoke timed out; required FPS verification remains blocked/partial. Report a backend block rather than claiming a pass.

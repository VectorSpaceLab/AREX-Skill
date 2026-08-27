# Configuration and experiment troubleshooting

Use this table to classify the failure before editing a config or deleting an
experiment directory. Preserve the exact command, selected mode/folds,
source/snapshot paths, and first traceback line.

| Symptom | Likely cause | Safe diagnosis | Stop/repair rule |
|---|---|---|---|
| `ModuleNotFoundError: default_configs` or `configs` | Wrong working directory, missing repository/package import path, or the toy generator's top-level import assumption | Construct the module with the package/repository import context and inspect `sys.path`; use the bundled fixture helper instead of the original generator | Do not add arbitrary global `sys.path` entries to a published config; fix the workspace/package install and record the version |
| `ModuleNotFoundError` for model/data loader | `cf.model_path` or `<exp_source>/data_loader.py` is absent, or the source/snapshot version is mixed | Print resolved config paths and check files without importing the model | Align `exp_source`, snapshot, and checkout; do not substitute an unrelated model file |
| `KeyError` during config construction | Unsupported `model` dispatch key | Check the model-to-`add_*_configs` dispatch and available model implementation | Select a documented/version-supported key or stop; do not silently fall back to another detector |
| `AssertionError` on learning-rate length | `len(learning_rate) != num_epochs` | Evaluate both values after `configs()` construction | Fix the schedule explicitly; never truncate epochs implicitly |
| Shape/stride/anchor error after changing `dim` | 2D and 3D patch, channel, anchor, or box settings were mixed | Compare `dim`, `patch_size`, `pre_crop_size`, `n_channels`, model-specific shapes, and annotation dimensionality | Rebuild the dimension-dependent block and route model details to the model node |
| `FileNotFoundError` for `info_df.pickle` or `.npy` | `pp_data_path`, `pp_name`, or `input_df_name` points to an example/private path | Check the path and metadata filename; inspect a bounded fixture with Pandas/NumPy | Correct the path/config or regenerate into a new empty fixture root; do not overwrite unknown data |
| Toy loader asserts requested data exceeds available | `n_train_val_data` remains 1,500 while fixture is intentionally small | Count unique metadata pids and compare with config | Lower `n_train_val_data` in the copied config; do not inflate or duplicate fixture records to satisfy it |
| `ModuleNotFoundError: configs` from original toy generator | It is run outside `experiments/toy_exp`, while the script imports `configs` by top-level name | Read-only inspect invocation directory and module path | Use `generate_toy_fixture.py`; do not patch the source generator as part of onboarding |
| Existing `exp_dir` lacks `configs.py`, `model.py`, or `backbone.py` | Partial `create_exp`, wrong directory, or incompatible snapshot | List the tree and compare snapshot files to the selected source config | Stop and preserve the partial tree. Repair in a deliberate new directory or with explicit overwrite approval |
| `FileExistsError`/missing parent from `os.mkdir` | Parent path is absent or the legacy function races with another job | Ensure the parent exists and no concurrent preparation is active | Use a unique directory and one preparer; do not rely on concurrent `create_exp` |
| Test unexpectedly uses changed source code | Testing copies snapshot scripts into temporary source modules, or training used `use_stored_settings=False` | Compare snapshot hashes/version and temporary module paths | Use a controlled workspace and stored settings; never infer reproducibility from the directory name |
| Fold index error or empty test split | Fold ID is outside `range(n_cv_splits)`, fold metadata is missing/stale, or hold-out policy changed | Validate requested folds, `fold_ids.pickle`, and `hold_out_test_set` together | Stop before execution; regenerate/repair split metadata only through the data workflow |
| `--resume_to_checkpoint` ignored or wrong fold resumed | Resume path supplied without `--folds`, or path belongs to another fold | Confirm CLI arguments and expected `<exp_dir>/fold_N` checkpoint | Pair resume with exactly the intended fold and verify its `params.pth`; do not guess |
| `analysis` has no predictions/metrics | Analysis expects saved predictions and a complete stored config | Check prediction files and `cf.hold_out_test_set`/fold selection | Do not run training as a hidden repair; route prediction schema to inference/evaluation |
| `--server_env` points to inaccessible data | Config replaces paths/source root for a cluster deployment | Construct both server/local configs and compare paths without loading data | Use only with the intended deployment and `data_dest`; do not copy private server paths into public skills |
| Shell `cp` fails for spaces/quoting | Legacy `prep_exp` builds unquoted shell commands | Use simple workspace paths and inspect subprocess return/logs | Rename/use a safe workspace; do not add shell interpolation of untrusted paths |
| `exec.py --help` fails before help | Dependency/import failure in top-level evaluator/predictor/plotting imports | Run the live help command in the inspection environment and capture the import traceback | Treat as environment/version drift; do not claim CLI support from source text alone |
| CUDA/FFI/ABI error after valid config | Legacy detector/custom operation dependency, not configuration | Route to [cuda-extensions](../../cuda-extensions/SKILL.md) and inspect backend compatibility | Do not “fix” it by switching dimension/model without an explicit scope decision |

## Version and reproducibility checks

Record these before handing a configuration to another agent:

1. repository commit/tag and whether the checkout is dirty;
2. installed package/runtime version and Python/Torch compatibility facts;
3. the exact config source and snapshot files used;
4. `model`, `dim`, data roots, `input_df_name`, class map, fold policy, and
   requested folds;
5. whether `server_env`, stored settings, dev mode, and resume were used;
6. any generated fixture seed/count/shape and its metadata row count.

The README states that the project is no longer maintained. If a modern Python,
Torch, or CUDA stack changes import behavior, preserve the failure as an
explicit compatibility limit and route to the compatibility node. Do not
modernize code while answering a configuration question.

## Safe stop conditions

Stop without running a job when any of these holds:

- a data path is a placeholder or private path that has not been authorized;
- a requested fold cannot be proven to exist;
- a stored snapshot is partial or mixed-version;
- the config imports only after an unexplained `sys.path` hack;
- a model/custom-op import fails and the failure has not been classified;
- a fixture would overwrite existing files or exceed the helper's hard caps.

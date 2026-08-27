# CLI Model Operations

This reference covers DeePMD-kit command-line operations for inference, descriptors, embeddings, model deviation, model inspection, pretrained models, conversion, compression, and bias changes.

Use explicit backend selectors when needed:

```bash
dp --tf ...      # TensorFlow backend
dp --pt ...      # PyTorch backend
dp --jax ...     # JAX backend
dp --pd ...      # Paddle backend
dp --pt-expt ... # PyTorch exportable backend, when installed and appropriate
```

## `dp test`: Evaluate Against Labeled Data

Purpose: run a model over a DeePMD data system and report prediction errors.

```bash
dp test -m graph.pb -s /path/to/system -n 30
```

Common options:

| Option | Meaning |
| --- | --- |
| `-m, --model MODEL` | Frozen model file or backend-supported model artifact. |
| `-s, --system SYSTEM` | System directory; recursively detects systems. |
| `-f, --datafile FILE` | Text file listing system directories, one per line. |
| `--train-data input.json` | Use training data from a training input file. |
| `--valid-data input.json` | Use validation data from a training input file. |
| `-n, --numb-test NUM` | Number of frames; `0` means all frames. |
| `--shuffle-test` | Shuffle test frames. |
| `-d, --detail-file PREFIX` | Write detailed prediction/error files. |
| `-a, --atomic` | Test atomic labels/outputs where supported. |
| `--head, --model-branch BRANCH` | Select PyTorch multi-task branch. |

Output: logs RMSE-style metrics for energy, force, virial, and supported tensor properties. With `--detail-file`, writes per-frame/per-atom details using the given prefix.

Pitfalls:

- The system type map must match the model type map. `dp test` constructs data with the model `type_map`, so mismatched `type.raw` semantics can silently test the wrong species if data was prepared for another model.
- Use `-n 0` intentionally; it means all available frames, not zero frames.
- For non-PBC data systems, DeePMD data loading sets boxes to `None` internally when the data marks itself non-periodic.

## `dp eval-desc`: Save Descriptor Arrays

Purpose: evaluate descriptors and save NumPy arrays.

```bash
dp eval-desc -m graph.pb -s /path/to/system -o desc --dtype native
```

Options:

| Option | Meaning |
| --- | --- |
| `-m, --model MODEL` | Model to import. |
| `-s, --system SYSTEM` | System directory. |
| `-f, --datafile FILE` | File listing systems. |
| `-o, --output DIR` | Output directory; files are `DIR/<system_name>.npy`. |
| `--dtype fp32|fp64|native` | Descriptor precision; default `native`. |
| `--head, --model-branch BRANCH` | PyTorch multi-task branch. |

Output: one `.npy` file per system, each a 3D array `(nframes, natoms, ndesc)`.

Notes:

- Current PyTorch tests treat `dp eval-desc` as a compatibility path; `dp embed` is preferred when the user also needs atomic and structural features.
- Choose `native` for exact backend precision and `fp32`/`fp64` for fixed downstream dtype.

## `dp embed`: Save Descriptor, Atomic Feature, and Structural Feature

Purpose: extract embeddings into a single HDF5 file.

```bash
dp embed -m model.ckpt.pt -s /path/to/system -o embedding.hdf5 --dtype fp32
```

Options:

| Option | Meaning |
| --- | --- |
| `-m, --model MODEL` | PyTorch energy checkpoint `.pt` or frozen `.pth` for supported models. |
| `-s, --system SYSTEM` | System directory. |
| `-f, --datafile FILE` | File listing systems. |
| `-o, --output FILE` | Output HDF5 file; default `embedding.hdf5`. |
| `--dtype fp32|fp64|native` | Embedding precision; default `fp32`. |
| `--head, --model-branch BRANCH` | PyTorch multi-task branch. |

HDF5 layout:

- File attribute `type_map` records model type map.
- Each system is a group named from the system path.
- Each group has `system` and `nframes` attributes.
- Datasets include `descriptor`, `atomic_feature`, `structural_feature`, and `atom_types`.

Support constraints:

- PyTorch energy models are the primary target.
- DPA4/SeZM may require a `.pt` checkpoint rather than a frozen `.pth`.
- Spin models are not supported for embedding extraction.

## `dp model-devi`: Compare an Ensemble

Purpose: calculate model deviation from multiple models over a DeePMD data system.

```bash
dp model-devi -m graph.000.pb graph.001.pb graph.002.pb graph.003.pb -s ./data -o model_devi.out
```

Options:

| Option | Meaning |
| --- | --- |
| `-m, --models M0 M1 ...` | Frozen model files. |
| `-s, --system SYSTEM` | System directory; recursively detects systems. |
| `-o, --output FILE` | Output text table. |
| `-f, --frequency INT` | Step spacing written in the first column; default `1`. |
| `--real_error` | Calculate RMS real error against labeled data instead of pure ensemble deviation. |
| `--atomic` | Add per-atom force-deviation columns. |
| `--relative FLOAT` | Relative force deviation level parameter. |
| `--relative_v FLOAT` | Relative virial deviation level parameter. |

Output columns without `--atomic`:

```text
step max_devi_v min_devi_v avg_devi_v max_devi_f min_devi_f avg_devi_f devi_e
```

Pitfalls:

- All models must have identical `type_map`; the command raises if they differ.
- `--relative` and `--relative_v` require numeric level parameters such as `0.05`; they are not flags.
- For repeated trajectory batches in Python, prefer `calc_model_devi` with pre-loaded `DeepPot` objects to avoid repeated model loading.

## `dp show`: Inspect Model Metadata

Purpose: print type maps, descriptor/fitting parameters, branch info, size, and observed types.

```bash
dp --pt show model.pt model-branch type-map descriptor fitting-net size observed-type
```

Attributes:

| Attribute | Meaning |
| --- | --- |
| `model-branch` | Multi-task branches plus `RANDOM` branch marker. |
| `type-map` | Model element/type order. |
| `descriptor` | Descriptor configuration when stored in the artifact. |
| `fitting-net` | Fitting-network configuration when stored in the artifact. |
| `size` | Parameter counts for components and total. |
| `observed-type` | Element types observed during data statistics; may differ from full type map. |

Use this before inference when:

- The user provides species symbols but not integer atom types.
- A multi-task model needs a branch.
- A model was frozen without training config and some metadata may be unavailable.

## `dp pretrained`: Download Built-In Models

Purpose: resolve built-in model names into cached local model files.

```bash
dp pretrained download DPA-3.2-5M
```

```bash
dp pretrained download DPA-3.2-5M --cache-dir ./models
```

Rules:

- The installed package controls the valid model-name choices; use `dp pretrained download -h` to list them.
- `DeepPot("DPA-3.2-5M")` can resolve and download automatically if the model is not already cached.
- In restricted or offline environments, ask the user for a pre-downloaded path or an allowed cache directory.

## `dp compress`: Compress Frozen Models

Purpose: produce a compressed model for faster/lower-memory inference when the descriptor/model supports tabulation.

```bash
dp compress -i graph.pb -o graph-compress.pb
```

```bash
dp --pt compress -i model.pth -o model-compress.pth
```

Options:

| Option | Meaning |
| --- | --- |
| `-i, --input MODEL` | Original frozen model. |
| `-o, --output MODEL` | Compressed output model. |
| `-s, --step FLOAT` | First-table interpolation step; smaller is more accurate and larger. |
| `-e, --extrapolate INT` | Extends second-table range beyond training-data range. |
| `-f, --frequency INT` | Overflow-check frequency; default disables checks. |
| `-c, --checkpoint-folder DIR` | Compression checkpoint folder. |
| `-t, --training-script FILE` | Training script for the input frozen model when needed. |

Constraints:

- Compression support depends on descriptor type and activation functions.
- Old TensorFlow frozen models may need `dp convert-from` before compression.
- PyTorch compression requires the customized operator library to be available in the installation.
- Validate accuracy after compression with `dp test` or a small Python inference comparison.

## `dp convert-from`: Convert Old TensorFlow Frozen Models

Purpose: update older TensorFlow frozen graphs to the installed compatibility target or convert `.pbtxt`.

```bash
dp convert-from auto -i old_frozen_model.pb -o converted_model.pb
```

```bash
dp convert-from 1.2 -i old_frozen_model.pb -o converted_model.pb
```

Options:

| Option | Meaning |
| --- | --- |
| `FROM` | `auto`, `0.12`, `1.0`, `1.1`, `1.2`, `1.3`, `2.0`, or `pbtxt`. |
| `-i, --input-model FILE` | Input model. |
| `-o, --output-model FILE` | Output model; `.pbtxt` output writes text graph when applicable. |

Use when the installed DeePMD-kit rejects a frozen TensorFlow model for compatibility reasons. Compatibility is guaranteed within the same major/minor line; older supported models can often be converted, while unsupported old models may have no conversion path.

## `dp convert-backend`: Convert Between Backend Artifacts

Purpose: serialize with the input backend and deserialize with the output backend inferred from file names.

```bash
dp convert-backend model.pb model.pth
```

```bash
dp convert-backend model.pb model.dp
```

Options:

| Option | Meaning |
| --- | --- |
| `INPUT` | Source model artifact. |
| `OUTPUT` | Destination model artifact; suffix determines backend. |
| `--atomic-virial` | For `.pt2`/`.pte` outputs, include per-atom virial correction at about 2.5x inference cost; ignored with warning for other outputs. |

Pitfalls:

- Conversion support depends on installed backend serializers.
- If suffix detection is ambiguous, choose a clearer output name or backend-specific workflow.
- Test the converted model on a small known system before using it in production MD.

## `dp change-bias`: Adjust Output Bias

Purpose: update energy/output bias using target systems or user-provided per-type values.

```bash
dp --tf change-bias model.ckpt -s data_dir -o model_updated.pb
```

```bash
dp --pt change-bias model.pt -b -92.523 -187.66 -o model_updated.pt
```

```bash
dp --pt change-bias multi_model.pt -s data_dir -o model_updated.pt --model-branch branch_1
```

Options:

| Option | Meaning |
| --- | --- |
| `INPUT` | Input checkpoint or frozen model. |
| `-s, --system SYSTEM` | Target system directory. |
| `-f, --datafile FILE` | File listing target systems. |
| `-b, --bias-value VALUES...` | User-defined energy bias per type-map entry. |
| `-n, --numb-batch NUM` | Frames per system for bias changing; `0` means all. |
| `-m, --mode change|set` | `change`: fit prediction error shift; `set`: use target data statistic bias directly. |
| `-o, --output OUTPUT` | Output model/checkpoint. |
| `--model-branch BRANCH` | Multi-task model branch. |

Pitfalls:

- The number and order of `--bias-value` entries must match the model `type_map`.
- For multi-task PyTorch models, always specify `--model-branch` unless the desired branch is unambiguous.
- Bias adjustment is not a substitute for training-data or type-map repair.

## Backend and Suffix Quick Map

| Artifact | Common backend | Typical operations |
| --- | --- | --- |
| `.pb` | TensorFlow frozen graph | `test`, `eval-desc`, `model-devi`, `compress`, `convert-from`, `convert-backend`. |
| `.pth` | PyTorch frozen model | `test`, `eval-desc`, `embed` for supported energy models, `model-devi`, `compress`, `show`. |
| `.pt` | PyTorch checkpoint | `embed`, `show`, `change-bias`; freeze for standard frozen-model workflows when required. |
| `.json` + `.pdiparams` | Paddle frozen model | Paddle-supported inference/model ops. |
| Built-in name | Pretrained resolver | `DeepPot(NAME)` or `dp pretrained download NAME`. |

## Minimal Operation Order for Unknown Model Artifacts

1. Run `dp --version` and choose a backend flag if the environment has multiple backends.
2. Inspect with `dp show MODEL type-map descriptor fitting-net size` if the artifact supports it.
3. If the model is old TensorFlow and rejected, run `dp convert-from auto` and retry.
4. Run a small `dp test` or Python `DeepPot.eval` batch before long trajectories.
5. Only then run expensive `dp embed`, `dp model-devi`, compression, or backend conversion.

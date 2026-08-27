# Troubleshooting Inference and Model Operations

Use this matrix when DeePMD-kit model loading, Python inference, CLI testing, descriptor extraction, model deviation, or model artifact operations fail.

## Wrong Backend or Model Suffix

Symptoms:

- Model loading fails immediately with backend detection or deserialization errors.
- A `.pt`, `.pth`, `.pb`, `.dp`, `.json`, or `.pdiparams` artifact is treated as the wrong backend.
- `dp show` or `DeepPot` works for one model but not another nominally similar file.

Actions:

1. Identify the artifact type:
   - `.pb`: TensorFlow frozen graph.
   - `.pth`: PyTorch frozen model.
   - `.pt`: PyTorch checkpoint; not always equivalent to a frozen model.
   - `.json` plus `.pdiparams`: Paddle frozen model.
   - built-in names such as `DPA-3.2-5M`: pretrained selector, not a local suffix.
2. Retry CLI operations with an explicit backend flag, for example `dp --tf test ...` or `dp --pt test ...`.
3. Use `dp show MODEL type-map descriptor fitting-net size` to check whether the selected backend can load the artifact.
4. If converting, make the output suffix unambiguous before `dp convert-backend INPUT OUTPUT`.

Avoid:

- Renaming a file suffix to force a backend. Use the appropriate conversion or freeze workflow.
- Passing a training checkpoint to a command that expects a frozen model unless the command explicitly supports checkpoints.

## Repeated Model Loading Memory Growth

Symptoms:

- Memory usage grows across trajectory frames, active-learning batches, or repeated model-deviation calls.
- CPU/GPU memory is not released even after Python objects go out of scope.
- Long loops eventually fail with out-of-memory errors.

Cause:

TensorFlow and PyTorch runtimes may retain model graphs, compiled functions, kernels, or allocator pools. DeePMD-kit documentation warns against repeatedly loading the same model in cyclic inference or model-deviation workflows.

Actions:

1. Load each model once outside the loop.
2. Reuse `DeepPot` objects for all frames/batches.
3. For model deviation, pass already-loaded objects to `calc_model_devi`.
4. If a CLI command must be used, batch systems through `-f datafile` where possible instead of launching many short processes.

Good pattern:

```python
models = [DeepPot(path, auto_batch_size=True) for path in model_paths]
for coord, cell, atype in batches:
    deviation = calc_model_devi(coord, cell, atype, models)
```

Bad pattern:

```python
for batch in batches:
    models = [DeepPot(path) for path in model_paths]
```

## Atom Type Order Mismatch

Symptoms:

- Energies/forces are nonsensical, but shapes are valid and no exception is raised.
- A model trained with `type_map=["O", "H"]` is used with `atype=[1, 0, 0]` that the user intended as alphabetical order.
- Multiple models in `dp model-devi` fail with a type-map mismatch.

Actions:

1. Inspect model type order with `pot.get_type_map()` or `dp show MODEL type-map`.
2. Build atom-type indices from that model order:

   ```python
   type_to_index = {symbol: i for i, symbol in enumerate(pot.get_type_map())}
   atype = [type_to_index[symbol] for symbol in symbols]
   ```

3. For ensemble deviation, verify all models have identical `type_map` before comparing.
4. For DeePMD data systems, confirm `type.raw` indices were produced for the same type map.

Avoid:

- Assuming alphabetical, periodic-table, or data-file order equals model order.
- Repairing prediction errors by changing coordinates before checking type order.

## Bad Coordinate, Cell, or Atype Shapes

Symptoms:

- Reshape errors mentioning `nframes`, `natoms`, or size mismatch.
- Errors about wrong `fparam` or `aparam` size.
- Forces have unexpected atom count or frames collapse into one frame.

Expected shapes:

| Input | Shape |
| --- | --- |
| `coords` | `(nframes, natoms, 3)` or flattened `(nframes, natoms * 3)`. |
| `cells` | `(nframes, 3, 3)`, flattened `(nframes, 9)`, or `None`. |
| `atom_types` | `(natoms,)` normally; `(nframes, natoms)` with `mixed_type=True`. |
| `fparam` | `(nframes, dim_fparam)` or `(dim_fparam,)`. |
| `aparam` | `(nframes, natoms, dim_aparam)`, `(natoms, dim_aparam)`, or `(dim_aparam,)`. |

Actions:

1. Determine `nframes` and `natoms` before constructing arrays.
2. Use the bundled helper to generate a skeleton:

   ```bash
   python sub-skills/inference-model-ops/scripts/deeppot_input_shapes.py --natoms 64 --nframes 10
   ```

3. For mixed-type data, pass `mixed_type=True` and shape `atom_types` as `(nframes, natoms)`.
4. Check optional parameter dimensions with `get_dim_fparam()` and `get_dim_aparam()`.

## Non-Periodic Cell Handling

Symptoms:

- Isolated molecule inference fails due to invalid cell or unexpected periodic interactions.
- User passes a zero cell matrix and gets bad predictions or neighbor-list problems.

Actions:

- In Python, pass `cell=None` for non-PBC:

  ```python
  energy, force, virial = pot.eval(coord, None, atype)
  ```

- In DeePMD data-system CLI workflows, rely on the data loader's PBC metadata; do not manually fake boxes unless the data format requires it.
- If a cell is present, ensure each frame has 9 values and physically sensible dimensions for the model cutoff.

Avoid:

- Using zero, identity, or tiny cells as a non-PBC sentinel without confirming the model/data workflow expects that.

## Descriptor, Embedding, and Dtype Confusion

Symptoms:

- User expects `dp eval-desc` to produce HDF5 embeddings.
- Descriptor arrays have a different dtype than expected.
- `eval_embedding` raises `NotImplementedError` or fails for a non-PyTorch or spin model.

Distinctions:

| Operation | Output | Default dtype | Main support |
| --- | --- | --- | --- |
| `eval_descriptor` / `dp eval-desc` | Descriptor only, `(nframes, natoms, ndesc)` | `native` | Cross-backend descriptor path. |
| `eval_embedding` / `dp embed` | Descriptor, atomic feature, structural feature | `fp32` | PyTorch energy models that support embedding. |

Actions:

1. Use `dp eval-desc` when only local descriptors are needed as `.npy` files.
2. Use `dp embed` when downstream analysis needs all three embedding outputs in HDF5.
3. Pass `--dtype fp32`, `--dtype fp64`, or `--dtype native` explicitly when reproducibility matters.
4. For multi-task models, include `--head` / `--model-branch`.

## Unsupported Old Frozen Model

Symptoms:

- TensorFlow `.pb` model fails with compatibility/version errors.
- Compression rejects a model trained by an older DeePMD-kit version.
- Model metadata is missing or cannot be parsed.

Actions:

1. Try automatic conversion:

   ```bash
   dp convert-from auto -i old_frozen_model.pb -o converted_model.pb
   ```

2. If known, specify the source version:

   ```bash
   dp convert-from 1.2 -i old_frozen_model.pb -o converted_model.pb
   ```

3. Retry `dp test`, `dp show`, or `dp compress` with the converted model.
4. If conversion is unavailable for the original version, ask the user for a newer frozen model, checkpoint, or the original training environment.

Notes:

- DeePMD-kit generally guarantees compatibility within the same major/minor release line.
- Some old models can be converted; some are not supported by the installed version.

## Pretrained Network or Cache Constraints

Symptoms:

- `DeepPot("DPA-3.2-5M")` or `dp pretrained download` fails due to offline execution.
- Cache path is unwritable.
- Requested pretrained model name is rejected by argument parsing.

Actions:

1. List valid names for the installed package:

   ```bash
   dp pretrained download -h
   ```

2. Use a writable cache directory:

   ```bash
   dp pretrained download DPA-3.2-5M --cache-dir ./models
   ```

3. If network access is unavailable, ask the user for a pre-downloaded model path.
4. Treat pretrained names as installed-version-specific selectors; do not assume every release has the same list.

Avoid:

- Hard-coding private cache paths in reusable scripts or skill content.
- Automatically downloading large pretrained assets when the user has not allowed network/cache changes.

## Compression Accuracy or Operator Problems

Symptoms:

- `dp compress` fails for a descriptor/model type.
- PyTorch compression complains about missing custom operators.
- Compressed model is faster but accuracy changes unexpectedly.

Actions:

1. Confirm the descriptor supports compression.
2. For PyTorch, confirm the installation includes the customized operator library needed for compression.
3. Use a conservative `--step` value and record the command.
4. Compare original and compressed models on a small validation system with `dp test` or Python `DeepPot.eval`.
5. If overflow is suspected during MD/inference, set `--frequency` to enable periodic overflow checks.

## Bias-Change Problems

Symptoms:

- `dp change-bias` updates the wrong branch or rejects a multi-task model.
- Manual `--bias-value` gives wrong energies after the update.
- Output path is not inferred as expected.

Actions:

1. Inspect type map before manual bias values:

   ```bash
   dp show model.pt type-map
   ```

2. Provide one bias value per type-map entry, in order.
3. For multi-task PyTorch models, pass `--model-branch`.
4. Use `-m change` to fit a shift from prediction errors on target systems; use `-m set` only when target data statistics should directly define the bias.
5. Validate the adjusted model with `dp test` on a small target system.

## Convert-Backend Problems

Symptoms:

- `dp convert-backend` cannot infer input/output backend.
- Converted model loads but gives different outputs.
- Per-atom virial is missing in downstream LAMMPS workflows.

Actions:

1. Use unambiguous suffixes for `INPUT` and `OUTPUT`.
2. Confirm both backends are installed and support serialization hooks.
3. Use `--atomic-virial` only for `.pt2`/`.pte` outputs that need per-atom virial correction; expect extra inference cost.
4. Run a small equivalence check after conversion.

## Quick Diagnostic Questions

Ask the user:

- What is the exact model artifact path or pretrained model name?
- Which backend produced it and which backend should load it?
- What is the model `type_map`, and what element order are the coordinates using?
- Is the system periodic? If not, are they passing `cell=None`?
- Are they running this in a loop that reloads models?
- Do they need descriptor-only output, HDF5 embeddings, or energy/force/virial predictions?

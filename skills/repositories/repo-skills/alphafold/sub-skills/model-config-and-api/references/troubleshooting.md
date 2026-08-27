# Model Config and API Troubleshooting

Use this reference when AlphaFold model-layer inspection, config edits, parameter loading, or backend imports fail before prediction. Keep routine checks lightweight and avoid loading weights unless the user explicitly needs parameter validation.

## Triage Checklist

1. Identify the active task: preset selection, config edit, feature processing, parameter loading, or model execution.
2. Print presets with `scripts/inspect_model_presets.py --json`; do not load weights just to discover model names.
3. Verify selected model names are from `MODEL_PRESETS` unless the task explicitly targets historical configs.
4. If imports fail, repair package pins before debugging model code.
5. If parameter loading fails, check `<data_dir>/params/params_<model_name>.npz` naming before changing code.
6. If GPU or memory errors appear, reduce config/runtime pressure only after confirming the user intended to run inference.

## JAX and JAXLIB Mismatch

Symptom examples:

- Importing `jax` or AlphaFold model modules fails with a message that `jaxlib` is newer than `jax` or otherwise incompatible.
- JAX imports but fails before any AlphaFold-specific code executes.

Likely cause:

- `jax` and `jaxlib` versions are installed from incompatible releases. In the verified inspection context for this skill, `jax==0.4.26` required an aligned `jaxlib==0.4.26` while preserving `numpy==1.24.3` and `ml-dtypes==0.3.2`.

Safe repair plan:

1. Inspect versions with a small Python command, not full AlphaFold inference:
   ```bash
   python - <<'PY'
   import jax, jaxlib, numpy, ml_dtypes
   print('jax', jax.__version__)
   print('jaxlib', jaxlib.__version__)
   print('numpy', numpy.__version__)
   print('ml_dtypes', ml_dtypes.__version__)
   PY
   ```
2. Align `jaxlib` to the installed `jax` release, or align both to the version set required by the project environment. For AlphaFold package version 2.3.2 evidence, the compatible pair is `jax==0.4.26` and `jaxlib==0.4.26`.
3. Avoid upgrading NumPy or TensorFlow opportunistically; AlphaFold's pinned stack uses `numpy==1.24.3` and `tensorflow-cpu==2.16.1`.
4. Re-test a lightweight import such as `python -c "from alphafold.model import config; print(config.MODEL_PRESETS)"`.

Do not silently mutate a user-owned environment if the repair could break their other projects.

## Missing Haiku, ML Collections, or Other Model Dependencies

Symptom examples:

- `ModuleNotFoundError: No module named 'haiku'`
- `ModuleNotFoundError: No module named 'ml_collections'`
- Import succeeds for `alphafold` but fails for `alphafold.model.config` or `alphafold.model.model`.

Expected package names:

- Haiku is installed as `dm-haiku`, imported as `haiku`.
- ML Collections is installed as `ml-collections`, imported as `ml_collections`.
- TensorFlow model feature processing imports `tensorflow.compat.v1` from `tensorflow-cpu` in the pinned package set.

Repair approach:

- Install the missing pinned dependency set for the AlphaFold package rather than latest unpinned versions.
- Re-run only config import and the bundled preset inspector before attempting `RunModel` construction.

## TensorFlow, NumPy, and ML-DTypes Conflicts

Symptom examples:

- Importing TensorFlow fails after a JAX/NumPy upgrade.
- `features.np_example_to_features` fails at TensorFlow graph/session setup.
- Error messages mention missing dtypes, incompatible NumPy ABI, or `ml_dtypes` symbols.

Relevant facts:

- AlphaFold 2.3.2 package metadata pins `numpy==1.24.3` and `tensorflow-cpu==2.16.1`.
- A working inspection stack used `ml-dtypes==0.3.2` with `jax==0.4.26` and `jaxlib==0.4.26`.
- Monomer feature processing uses TensorFlow v1 graph/session APIs on CPU; multimer `RunModel.process_features` bypasses this function.

Repair approach:

1. Confirm whether the task truly needs monomer feature preprocessing. Config and preset inspection should not import TensorFlow-heavy paths beyond what `config` requires.
2. If TensorFlow is required, restore the pinned AlphaFold dependency set instead of upgrading NumPy.
3. Re-test with a minimal import and only then run feature processing on a tiny synthetic feature dict if the user requested it.

## Model Parameter Path or Version Mismatch

Symptom examples:

- `FileNotFoundError` for `params_model_*.npz`.
- Parameter load succeeds but later `RunModel.predict` fails with missing keys or shape mismatch.
- Multimer v3 config is paired with old multimer v2 filenames.

Checks:

- `get_model_haiku_params(model_name, data_dir)` expects `data_dir` to contain a `params/` child directory.
- For `model_name='model_1_ptm'`, the expected file is `params/params_model_1_ptm.npz`.
- For `model_name='model_1_multimer_v3'`, the expected file is `params/params_model_1_multimer_v3.npz`.

Repair approach:

1. Print selected model names from `MODEL_PRESETS`.
2. Check only filenames first; do not load every `.npz` file unless necessary.
3. Download or point to the parameter bundle matching the AlphaFold package/model family.
4. Keep config name and parameter suffix identical.

## CASP14, PTM, Multimer, v2, and v3 Preset Confusion

Common mistakes:

| Mistake | Correction |
| --- | --- |
| Using `monomer` when the task requires PAE or pTM confidence. | Use `monomer_ptm`, e.g. `model_1_ptm` through `model_5_ptm`. |
| Treating `monomer_casp14` as a separate parameter family. | It is an alias of the monomer model tuple in this package. |
| Pairing `MODEL_PRESETS['multimer']` with `params_model_1_multimer.npz`. | Use v3 parameter filenames because the active multimer preset names end in `_multimer_v3`. |
| Editing `multimer_mode` manually on a monomer config. | Start from a multimer model name so module construction, heads, and feature assumptions are consistent. |
| Using old v2/v1 multimer config names because `CONFIG_DIFFS` contains them. | Treat them as historical/internal config support unless the user explicitly targets those weights. |

Difficult case: for a monomer pTM confidence run, select `monomer_ptm` and model names such as `model_1_ptm`, because those configs enable the predicted aligned error head weight. Do not use AlphaFold-Multimer v3 weights for this task: multimer v3 configs expect multimer feature semantics and v3-specific parameter files, and their ranking includes ipTM when multimer outputs exist.

## GPU Memory and Unified Memory Flags

Symptom examples:

- XLA out-of-memory during model initialization or prediction.
- GPU memory is exhausted before prediction starts.
- The user mentions unified memory flags, `TF_FORCE_UNIFIED_MEMORY`, `XLA_PYTHON_CLIENT_MEM_FRACTION`, or JAX preallocation.

Guidance:

- These are runtime execution concerns, not config-inspection requirements. Do not set global environment variables in generated skill content or on behalf of the user without explicit confirmation.
- First reduce task scope: avoid full inference, avoid benchmarking, and validate inputs/configs only.
- If the user intends inference, consider smaller targets, fewer seeds, reduced recycling, reduced MSA settings, or CPU-only inspection as safer diagnostics before changing global backend flags.
- Multimer v3 defaults can be heavier than monomer configs because of complex-focused settings such as high recycling and MSA budgets.

## `RunModel` Constructed Without Parameters

Symptom examples:

- Logs warn that parameters were initialized randomly.
- Predictions complete but are scientifically meaningless.

Cause:

- `RunModel.init_params` initializes random parameters when `params` is empty.

Repair approach:

- For real predictions, always pass parameters loaded by `get_model_haiku_params` for the same model name as the config.
- Use random initialization only for controlled shape/debug tests, and label results as non-scientific.

## Feature Processing Shape or Key Errors

Symptom examples:

- `KeyError: 'seq_length'` in `np_example_to_features`.
- Missing template/MSA feature keys after editing `cfg.data.common.use_templates`.
- Object-dtype arrays disappear from processed features.

Likely causes:

- Raw features came from the wrong data pipeline or were manually assembled incompletely.
- Template feature expectations changed after config edits.
- Multimer raw features were routed through monomer TensorFlow preprocessing.

Repair approach:

1. Route input parsing/data-pipeline preparation to `../input-data-and-formats/`.
2. Start from a preset config matching the data pipeline: monomer raw features for monomer configs, multimer raw features for multimer configs.
3. Avoid toggling template settings after feature generation unless you also regenerate compatible features.
4. Remember that `np_example_to_features` intentionally returns only non-object dtype outputs.

## Lightweight Validation Commands

Safe preset/config inspection:

```bash
python sub-skills/model-config-and-api/scripts/inspect_model_presets.py --json
```

Safe import smoke test:

```bash
python - <<'PY'
from alphafold.model import config
print(config.MODEL_PRESETS)
print(config.model_config('model_1_ptm').model.heads.predicted_aligned_error.weight)
PY
```

Avoid these as routine validation:

- Loading every parameter file.
- Constructing all `RunModel` instances.
- Calling `RunModel.predict`.
- Running feature preprocessing on real targets.
- Setting backend memory environment variables globally.

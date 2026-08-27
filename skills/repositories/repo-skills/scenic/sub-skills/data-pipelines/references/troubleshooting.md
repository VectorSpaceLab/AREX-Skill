# Scenic data-pipeline troubleshooting

Use this reference to diagnose dataset failures while avoiding accidental downloads or destructive conversions.

## Unknown dataset name

Typical error:

```text
KeyError: Unknown dataset (<name>). Did you import the dataset module explicitly?
```

Resolution flow:

1. Run a safe registry listing:

   ```bash
   python skills/disco/scenic/sub-skills/data-pipelines/scripts/check_dataset_registry.py --list
   ```

2. If `<name>` is in the lazy table, try a safe lookup:

   ```bash
   python skills/disco/scenic/sub-skills/data-pipelines/scripts/check_dataset_registry.py --dataset-name <name>
   ```

   - Success means the registry is fine; the later failure is likely data/dependency/config-related.
   - Import failure means an optional dependency or module import side effect failed. Fix that import first.

3. If `<name>` is not in the lazy table, decide between:

   - **Project/custom dataset:** import the module that contains `@datasets.add_dataset('<name>')`, then look up again.

     ```bash
     python skills/disco/scenic/sub-skills/data-pipelines/scripts/check_dataset_registry.py \
       --import-module package.or.project.dataset_module \
       --dataset-name <name>
     ```

   - **Typo/wrong config:** correct `config.dataset_name` to a built-in name or to the exact project-registered name.

4. If the error says an imported module did not register the dataset, the module was found but did not call `@datasets.add_dataset` with the requested string. Check for a name mismatch or a conditional import failure.

Synthetic case coverage: for an unknown name, do not assume Scenic lacks the dataset. First classify it as built-in lazy, project/custom registration, or typo.

## Missing TFDS data or accidental downloads

Symptoms:

- TFDS asks to download/prepare data.
- Permission/license errors for ImageNet, Cityscapes, COCO, or other gated datasets.
- Data directory exists but split metadata is missing.

Facts to remember:

- `load_split_from_tfds` and `get_num_examples` call `download_and_prepare()` and are not safe no-data probes.
- BigTransfer and FlexIO eventually use TFDS builders and need prepared/downloadable data for real iterators.
- Some TFDS names can read from GCS if configured by the helper, but this is still external data access.

Safer preflight:

```bash
python - <<'PY'
import tensorflow_datasets as tfds
name = 'cifar10'       # replace with the configured TFDS name
builder = tfds.builder(name, data_dir=None)
print('builder:', builder.name)
print('data_dir:', builder.data_dir)
print('known splits from builder metadata:', list(builder.info.splits.keys()))
print('No download was requested by this snippet.')
PY
```

Only run a real build after the user confirms the data directory/download policy and runtime budget.

## Optional dependency failures

Common optional imports and what they imply:

| Dependency/module | Usually needed for | Recovery |
| --- | --- | --- |
| `tensorflow_datasets` | TFDS-backed datasets, BigTransfer, FlexIO. | Install a compatible TFDS version or narrow to registry-only checks. |
| `tensorflow` | All `tf.data` pipelines and preprocessing. | Use the prepared Scenic environment; for registry-only checks, hide GPUs if TensorFlow allocation is the problem. |
| `tensorflow_addons` | BigTransfer rotate/randaugment image ops. | Install a version compatible with the TensorFlow version, avoid rotate/randaugment ops, or change preprocessing. |
| `clu` | FlexIO deterministic/preprocess APIs. | Install CLU or avoid FlexIO. |
| `grain.tensorflow` | FlexIO Grain-backed sources. | Install Grain support or use TFDS sources. |
| Custom `pp_libs` modules | FlexIO/project preprocessing specs. | Ensure the package/module named in `dataset_configs.pp_libs` is importable before building. |
| `pycocotools` | Many COCO annotation/eval/conversion flows. | Install it only when the requested COCO operation actually needs annotations/eval. |

Use `--verbose-traceback` with the registry helper when the top-level error hides the actual missing optional dependency.

## TensorFlow GPU memory or device conflicts

Registry lookup should not require GPU memory, but importing TensorFlow can still initialize CUDA libraries. If import checks fail with GPU allocation or CUDA initialization messages, retry a CPU-only diagnostic:

```bash
CUDA_VISIBLE_DEVICES="" TF_CPP_MIN_LOG_LEVEL=2 \
python skills/disco/scenic/sub-skills/data-pipelines/scripts/check_dataset_registry.py --dataset-name cifar10
```

For full training runs, coordinate TensorFlow/JAX memory policy in `running-and-training`. Common environment variables include `TF_FORCE_GPU_ALLOW_GROWTH=true` for TensorFlow and `XLA_PYTHON_CLIENT_PREALLOCATE=false` for JAX, but set them deliberately for the launch environment rather than hiding problems in data-pipeline code.

## BigTransfer preprocessing failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `KeyError` for `preprocess_ops.<name>` | Unknown/misspelled preprocessing op. | Compare the op name to the known BigTransfer op list; fix the `pp_train`/`pp_eval` string. |
| `Syntax error on: <token>` | Invalid `op(args)` syntax in preprocessing string. | Check quotes, commas, parentheses, and literal values. |
| TensorFlow Addons import/error around rotate/randaugment | `random_rotate`, `rotate`, or `randaug` uses TensorFlow Addons image helpers. | Install a compatible `tensorflow_addons` or remove those ops. |
| Field missing after preprocessing | `keep`, `drop`, `delete_field`, or TPU dtype filtering removed it. | Preserve the field in the preprocessing string or disable `remove_tpu_dtypes` only if the downstream supports that dtype. |
| Unexpected one-hot or mixup behavior | `target_is_onehot` depends on preprocessing/config, and mixup requires one-hot targets. | Confirm `onehot`/`onehot_labels` and mixup settings together. |

No-data validation: parse/review the preprocessing string and import the `bit` builder; do not call the builder unless TFDS data is available.

## FlexIO failures

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `This dataset requires a JAX RNG` | `rng=None` passed to FlexIO. | Pass a JAX PRNG key through `train_utils.get_dataset` or builder call. |
| `do not use shuffle_seed` | FlexIO rejects truthy `shuffle_seed`. | Set `config.shuffle_seed = None` or `0` according to the call path and rely on RNG. |
| `FlexIO pipeline does not support data service` | `dataset_service_address` was supplied. | Remove data-service use or choose a different input pipeline. |
| `Unsupported dtype_str` | FlexIO only supports `float32`. | Set `config.data_dtype_str = 'float32'` or use another dataset builder. |
| Grain requires `start_step` | Grain source needs deterministic resume index. | Supply `start_step` when constructing the dataset. |
| Mixed Grain sources not implemented | Multiple Grain sources with merged sampling. | Use one Grain source, avoid merge, or implement a project-specific Grain mixture. |
| Unknown preprocessing op | `pp_libs` does not include the module defining the CLU preprocess op. | Add/import the needed preprocessing library module and retry. |
| Incompatible input specs across unmerged sources | FlexIO currently expects matching specs. | Harmonize preprocessing/batching or merge sources with compatible outputs. |

## `tf.data` service issues

Symptoms and fixes:

- `ValueError` about random seed with data service: set `config.shuffle_seed = None` for data-service runs.
- Service address unreachable: verify the dispatcher address and network route outside Scenic first.
- Identical data on workers: ensure data service is used only with seed policy that Scenic accepts.
- Eval pipeline unexpectedly not distributed: many helpers intentionally apply data service only to training data.
- FlexIO rejects data service: this is by design; remove the service address for FlexIO.

Route cluster launch, service startup, and distributed command details to `running-and-training`.

## COCO/TFRecord request with no data present

When the user asks to convert COCO, create TFRecords, or inspect TFRecords but no data exists, do not fabricate a run. Provide this preflight instead:

1. Ask for or identify input roots: images/videos, annotation JSONs, existing TFRecords, tokenizer/assets, and label maps.
2. Ask for operation type: inspect schema, convert to TFRecord, use existing TFDS/Scenic pipeline, or evaluate predictions.
3. Check optional dependencies only for the selected operation (`pycocotools`, TensorFlow, TFDS, project-specific preprocess modules).
4. Require an explicit output directory for generated records and state whether overwriting is allowed.
5. If data remains unavailable, stop after the checklist and route project-specific conversion-tool details to `baselines-and-projects`.

Synthetic case coverage: a no-data conversion request should produce a layout/dependency/output preflight and avoid destructive conversion.

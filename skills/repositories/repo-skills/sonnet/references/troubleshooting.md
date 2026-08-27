# Sonnet Cross-Cutting Troubleshooting

Use this root troubleshooting file before entering a sub-skill when the failure
is about installation, imports, TensorFlow runtime selection, public API routing,
or the broad Sonnet mental model.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'sonnet'` | `dm-sonnet` is not installed in the Python environment running the code. | Install with `python -m pip install dm-sonnet tensorflow`; rerun the import check from the same Python. |
| `ModuleNotFoundError: No module named 'tensorflow'` | Sonnet imports TensorFlow and does not vendor it. | Install a TensorFlow build compatible with the Python version and platform. |
| `ModuleNotFoundError: No module named 'tree'` | Sonnet's `dm-tree` dependency is missing or the environment is partially installed. | Install/repair base dependencies: `python -m pip install dm-tree absl-py numpy wrapt tabulate`; run `python -m pip check`. |
| TensorFlow logs `Could not find cuda drivers` or `GPU will not be used` | The installed TensorFlow runtime is using CPU or cannot load CUDA libraries. | Fine for CPU Sonnet workflows. For accelerator tasks, verify `tf.config.list_physical_devices('GPU')` before claiming GPU support. |
| TPU errors from `TpuReplicator` | TPU runtime is absent or not initialized. | Do not claim TPU support from CPU. Use the distribution sub-skill on a TPU-enabled runtime. |

## Public API routing failures

| Symptom | Open next |
| --- | --- |
| Empty `module.trainable_variables` | [module-authoring](../sub-skills/module-authoring/SKILL.md) or [training-and-optimization](../sub-skills/training-and-optimization/SKILL.md). |
| Shape error during first call | [layers-and-nets](../sub-skills/layers-and-nets/SKILL.md) for built-ins; [module-authoring](../sub-skills/module-authoring/SKILL.md) for custom modules. |
| `optimizer.apply` raises about empty parameters, all `None` gradients, length mismatch, or dtype mismatch | [training-and-optimization](../sub-skills/training-and-optimization/SKILL.md). |
| RNN output/state shape confusion | [sequence-and-rnn](../sub-skills/sequence-and-rnn/SKILL.md). |
| `TensorVariable` cannot be read or has no value | [functional-transforms](../sub-skills/functional-transforms/SKILL.md). |
| SavedModel load result is not a Sonnet module | [serialization-and-distribution](../sub-skills/serialization-and-distribution/SKILL.md). |
| `CrossReplicaBatchNorm` says it cannot be called in cross-replica context | [serialization-and-distribution](../sub-skills/serialization-and-distribution/SKILL.md). |

## Minimal environment smoke

```bash
python scripts/check_sonnet_install.py --help
python scripts/check_sonnet_install.py
```

The helper imports TensorFlow/Sonnet, prints versions and TensorFlow devices,
builds an MLP, applies a tiny Sonnet optimizer step, and runs a short LSTM
unroll. It does not download data or require a GPU.

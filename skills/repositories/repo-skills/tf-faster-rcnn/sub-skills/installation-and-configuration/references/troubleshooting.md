# Troubleshooting

## Purpose

Use this when tf-faster-rcnn fails during dependency setup, native extension build, TensorFlow import, or config override parsing.

If the symptom is really about dataset placement, checkpoint layout, demo execution, or training/evaluation commands, route to the sibling sub-skill instead of trying to fix it here.

## Fast triage

1. Run `python scripts/check_environment.py --repo-root <tf-faster-rcnn-root>`.
2. If it reports missing `nvcc` or `CUDAHOME`, fix the CUDA toolchain first.
3. If it reports TensorFlow or protobuf mismatch, fix the Python package pins next.
4. If it reports missing `model.nms_wrapper`, the compiled NMS extensions are still not ready.
5. If the issue is a `cfg_from_list` or YAML override, fix the literal type or key name.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `OSError: The nvcc binary could not be located in your $PATH. Either add it to your path, or set $CUDAHOME` | `lib/setup.py` imports CUDA detection immediately and cannot see a toolkit. | Install CUDA, export `CUDAHOME=/usr/local/cuda` or your real toolkit root, add `$CUDAHOME/bin` to `PATH`, verify `nvcc --version`, then rerun `cd lib && make`. |
| `CUDA_HOME` is set but the build still fails | The build script looks for `CUDAHOME`, not just `CUDA_HOME`. | Export `CUDAHOME` as well, or put `nvcc` directly on `PATH`. |
| `ModuleNotFoundError: No module named 'tensorflow.contrib'` | A TensorFlow 2.x wheel is installed. This repo is TensorFlow 1.x / `slim` era code. | Pin TensorFlow 1.x. The verified inspection path used `tensorflow==1.15.5`. |
| Protobuf descriptor / import errors during TensorFlow import | A too-new protobuf wheel is installed. | Pin `protobuf==3.20.3` or another TensorFlow 1.x-compatible 3.x release. |
| `ModuleNotFoundError: No module named 'nms.gpu_nms'` | The native extension build never completed, or CUDA compilation was skipped. | Fix the CUDA toolchain and rerun the `lib/` build. If you only need source inspection, stay with `py_cpu_nms` and `generate_anchors`, but do not claim full runtime readiness. |
| `ImportError` when importing `model.nms_wrapper` | `model.nms_wrapper` imports both `nms.cpu_nms` and `nms.gpu_nms` eagerly. | Build the compiled NMS extensions. Setting `cfg.USE_GPU_NMS=False` alone does not remove the import requirement. |
| `KeyError: X is not a valid config key` | A typo or unsupported dotted key was passed to `cfg_from_list` or the YAML preset. | Use the exact key names from `lib/model/config.py`. |
| `AssertionError: type <class 'int'> does not match original type <class 'list'>` | A config override used the wrong Python literal type. | Match the existing field type exactly. Use `[800]` for list-valued scales, `False` for bools, and quoted strings for string overrides. |
| `AssertionError` from `cfg_from_list` with no message | The override list had an odd number of entries, or a nested key was invalid. | Pass key/value pairs only and double-check each dotted path. |
| `YAMLLoadWarning: calling yaml.load() without Loader=... is deprecated` | Modern PyYAML is warning about the legacy loader used by `cfg_from_file`. | Cosmetic for the current skill draft. If you refresh the repo skill later, switch to `safe_load`. |
| `pip install -e <repo-root>` fails because no `setup.py` or `pyproject.toml` exists at the repository root | The root checkout is not an installable Python project. | Install the Python dependencies separately and build from `lib/` instead. |
| `nvcc` compile errors mentioning an unsupported GPU architecture | The hardcoded `-arch=sm_*` flag in `lib/setup.py` does not match your GPU. | Edit the `-arch` flag to match your hardware, then rebuild. |

## Recovery commands

Common commands that are safe to retry after fixing the root cause:

```bash
python scripts/check_environment.py --repo-root <tf-faster-rcnn-root>
cd <tf-faster-rcnn-root>/lib && make
```

For a CPU-only source inspection path, you can also re-run only the pure utility checks from the inspector and stop before the compiled NMS wrapper.

## When to stop

Stop and hand the case to a data, demo, or training sub-skill when the missing piece is one of these:

- dataset directory layout or symlink placement
- pretrained checkpoint download or placement
- demo invocation or image visualization
- training, testing, or re-evaluation command construction

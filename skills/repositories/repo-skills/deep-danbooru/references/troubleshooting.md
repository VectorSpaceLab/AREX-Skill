# Cross-cutting troubleshooting

Read this before changing dependencies or interpreting a failure that crosses
multiple DeepDanbooru workflows.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: tensorflow` or `tensorflow_io` | The base package was installed without the TensorFlow workflow dependencies, or the wheels are incompatible with the Python version. | Use a fresh compatible environment, install the documented TensorFlow requirements, then run `python scripts/environment_smoke.py`. Do not patch around the import by hiding the package. |
| CLI fails before showing help | `deepdanbooru.__main__` imports TensorFlow Lite and the package imports TensorFlow-facing modules eagerly. | Run the smoke helper and inspect the first missing module/version. Fix the environment before diagnosing a model. |
| Native `test_package_setup` or `test_readme_pkg` fails | The exact source snapshot has older dependency floors in `setup.py` than in `requirements.txt`/README. | Treat this as package-metadata drift; use the current requirements for a new environment and report the source inconsistency rather than weakening the runtime dependency set. |
| No GPU appears | CUDA libraries/driver are unavailable to the chosen TensorFlow build. | Continue with the verified CPU path for correctness, or separately provision and verify a compatible GPU environment. Do not claim GPU readiness from `--allow-gpu`. |
| Model file is not found | `project.json`'s `model` value does not match `model-<model>.keras` or `.h5`, or the path is wrong. | Run the owning preflight, inspect the exact model value and filenames, and route missing artifacts to training. |
| Tags print with wrong names or no tags print | `tags.txt` order/count differs from the model output, or threshold is too high. | Validate the exact tag file used for training, compare output width with nonblank tag count, then rerun one image at a diagnostic threshold. |
| Folder input is rejected | `evaluate` received a directory without `--allow-folder`, or a custom filter does not match the extension. | Start with one file; add `--allow-folder` and comma-separated glob patterns only after the file path works. |
| `evaluate-project` raises `AttributeError` for a tag loader | Known 1.0.0 source defect: `load_project()` calls `dd.data.load_tags_from_project`, but the function is exposed under `dd.project`. | Use `evaluate --project-path PROJECT --allow-folder` for production evaluation, or apply a local compatibility fix only in a controlled development checkout. |
| Training appears to progress with too few samples | The TensorFlow dataset uses `ignore_errors()` and drops missing/undecodable images. | Run the training preflight with image checks, inspect SQLite-derived paths and file signatures, and do not treat a partial run as valid. |
| TFLite output is empty or conversion fails | Missing optimization flag, incompatible layer/operator, invalid model, or bad save path. | Run post-training preflight, require a non-empty artifact, retry default optimization before experimental sparsity, and validate with a CPU interpreter. |
| Grad-CAM writes only `input.png` | No prediction met the inclusive threshold, so no tag map was selected. | Confirm ordinary inference first and lower the threshold for diagnosis; distinguish this from missing SciPy/Pillow or gradient errors. |

## Safety boundaries

Network downloads, API credentials, full training, large model evaluation, and
image-writing visualization are not default verification actions. Keep them
explicit and bounded. Do not delete an existing model/checkpoint or overwrite
an output database until the user has chosen that replacement.

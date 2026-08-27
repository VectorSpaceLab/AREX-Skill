# Cross-cutting troubleshooting

## Purpose

Use this reference for failures that can occur before or across several ART workflows. For workflow-specific details, continue to the nearest sub-skill troubleshooting page.

## Install and import failures

| Symptom | Likely cause | What to do |
|---|---|---|
| `ModuleNotFoundError: No module named 'art'` | The distribution is not installed in the active Python environment. | Install `adversarial-robustness-toolbox`; verify with `python -c "import art; print(art.__version__)"`. |
| ART imports, but a backend wrapper fails | Optional backend package is missing. | Use `setup-and-backends` and `python scripts/inspect_art_install.py --json` to find the missing group. Install only the backend required by the task. |
| TensorFlow prints no-CUDA or GPU library warnings | CPU workflow on a host without matching CUDA libraries. | Treat as informational unless the user specifically needs GPU. If CPU is acceptable, continue. |
| GPy or SciPy fails after upgrading TensorFlow dependencies | Resolver selected incompatible NumPy/SciPy/ml-dtypes combination. | Pin a compatible NumPy/SciPy set for GPy/ART or split TensorFlow and GPy workflows into separate environments. |
| `PyTorchClassifier` tries to use GPU on a CPU-only wheel | ART PyTorch wrappers can default to GPU-oriented device selection. | Pass `device_type="cpu"` explicitly for CPU workflows. |

## Shape, label, and scale failures

| Symptom | Likely cause | What to do |
|---|---|---|
| Attack output shape differs from input | Channel/order or batch dimensions are inconsistent. | Validate `input_shape`, batch axis, `channels_first`, and preprocessor output shape before running attacks. |
| Targeted attack raises label errors or silently behaves untargeted | Missing or incorrectly encoded target labels. | Pass target labels to `generate(x, y=target_y)`; prefer one-hot labels unless the wrapper explicitly accepts class indices. |
| Perturbations are too large or clipped oddly | Attack budget does not match input scale. | Match `eps` and `eps_step` to `clip_values`; for normalized images use fractions such as `8/255`. |
| White-box attack fails on black-box estimator | The estimator lacks `loss_gradient` or `class_gradient`. | Rebuild a gradient-enabled estimator, or choose a compatible black-box/decision attack. |

## Workflow routing mistakes

| If the user asks for... | Route to... |
|---|---|
| Installing ART, checking optional dependencies, or deciding CPU/GPU packages | `sub-skills/setup-and-backends/` |
| Wrapping a model as an ART classifier/regressor | `sub-skills/estimators-and-models/` |
| Generating adversarial examples or adding preprocessors | `sub-skills/evasion-and-preprocessing/` |
| Poisoning, privacy inference, model inversion, extraction, or detectors | `sub-skills/poisoning-inference-extraction/` |
| Metrics, SecurityCurve, GREAT score, tree verification, randomized smoothing, or certification | `sub-skills/evaluation-and-certification/` |

## When to stop and ask for more information

Ask the user before continuing when:

- The task requires a GPU-only model, specialized speech/object-detection/malware runtime, private dataset, credential, or download not covered by the selected CPU-capable scope.
- The user wants to mutate an existing environment in a way that may break other projects.
- The required labels, `clip_values`, input shape, model family, or data scale are unknown and cannot be inferred safely.
- The user wants to run original repository examples, notebooks, or long training jobs rather than a bundled smoke script.

## After a bundled script fails

1. Read the owning sub-skill's troubleshooting reference.
2. Re-run with `--help` to confirm option names.
3. If import-only diagnostics fail, fix the environment first.
4. If tiny synthetic smokes pass but real data fails, compare labels, shapes, clipping, channel order, estimator capabilities, and backend device choices.
5. If the failure involves an out-of-scope workflow such as speech recognition, object detection, malware, or generation, treat it as a refresh/extension request rather than a covered runtime workflow.

# Cross-Cutting Troubleshooting

Use this root reference for install, import, Qt, CLI, ONNX Runtime, model-cache,
and backend symptoms that affect more than one X-AnyLabeling workflow. For
workflow-specific errors, load the nearest sub-skill troubleshooting file.

## Install/import failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: anylabeling` | Package not installed in the active Python. | Install `x-anylabeling-cvhub` in the environment that will run the task. Verify with `python -c "import anylabeling"`. |
| `xanylabeling: command not found` | Console script not on `PATH` or wrong environment active. | Use `python -m pip show x-anylabeling-cvhub`; reinstall in the active environment; run `python -m anylabeling.app version` only as a diagnostic fallback. |
| Version mismatch | Multiple installs or editable checkout shadowing package install. | Run `xanylabeling version` and `python -c "import anylabeling.app_info as i; print(i.__version__)"` in the same environment. |
| Broken dependencies after switching CPU/GPU extras | `onnxruntime` and `onnxruntime-gpu` or incompatible numpy/onnx packages installed together. | Create a clean environment and install exactly one of `cpu`, `gpu`, `gpu-cu11`, or `gpu-cu13`. |
| Import emits Qt multimedia `pipewire-0.3` warnings | Host lacks PipeWire multimedia libraries. | Treat as non-fatal for CLI/version/conversion when commands exit 0. Install system multimedia libraries only if video playback/capture features fail. |

Run the root checker for a concise snapshot:

```bash
python scripts/check_xanylabeling_env.py --show-model-registry --json
```

## Qt/display and GUI launch

| Symptom | Likely cause | Recovery |
|---|---|---|
| GUI does not open in WSL/Wayland | Qt selected an incompatible platform plugin. | Try `xanylabeling --qt-platform xcb ...`; ensure an X server or Wayland bridge is available. |
| `Could not load the Qt platform plugin` | Missing platform plugin libraries or incompatible PyQt/Qt install. | Reinstall package in a clean environment; verify PyQt6 imports; on Linux install required X11/Wayland runtime libraries. |
| Huge image fails to load or reports allocation limit | Qt image allocation limit is too low. | Relaunch with `--qt-image-allocation-limit 1024` or `0` for trusted very-large images. |
| Persisted window/layout state is broken | Qt settings state is corrupt or from an older release. | Run `xanylabeling --reset-config` with the same `--work-dir`. |
| GUI starts but labels/config behave unexpectedly | Wrong `.xanylabelingrc` or inline YAML parsed incorrectly. | Run `xanylabeling config`; set an explicit `--work-dir`; use a valid YAML mapping for `--config`. |

## CLI and conversion symptoms

- `xanylabeling convert` lists tasks, but a task run fails with missing args:
  load `sub-skills/conversion-cli/references/cli-reference.md` and check the
  task's required and mode-specific options.
- Exact label validation fails at GUI launch: use `--labels` or config `labels`
  when `--validatelabel exact` is set; see `sub-skills/annotation-ui`.
- Conversion output is empty: check whether the source label file exists,
  classes/pose mapping matches labels, the selected mode matches shape types,
  and whether `--skip-empty-files` was used.

## ONNX Runtime, CUDA, and TensorRT

| Symptom | Likely cause | Recovery |
|---|---|---|
| `onnxruntime.get_available_providers()` lacks CUDA | CPU extra installed, GPU wheel missing, or driver/runtime mismatch. | Use a clean environment with the matching GPU extra and verify driver/CUDA compatibility. |
| Both CPU and GPU ONNX Runtime packages are installed | Mixed extras or manual pip installs. | Uninstall both and reinstall one backend extra in a fresh environment. |
| TensorRT import error mentions `tensorrt` or `cuda-python` | TensorRT dependencies are optional and absent. | Install `tensorrt cuda-python` only for TensorRT workflows and verify the engine was built for the same GPU/TensorRT major version. |
| TensorRT deserialization fails | `.engine` file built for a different TensorRT version or GPU architecture. | Re-export the engine on the target machine or with matching major TensorRT and compute capability. |
| Model loads on CPU but not GPU | GPU extra/runtime mismatch, unsupported provider, or model-specific backend config. | Verify ONNX Runtime providers first, then read `sub-skills/auto-labeling-models/references/backend-and-downloads.md`. |

## Model downloads and cache

| Symptom | Likely cause | Recovery |
|---|---|---|
| Built-in model download times out | Network, proxy, or selected model hub unavailable. | Use a reachable network, choose ModelScope when appropriate, or manually download and point a custom config's model path to the file. |
| Downloaded model is deleted and redownloaded | Integrity check failed for `.onnx`, `.pt`, or `.pth`, or file was empty. | Redownload from a trusted source; avoid interrupted partial files. |
| Model file path not found | Relative path resolved from current process/config location does not exist. | Use an absolute model path or place the file next to the custom config as intended. |
| Remote/API model fails | Service URL, token, or server contract is wrong/unreachable. | Confirm credentials and service health; do not test with fake tokens. |

## Training/build/localization

- Too few labels, missing pose config, unavailable device, or `ultralytics`/
  `torch` issues: use `sub-skills/developer-workflows/references/troubleshooting.md`.
- PyInstaller target/spec/device mismatch: use
  `sub-skills/developer-workflows/references/packaging-and-localization.md`.
- Translation/resource compiler failures: use developer-workflows localization
  troubleshooting; these workflows mutate generated files.

## Stop conditions

Stop and ask for missing external inputs when a task requires:

- API tokens, private server URLs, or credentials.
- Network downloads that are not already authorized.
- GPU/TensorRT verification on unavailable or incompatible hardware.
- Large model training, benchmark-scale conversion, or executable builds with
  unbounded runtime/side effects.
- Mutation of a user-owned Python environment that might break existing work.

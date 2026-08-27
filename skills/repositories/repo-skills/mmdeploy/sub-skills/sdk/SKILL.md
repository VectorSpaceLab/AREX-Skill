---
name: sdk
description: "Use MMDeploy SDK model directories, runtime FFIs, profiler output,
  and packaged SDK distributions for inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMDeploy SDK Router

Use this sub-skill when the user already has, or needs to consume, an MMDeploy
SDK model directory produced with `--dump-info`; when they ask how to run
`mmdeploy_runtime` from Python; when they need C, C++, Java, or C# SDK inference
patterns; when they have SDK profiler output; or when they need safe guidance on
precompiled SDK/runtime packages.

Do not use this sub-skill for conversion internals, deployment config authoring,
backend toolkit installation, custom-op builds, regression automation, or metric
benchmarking. Route those tasks to the owning conversion, backend, extensibility,
or validation guidance, and return here only for the SDK model directory/runtime
handoff.

## Read These First

- [SDK workflows](references/sdk-workflows.md) — `--dump-info` handoff, Python
  and C/C++ API patterns, language demo coverage, and FFI task mapping.
- [Model directory](references/model-directory.md) — required JSON files,
  backend artifacts, zip-model support, and validation checks for SDK model
  packages.
- [Profiler and packaging](references/profiler-and-packaging.md) — SDK profiler
  data format, bundled analyzer usage, precompiled package concepts, and safe
  packaging caveats.
- [Troubleshooting](references/troubleshooting.md) — symptoms, likely causes,
  recovery steps, and stop conditions for SDK runtime failures.
- [SDK profile analyzer](scripts/sdk_analyze.py) — read-only analyzer for SDK
  profiler text files.

## Route The User Request

1. **Clarify the artifact.** SDK runtime APIs consume a model directory or a
   zip model built for SDK loading. A raw backend file such as `end2end.engine`,
   `end2end.onnx`, `end2end.xml`, or `end2end.param` is not enough for
   `mmdeploy_runtime` task classes because preprocessing and postprocessing live
   in the SDK metadata JSON files.
2. **Check the model package before writing runtime code.** At minimum, the
   directory should contain `deploy.json`, `pipeline.json`, `detail.json`, and
   every backend file named by `deploy.json`. Use
   [Model directory](references/model-directory.md) for a deterministic checklist.
3. **Pick the runtime FFI from the user environment.**
   - Python: import `mmdeploy_runtime` and create the appropriate task class,
     usually `Detector`, `Classifier`, `Segmentor`, `Restorer`,
     `TextDetector`, `TextRecognizer`, `PoseDetector`, `RotatedDetector`, or
     `VideoRecognizer`.
   - C: create a model or task handle, convert input images to `mmdeploy_mat_t`,
     call `*_apply`, release results, and destroy handles.
   - C++: use `mmdeploy::Model`, `mmdeploy::Device` or `mmdeploy::Context`, then
     construct `mmdeploy::<Task>` and call `Apply`.
   - Java/C#: instantiate the generated task wrapper with `(modelPath,
     deviceName, deviceId)` and keep required native libraries discoverable.
4. **Interpret device arguments literally.** Python runtime constructors take a
   `device_name` such as `"cpu"` or `"cuda"` plus a numeric `device_id`. Do not
   pass a converter-style `backend_files` list to SDK task classes, and do not
   pass only an engine file as `model_path`.
5. **For profiler questions, route directly to the analyzer.** If the file is a
   text SDK profile with a graph section, a `----` separator, and event lines,
   run:

   ```bash
   python scripts/sdk_analyze.py profiler_data.txt
   ```

   Then use [Profiler and packaging](references/profiler-and-packaging.md) to
   interpret `occupy`, `usage`, `n_call`, `t_mean`, `t_50%`, and `t_90%`.
6. **For precompiled package questions, distinguish usage from release builds.**
   Installing an existing runtime wheel/package is a user workflow. Building
   release packages is a maintainer workflow that depends on Python ABI,
   platform, device, backend libraries, CMake flags, and licensing constraints.

## Minimal SDK Runtime Checks

Use these only as read-only probes; they do not prove a backend engine is valid:

```bash
python - <<'PY'
import importlib.util
print('mmdeploy_runtime:', importlib.util.find_spec('mmdeploy_runtime') is not None)
PY
```

```python
from mmdeploy.backend.sdk import is_available
print(is_available())  # True only when the Python SDK runtime module is visible
```

If either check is false, do not continue with SDK inference code until the
runtime package or built SDK Python API is available.

## Boundaries And Handoffs

- If `--dump-info` was omitted or the SDK JSON files are missing, hand the user
  back to conversion guidance to regenerate the model directory with SDK info.
- If `mmdeploy_runtime` imports but backend shared libraries or device runtimes
  are missing, use backend guidance for the target backend/device before trying
  another API layer.
- If the user asks for model accuracy, dataset metrics, latency benchmarking, or
  regression matrix automation, use validation guidance. This route only covers
  SDK inference and SDK profiler interpretation.
- If the user asks to modify converters, rewrite transforms, or add new SDK
  task support, use extensibility guidance; this route only consumes the emitted
  SDK package.

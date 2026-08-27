# SDK Profiler And Packaging

This reference covers two SDK-adjacent workflows owned by this sub-skill:
reading SDK profiler output and reasoning about precompiled SDK/runtime package
contents. It does not replace backend installation or regression validation
routes.

## Generating SDK Profiler Data

The SDK profiler is attached through an SDK context before creating the task
handle. In C/C++ terms, the flow is:

1. Create or load an SDK model.
2. Create a profiler that writes to a profile text file.
3. Create a context with the target device.
4. Add the profiler to the context.
5. Create the task with the context-enabled constructor.
6. Run enough inference iterations to get stable timings.
7. Destroy the task/model/profiler/context so the file is flushed.

Minimal C-style sketch:

```c
mmdeploy_model_t model{};
mmdeploy_model_create_by_path("sdk_model_dir", &model);

mmdeploy_profiler_t profiler{};
mmdeploy_profiler_create("profiler_data.txt", &profiler);

mmdeploy_context_t context{};
mmdeploy_context_create_by_device("cpu", 0, &context);
mmdeploy_context_add(context, MMDEPLOY_TYPE_PROFILER, nullptr, profiler);

mmdeploy_classifier_t classifier{};
mmdeploy_classifier_create_v2(model, context, &classifier);

/* warm up, run inference loop, release results */

mmdeploy_classifier_destroy(classifier);
mmdeploy_model_destroy(model);
mmdeploy_profiler_destroy(profiler);
mmdeploy_context_destroy(context);
```

The same idea applies to C++ by adding `mmdeploy::Profiler` and
`mmdeploy::Device` to a `mmdeploy::Context` before constructing the task object.

## Profiler File Format

The analyzer expects a **text** file with two sections:

```text
<node-name> <node-address> [child-address ...]
<node-name> <node-address> [child-address ...]
----
<node-address> <kind> <call-index> <timestamp>
<node-address> <kind> <call-index> <timestamp>
```

Interpretation:

- The graph section names pipeline nodes and their child addresses.
- A line containing exactly `----` separates graph from events.
- Event `kind` is `0` for start and nonzero for finish.
- Timestamps are emitted by the SDK profiler; the analyzer reports duration
  columns in milliseconds.
- Every event address must exist in the graph section.

If a profile file has no `----` separator, route to
[Troubleshooting](troubleshooting.md): it may be a different profiler output,
an incomplete file, or a file that was not flushed by destroying the profiler.

## Analyze A Profile

Run the bundled read-only analyzer from this sub-skill:

```bash
python scripts/sdk_analyze.py profiler_data.txt
```

Expected output columns:

| Column | Meaning | Bottleneck signal |
| --- | --- | --- |
| `name` | Pipeline node name, nested under parent nodes. | Identify stage: preprocess, backend net, postprocess, pipeline. |
| `occupy` | Fraction of total active time occupied by this node when it is a leaf. | High value means this leaf dominates wall time. |
| `usage` | Occupancy multiplied by concurrent active-call count. | High value can indicate repeated or overlapping work. |
| `n_call` | Number of calls observed. | Unexpectedly high calls can indicate batching or pipeline expansion issues. |
| `t_mean` | Mean duration per call in milliseconds. | High mean means one call is slow. |
| `t_50%` | Median-like percentile in milliseconds. | Compare with mean for outliers. |
| `t_90%` | 90th percentile in milliseconds. | High tail latency indicates unstable stages. |

Rows with children display `-` for `occupy` and `usage` because their child
leaves explain the time. For a bottleneck request, sort mentally by high leaf
`occupy` first, then by high `t_mean` and `t_90%`. Common outcomes:

- Backend net dominates: check backend/device choice, engine optimization, and
  input shape/profile.
- Preprocess dominates: inspect image transforms, input resolution, host-device
  copies, and whether fused preprocessing is available for the model.
- Postprocess dominates: inspect task-specific thresholds, NMS, OCR decoding, or
  result size.
- `n_call` is much higher than expected: inspect batching, nested pipelines, and
  repeated composite steps such as detection-then-pose.

## Precompiled Package Concepts

MMDeploy distribution has separate but related package surfaces:

| Surface | Purpose |
| --- | --- |
| Model converter package | Python package containing conversion APIs and deployment helpers. |
| SDK C/C++ package | Native SDK libraries, headers, examples, setup scripts, and backend runtime libraries. |
| SDK Python runtime package | Python module `mmdeploy_runtime` plus native libraries for task classes. |
| Language bindings | Java/C# wrappers that depend on generated classes/NuGet package and native libraries. |

A maintainer precompiled build generally:

1. Generates a build configuration for target system, device, backend, and SDK
   flags.
2. Builds the converter package when requested.
3. Builds and installs SDK native libraries when SDK output is requested.
4. Builds the SDK Python API wheel for the selected Python ABI(s) when requested.
5. Copies required backend runtime libraries and example programs into the
   package output.
6. Runs package smoke checks such as importing `mmdeploy_runtime` and applying a
   simple classifier model.

Do not copy package-building scripts into this sub-skill runtime tree. They are
maintainer/release automation with external toolchain and artifact assumptions;
this sub-skill keeps them as distilled operational guidance.

## Safe Packaging Caveats

Before building or consuming a precompiled package, confirm:

- **Platform and architecture:** Linux versus Windows, x86_64 versus target
  embedded architecture, and compiler/runtime ABI.
- **Python ABI:** the `mmdeploy_runtime` wheel tag must match the target Python
  major/minor and platform tag.
- **Device stack:** CUDA, cuDNN, TensorRT, ONNXRuntime, OpenCV, and vendor SDKs
  must match the package build notes for GPU/accelerator packages.
- **SDK flags:** required flags include SDK build, language binding build, static
  versus dynamic/monolithic choice, dynamic-net support, and optional zip-model
  support.
- **Library discovery:** native libraries must be on the process library path or
  packaged next to the binding in a way the platform loader recognizes.
- **Licensing:** do not redistribute proprietary backend libraries unless the
  package owner has the right to do so.
- **Environment isolation:** package builds should run in clean build
  environments. Do not mutate a user's existing research environment just to
  repair package build dependencies.
- **Smoke checks:** at minimum, verify runtime import, task class availability,
  model directory loading, and one simple inference path for each packaged
  backend/device variant.

Stop rather than guessing when the user lacks the target device, proprietary SDK,
matching backend library version, or build logs needed to diagnose a package
failure.

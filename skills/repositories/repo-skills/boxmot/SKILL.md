---
name: boxmot
description: "Use BoxMOT for multi-object tracking, benchmark replay, ReID model
  lifecycle workflows, and native C++ tracker backends."
metadata:
  disco-role: operating
disable-model-invocation: true
license: AGPL 3.0
---

# BoxMOT

BoxMOT is the skill to use when the user wants to track objects, run MOT benchmarks, train or compare ReID models, export ReID checkpoints, or switch trackers to native C++ backends.

## Quick install and smoke check

For a public install, use the package itself:

```bash
pip install boxmot
boxmot --help
python -c "import boxmot; print(boxmot.__version__)"
```

If you are working from a source checkout, `uv sync --all-extras --all-groups` is the broadest dev-friendly install, but the runtime skill should stay usable from the published package too.

If the CLI or import fails, read:
- [install and inspect](references/install-and-inspect.md)
- [cross-cutting troubleshooting](references/troubleshooting.md)
- [repo provenance](references/repo-provenance.md)

## Route map

### `tracking-and-trackers`
Use this route for direct tracking, tracker construction, tracker defaults, AABB/OBB detection layouts, output schemas, and tracker-level debugging.

Typical prompts:
- track a webcam or video with a specific tracker
- explain tracker output columns or OBB input shapes
- instantiate a tracker from Python and inspect its results
- debug shape errors or missing `det_ind` values

Read:
- `sub-skills/tracking-and-trackers/SKILL.md`
- `sub-skills/tracking-and-trackers/references/workflows.md`
- `sub-skills/tracking-and-trackers/references/data-formats.md`

### `benchmark-workflows`
Use this route for cached `generate` / `eval` / `tune` / `research` workflows, benchmark YAMLs, cache reuse, public detections, and postprocessing.

Typical prompts:
- generate caches for a benchmark
- reuse an existing cache with a different tracker
- tune tracker hyperparameters on MOT17 or MMOT
- debug benchmark config selection or split handling

Read:
- `sub-skills/benchmark-workflows/SKILL.md`
- `sub-skills/benchmark-workflows/references/benchmark-workflows.md`
- `sub-skills/benchmark-workflows/references/configuration.md`

### `reid-lifecycle`
Use this route for training ReID backbones, evaluating checkpoints, comparing multiple checkpoints, exporting to ONNX/OpenVINO/TensorRT/TFLite, and generating embeddings.

Typical prompts:
- train a ReID model on a dataset or recipe
- evaluate or compare checkpoints across target datasets
- export a ReID model for deployment
- debug dataset, preprocess, or export-format issues

Read:
- `sub-skills/reid-lifecycle/SKILL.md`
- `sub-skills/reid-lifecycle/references/reid-lifecycle.md`
- `sub-skills/reid-lifecycle/references/model-and-export-overview.md`

### `native-cpp-backends`
Use this route for `--tracker-backend cpp`, `boxmot build`, native C++ live tracking, native replay, and embedding the trackers in your own C++ program.

Typical prompts:
- build the native trackers
- switch a supported tracker to the C++ backend
- understand supported native tracker coverage
- troubleshoot build-tool or backend-selection failures

Read:
- `sub-skills/native-cpp-backends/SKILL.md`
- `sub-skills/native-cpp-backends/references/native-cpp.md`
- `sub-skills/native-cpp-backends/references/troubleshooting.md`

## Public package facts

- CLI entry point: `boxmot`
- Public Python facade: `boxmot.BoxMOT`
- Public detector wrapper: `boxmot.Detector`
- Public ReID wrapper: `boxmot.ReIDModel`
- Package-level tracker export: `boxmot.trackers.OccluBoost`
- Supported tracker names are defined in `boxmot.trackers.registry.TRACKER_MAPPING`
- Detection layouts switch automatically from tensor shape:
  - AABB: `(N, 6)` input -> `(N, 8)` output
  - OBB: `(N, 7)` input -> `(N, 9)` output

## When to start here

If the user only says "use BoxMOT", start with the route that matches the task family and then open the nearest sub-skill reference. If the request names a CLI flag, benchmark id, tracker name, ReID checkpoint, output schema, or C++ backend, use that signal to choose the route immediately.

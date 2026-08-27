---
name: export
description: "Export, profile, and prepare NanoTrack split backbone/head models
  for ONNX and deployment handoff with explicit shape, artifact, and benchmark
  safeguards."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# NanoTrack Export and Deployment Handoff

## Use This Sub-skill When

Use this sub-skill for NanoTrack requests involving:

- split backbone/head ONNX export;
- ONNX input, output, name, or opset inspection;
- optional ONNX simplification planning;
- MAC, parameter, model-size, or throughput measurement;
- a bounded handoff to NCNN or a mobile inference implementer.

This guidance covers the maintained NanoTrack workflow. Treat other SiamTrackers
snapshots as catalog entries unless another sub-skill explicitly owns them.

## Route Elsewhere

- Route frame preprocessing, template caching, search updates, and result
  decoding to the `inference` sub-skill.
- Route optimization, loss, data loading, and checkpoints produced by learning
  to the `training` sub-skill.
- Route dataset metrics and benchmark protocols to the `evaluation` sub-skill.
- Android, iOS, macOS, C++, NCNN builds, and third-party conversion services are
  documentation-only boundaries here; this sub-skill does not claim those
  toolchains work.

## Start From the Verified Contract

The source export intent is a two-graph NanoTrackV3 contract:

| Graph | Inputs | Outputs | Opset |
| --- | --- | --- | --- |
| backbone | `input`: `[1,3,255,255]` | `output`: `[1,96,16,16]` | 14 |
| head | `input1`: `[1,96,8,8]`; `input2`: `[1,96,16,16]` | `output1`: `[1,2,15,15]`; `output2`: `[1,4,15,15]` | 14 |

`output1` is the classification tensor and `output2` is the positive
localization tensor returned by the NanoTrackV3 head. Read
[export-reference.md](references/export-reference.md) before changing graph
boundaries, spatial axes, head variant, or preprocessing assumptions.

This is an evidence-backed intended contract, **not** a claim that an export was
successfully run or validated. A compatible configuration and trusted weights
are required. No weights are bundled with this skill.

## Choose a Workflow

### Validate a proposed split contract

Run the no-write checker from this sub-skill directory:

```bash
python scripts/export_shape_check.py
```

To inspect already-created ONNX graphs, install `onnx` in the caller-controlled
environment and pass both files:

```bash
python scripts/export_shape_check.py \
  --backbone-model artifacts/backbone.onnx \
  --head-model artifacts/head.onnx
```

The paths above are placeholders for caller-owned artifacts. The checker never
downloads, exports, creates directories, or overwrites files.

### Plan output artifacts safely

Use a caller-owned staging directory and relative names. Names are examples,
not required filenames:

```bash
python scripts/export_shape_check.py \
  --artifact-root artifacts \
  --backbone-name release/backbone-v3.onnx \
  --head-name release/head-v3.onnx
```

The checker rejects absolute artifact names, `..` traversal, duplicate targets,
non-ONNX suffixes, and existing targets unless explicitly acknowledged.
Read [export-reference.md](references/export-reference.md) for export,
validation, simplification, and manifest gates.

### Plan profiling or throughput work

Validate a benchmark plan without importing PyTorch or running long loops:

```bash
python scripts/profile_shape_check.py \
  --device cpu --timer wall --warmup 100 --iterations 1000 --repeats 5
```

For wall-clock CUDA timing, require synchronization around each timed region:

```bash
python scripts/profile_shape_check.py \
  --device cuda --timer wall --synchronize \
  --warmup 100 --iterations 1000 --repeats 5
```

Read [performance.md](references/performance.md) before interpreting MACs as
FLOPs, comparing model file sizes, or reporting FPS.

## Safe Export Gates

1. **Variant gate:** confirm the backbone, adjust channels, head implementation,
   and checkpoint all belong to the same NanoTrack version.
2. **Weight gate:** load a trusted checkpoint with key/shape diagnostics; do not
   silently profile or export random initialization.
3. **Mode gate:** use one model instance in evaluation mode and disable gradient
   recording during representative forwards.
4. **Shape gate:** verify template image `127x127`, search image `255x255`,
   backbone features `96x8x8` and `96x16x16`, and head outputs `2x15x15` and
   `4x15x15` for NanoTrackV3.
5. **Artifact gate:** write to a new caller-owned staging path, never a hard-coded
   repository-relative destination and never over an existing artifact by
   default.
6. **ONNX gate:** check graph syntax, opset, names, dtypes, and static/dynamic
   dimensions, then compare outputs in a separate runtime when available.
7. **Simplification gate:** preserve the unsimplified graph, write simplification
   to a distinct name, check the simplifier result flag, and rerun parity.
8. **Deployment gate:** record hashes and preprocessing/postprocessing contracts;
   conversion alone does not prove mobile correctness or speed.

## Important Static-Shape Warning

A backbone exported only from `[1,3,255,255]` without dynamic axes is normally a
static search graph. The head nevertheless needs a template feature of
`[1,96,8,8]`, which comes from the `127x127` template path in PyTorch. Do not
assume one static `255x255` ONNX backbone also accepts `127x127`. Choose and
validate one explicit design: dynamic spatial axes, separate template/search
backbone artifacts, or a deployment pipeline with an independently justified
template-feature path.

## Dependency and Backend Policy

- `torch` is needed to instantiate and export the model.
- `onnx` is optional but required for structural graph checking.
- `onnxruntime` is optional and useful for numerical parity.
- `onnxsim` is optional; simplification is not an automatic success gate.
- `thop` is optional and provides MAC/parameter estimates, not universal FLOP
  semantics.
- Historical environment pins are compatibility clues, not install commands.
  Resolve versions against the current Python, PyTorch, ONNX, and target-runtime
  compatibility matrices instead of copying obsolete pins.
- Prefer CPU export for portability when supported. If CUDA is selected, record
  device/backend details and synchronize timing; CUDA availability alone does
  not prove ONNX or mobile backend support.

## Known Limits

No dataset benchmark, full tracker run, training run, ONNX export, numerical
parity run, NCNN conversion, or mobile build is proven by this sub-skill. The
source export workflow used snapshots, hard-coded output paths, and automatic
CUDA selection. Its speed loop warmed up 100 times and timed 1000 `track` calls;
that is methodology evidence, not a safe construction-time smoke test.

Use [troubleshooting.md](references/troubleshooting.md) for missing weights,
variant mismatches, shape errors, optional dependencies, CUDA timing, ONNX
simplification, and deployment-boundary failures.

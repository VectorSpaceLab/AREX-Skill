# Cross-Cutting Troubleshooting

## Read this first

Use this page when setup/import, optional dependencies, data/config paths,
checkpoints, compiled extensions, or backend behavior is unclear. Diagnose the
smallest offline gate before running a GUI, dataset download, benchmark, or
long training job.

## Install and import failures

**Symptom:** `ModuleNotFoundError` for `torch`, `cv2`, `yacs`, `Cython`,
`tqdm`, `PIL`, `shapely`, `colorama`, `tensorboard`, `thop`, or `wget`.

**Recovery:** install only the dependencies owned by the selected route in an
isolated environment, then run the bundled
[`check_environment.py`](../scripts/check_environment.py). Do not copy the
repository's historical all-in-one pins into a current Python environment;
choose a mutually compatible PyTorch/CUDA/Python set first. `thop` and ONNX
packages are optional for profiling/export, while `yacs` and a compatible
PyTorch/OpenCV stack are needed for NanoTrack model/config use.

**Symptom:** a source checkout imports one root package but not another.

**Recovery:** the collection is not one reliable modern distribution. Confirm
which implementation root is selected, expose that root according to the
checkout's packaging policy, and avoid mixing similarly named modules from two
snapshots. The generated skill itself does not require an original checkout
path and its offline helpers do not import the tracker.

## Compiled region extension

**Symptom:** `ImportError` from `toolkit.utils.region`, such as
`undefined symbol: _Py_ZeroStruct`, or evaluation imports fail while core model
imports pass.

**Cause:** the checkout contains prebuilt `.so` binaries tied to older Python
ABIs. A binary that imports on Python 3.6–3.8 is not portable to Python 3.10+
without rebuilding.

**Recovery:** use the bundled [region extension builder](../scripts/build_region_extension.py)
with an explicit implementation root. It copies the source into a temporary
folder and runs the local build contract without mutating the source by default.
Install Cython and a C compiler in the selected environment first. This legacy
`.pyx` built successfully with Python 3.10 and Cython 0.29.37; Cython 3.x
produced source errors and Cython 0.29 on Python 3.13 produced Python C-API
compile errors. Start with an isolated Python 3.10/3.11-compatible prefix and
`Cython<3` rather than mutating a modern environment. Do not delete or
overwrite shared user artifacts as a first step. If the rebuild is unavailable,
keep benchmark/evaluation readiness explicitly blocked; do not substitute a
stale binary with a CPU import claim.

## Configuration and variant mismatches

**Symptom:** tensor channel/shape errors, missing `ban_head`, unexpected output
grid, or a model that works only after another variant was run.

**Recovery:** use one fresh process per V1/V2/V3 variant. Merge the matching
config, select the matching BAN head, verify the channel count and output grid,
then construct `ModelBuilder()`. V1/V2 use the 64-channel/16-grid path; V3
uses a 96-channel path and 15-grid tracking output. Do not rely on a YAML merge
to clear mutable global `cfg` or head registry state.

**Symptom:** `cfg.CUDA` is true but CPU model execution calls `.cuda()`, or a
CUDA model is left on CPU.

**Recovery:** choose one device, set `cfg.CUDA` to match it before tracker
initialization, move the model to that device, and fail explicitly when CUDA
was required but unavailable. A CUDA availability probe is not a checkpoint or
end-to-end model proof.

## Data, checkpoint, and CLI failures

**Symptom:** training cannot find images/annotations, or dataset length is zero.

**Recovery:** validate that the selected `DATASET.NAMES` entries have real
`ROOT` and `ANNO` values. The documented GOT-10k default expects cropped
`crop511` images plus `train.json`; empty defaults for VID/YouTubeBB/DET/COCO/
LaSOT must be removed from the active dataset list or populated. Use the
training config checker before launching.

**Symptom:** checkpoint is missing, unreadable, or gives unexpected keys.

**Recovery:** use a checkpoint from the same variant, inspect its state-dict
keys before moving it to a device, and compare the backbone/head/config channel
contract. The bundled inference preflight checks only explicit file existence;
it does not load or validate checkpoint tensors.

**Symptom:** CLI `--help` works but a real `test`/`eval` run fails.

**Recovery:** check the dataset root, tracker name, snapshot, result directory,
protocol-specific result format, and compiled region extension. Test and demo
entry points are data/checkpoint-bound; evaluation also starts multiprocessing
and may open windows when visualization is enabled. Keep `--vis` off during the
first run.

## Optional evaluation/export/performance dependencies

- Use the evaluation result-layout checker before importing or starting
  benchmark workers. It is offline and uses only the standard library.
- Use the export shape checker before writing ONNX artifacts; install `onnx`
  only when inspecting an existing graph. Stage outputs in a new directory and
  do not permit accidental overwrite.
- Use the profile shape checker to review timing boundaries, warmups, device,
  synchronization, and metric provenance. It deliberately does not execute the
  model or turn MACs into FLOPs.
- `jpeg4py`, `mpi4py`, `ray`, and `hyperopt` are not required for the core
  static/API graph; add them only when a selected legacy workflow proves it
  needs them.

## Performance and deployment limits

The source throughput helper warms a cached template and times repeated search
calls, but CUDA operations are asynchronous unless synchronized. Report device,
input shapes, warmups, iterations, preprocessing/postprocessing/transfer
boundaries, and repeat statistics. Do not compare the README FPS table with a
new measurement without matching those conditions.

ONNX export in the source is split into backbone and head graphs and uses a
V3-specific shape/opset contract. Validate graph names/shapes/opset and numeric
parity before handing the graphs to an external NCNN/mobile converter. Android,
macOS native, C++, and NCNN builds remain deployment-owner work; they are not
proven by a PyTorch import.

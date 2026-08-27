# Legacy workflow patterns

This reference distills recurring shapes from the collection's root and variant
READMEs, setup metadata, requirements files, and representative `bin/` files.
Backticked source names are provenance labels only. The commands below are
**safe workflow shapes**, not copy-paste commands against the vanished source
checkout. Replace placeholders only after the user has supplied an authorized
current checkout and the selected snapshot has passed the artifact/config
checks.

## Preconditions and evidence grades

Before treating a workflow as executable, record each item as `present`,
`absent`, or `unverified`:

- selected source root and package import root;
- selected config file and model/checkpoint path;
- setup.py or an equivalent build recipe;
- Python/PyTorch/vision/CUDA compatibility plan;
- Cython region sources and a fresh build result for the active interpreter;
- dataset image/annotation layout and protocol toolkit;
- writable result/log directory;
- GPU count/memory if training or distributed launch is requested.

The collection evidence supports the following confidence classes:

- **Pattern evidence:** a README or launcher names a step, but execution was
  not performed here.
- **Source evidence:** the corresponding Python/config/build files are locally
  present in the inspected snapshot.
- **Runtime evidence:** only a separately recorded fresh smoke or end-to-end
  run can establish this. The current catalog has no full tracking/training/
  evaluation/export run to report.

## Common region-extension pattern

Several pysot-shaped variants carry the same conceptual extension:

- Cython wrapper: `toolkit/utils/region.pyx`;
- C source: `toolkit/utils/src/region.c`;
- extension name: commonly `toolkit.utils.region`;
- build intent: cythonize the extension in place from the selected snapshot
  root.

The local setup metadata explicitly shows this pattern for SiamBAN, SiamMask,
SiamRPN-pysot, SiamRPNpp, TrTr, and NanoTrack. Region sources also appear in
DaSiamRPN, SiamCAR, SiamFCpp-pysot, UpdateNet, and the video-analyst VOT
benchmark, but some of those snapshots do not contain a local top-level
setup.py. Do not copy a setup.py from a sibling without first confirming the
package path and extension name.

A generic, user-controlled build plan is:

1. activate an isolated environment selected for the snapshot;
2. inspect the local setup metadata and source filenames;
3. remove or ignore stale binary outputs from another Python ABI;
4. run the snapshot's own build command, if its setup metadata supports one;
5. import the newly built extension in the same interpreter;
6. only then run a minimal toolkit geometry check and proceed to data/model
   validation.

The checkout's prebuilt `NanoTrack/toolkit/utils/region.so` is ABI-incompatible
with Python 3.13. More generally, any `region*.so` carrying a Python-3.6,
3.7, or 3.8 ABI tag is evidence of a historical build, not proof of current
importability. The final verification should build an isolated extension.

## Variant setup and requirements inventory

| Snapshot | Local setup.py | Local requirement file | Region/build interpretation |
|---|---|---|---|
| NanoTrack | Yes | No | Explicit `toolkit.utils.region`; maintained build metadata |
| DaSiamRPN | No | No | Region sources and historical binary; no local one-command setup contract |
| LightTrack | No | No | Reference-only; no implementation |
| Ocean | No | No | Reference-only; no implementation |
| SiamBAN | Yes | No | Explicit common region extension |
| SiamCAR | No | `requirement.txt` | Region sources, but build metadata is incomplete in this snapshot |
| SiamDW-FC | No | No | No common region source/setup found |
| SiamDW-RPN | No | `requirement.txt` | No common region source/setup found |
| SiamFC | No | No | No common region source/setup found |
| SiamFCpp-pysot | No | `requirement.txt` | Region sources, but no local top-level setup found |
| SiamFCpp-video_analyst | Nested VOT setup only | `requirements.txt` | Framework plus nested VOT extension; `compile.sh` is a wrapper-shaped step |
| SiamMask-pysot | Yes | No | Explicit common region extension |
| SiamRPN root | No | `requirement.txt` | No common region source/setup found |
| SiamRPN-pysot | Yes | No | Explicit common region extension |
| SiamRPNpp | Yes | No | Explicit common region extension |
| TrTr-pysot | Yes | No | Explicit common region extension |
| UpdateNet-DaSiamRPN | No | No | Region sources and updater/base code, but no local setup contract |

The root `requirements.txt` is a shell-style historical installer recipe, not a
portable requirements lock. It mentions Python 3.8, CUDA 10, PyTorch 1.7.0,
old Pillow, and additional packages. Do not execute it blindly.

## Train/test/eval patterns by family

### Maintained NanoTrack pattern

Source evidence in `NanoTrack/README.md` and `NanoTrack/bin/` exposes these
logical stages:

1. choose V1, V2, or V3 by matching the head import and config values;
2. provide cropped GOT-10k-shaped training data and benchmark data separately;
3. build the region extension;
4. train with the training launcher;
5. test with the test launcher;
6. evaluate with the evaluation launcher;
7. optionally run hyperparameter search, FLOPs/speed measurement, or model
   conversion.

The maintained siblings own detailed execution. This catalog only verifies that
variant choice precedes data/config/checkpoint choice and that deployment claims
remain separate from benchmark claims.

### Pysot-shaped train/test/eval pattern

SiamBAN, SiamCAR, SiamFCpp-pysot, SiamMask, SiamRPN-pysot, SiamRPNpp, and TrTr
share a broad family resemblance:

- config and model roots under the selected snapshot;
- `my_train.py` or a variant-specific training file;
- `my_test.py` or `test.py`, commonly taking a dataset and snapshot/config;
- `my_eval.py` or `eval.py`, commonly aggregating result files;
- `cmd_dist_train.sh`, `cmd_test.sh`, or `cmd_eval.sh` loops over checkpoint
  names in several snapshots;
- toolkit code for dataset/result evaluation.

This resemblance is a routing aid, not permission to substitute files. Shell
launchers often hard-code checkpoint ranges, dataset names, GPU counts, ports,
result paths, and wildcard patterns. Rewrite the intended operation in a
reviewable run plan rather than copying a legacy launcher.

A safe abstract sequence is:

```text
validate isolated environment
→ build selected region extension, if required
→ validate config ↔ model family ↔ dataset contract
→ run one bounded test on a supplied small sequence
→ inspect result format and logs
→ run evaluation only with a complete protocol dataset
→ train or distributed-train only after a dry-run and resource check
```

### Classic/standalone patterns

- **DaSiamRPN:** variant README exposes `my_test.py` and `my_eval.py` plus
  named VOT/OTB model artifacts. No setup/requirements contract is present.
- **SiamFC:** model-number `my_test.py`, `my_eval.py`, and `my_train.py` patterns
  exist; dataset and model directories must be checked rather than assumed.
- **SiamDW-FC/RPN:** `my_test.py` takes a `model_path`; training is represented
  in `my_train.py` for RPN and FC, and test loops enumerate numbered model files.
  RPN has a requirement file; FC does not.
- **SiamRPN root:** train/eval/test scripts use model-path and data-path style
  arguments; its requirement file names legacy packages. Do not confuse it with
  the pysot snapshot.
- **UpdateNet:** first create template data, then run staged updater training,
  then test through the DaSiamRPN base with an updater checkpoint. The README
  documents stages 1.1 through 3.2 and a geometry workaround; neither should
  be collapsed into a one-step tracker run.

### SiamFCpp video-analyst pattern

The video-analyst snapshot has a framework-specific config/model pipeline. Its
source evidence includes `compile.sh`, `bin/my_train.py`, `bin/my_test.py`,
`bin/train.py`, `bin/test.py`, distributed launchers, HPO, dataset/config/model
roots, and a nested VOT benchmark build. The README describes a framework
compile step and a model-path argument. Keep this route separate from the
pysot-shaped SiamFCpp snapshot; their configs, package roots, and requirements
are not interchangeable.

### SiamMask pattern

SiamMask extends the pysot-shaped pattern with mask-capable model/config and
mask datasets. The train/test/eval/demo family is present. A box-only test is
not evidence of mask functionality: require mask labels, mask config, mask
checkpoint, and mask result schema for a mask request.

## Dataset and model acquisition pattern

The READMEs name external archives for GOT-10k, VOT, OTB, UAV, LaSOT,
ILSVRC/VID/DET, COCO, YTB-Crop511, TrackingNet, YTB-VOS, and DAVIS, as well as
model/checkpoint archives. Those names and links are provenance only. No future
runtime should assume that an external archive, password, official repository,
or network service is available.

Ask the user to provide or authorize:

- a local dataset root and its license/usage status;
- exact protocol (for example, OTB, VOT, GOT-10k, or a custom sequence);
- annotation format and expected split;
- exact checkpoint file and checksum/source;
- preprocessing/cropping version;
- model/config pair and output directory.

Then perform only local validation: existence, non-empty files, expected
subdirectories, annotation parse, image readability, checkpoint load, and
result schema. A directory named `datasets`, a result archive, a README metric,
or a model filename in a default argument is not enough.

## Deployment and export patterns

### NanoTrack

The collection README documents PyTorch, PyTorch-to-ONNX, and an ONNX-to-NCNN
shaped path, and mentions mobile/embedded demos. Route implementation and
conversion details to the `export` sibling. Before claiming deployment, verify
operator compatibility, input tensor names/shapes, preprocessing/postprocessing,
state handling, numerical tolerance, target runtime, and measured latency on the
actual device. Do not use README FPS tables as a fresh performance result.

### Alternative snapshots

Most alternative snapshots expose a Python `demo.py` or `my_demo.py` that
accepts a video/image path and a model/config pair. This is an inference/demo
pattern, not a portable deployment artifact. The catalog does not find a
maintained export contract for DaSiamRPN, SiamBAN, SiamCAR, SiamDW, SiamFC,
SiamRPN families, SiamMask, TrTr, or UpdateNet. Route a deployment request to
NanoTrack unless the user explicitly accepts a custom adaptation and supplies a
verification target.

For a custom alternative deployment, require:

1. a bounded single-sequence smoke test;
2. stable output box/mask schema;
3. a device/backend compatibility check;
4. numerical comparison against the source Python path;
5. latency and memory measurements under a stated protocol;
6. explicit treatment of unsupported ops and stateful template updates.

## Historical result handling

The collection READMEs contain VOT/OTB/UAV/GOT-10k tables and FPS claims for
several snapshots. Preserve them only as historical provenance. A current report
must identify variant, commit/version, config, checkpoint, dataset split,
protocol toolkit, hardware, software versions, and whether the number was
reproduced. Never combine numbers from NanoTrack, LightTrack, a reference-only
entry, or a different snapshot into a new ranking.

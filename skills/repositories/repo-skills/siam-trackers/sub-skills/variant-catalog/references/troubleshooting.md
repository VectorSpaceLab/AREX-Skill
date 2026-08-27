# Variant-catalog troubleshooting

Use this as a decision tree. Stop at the first unresolved gate; do not “fix” a
legacy tracker by silently mixing dependencies or copying a sibling's files.
All commands are illustrative checks in a user-authorized isolated environment,
not instructions to reopen the original collection checkout.

## 1. Legacy dependency conflicts

### Symptoms

- resolver failure around `torch`, `torchvision`, `numpy`, `opencv-python`,
  `Cython`, `scipy`, `numba`, or `Pillow`;
- import errors mentioning removed symbols or an old binary ABI;
- a requirement file demands PyTorch 1.2.0/1.4.0 or Cython 0.27.3 while the
  available environment is modern;
- a package name such as `panda` or `sklearn` is requested instead of the
  maintained package name expected by the code;
- installation of the root shell-style recipe attempts CUDA 10 or an old
  conda/Python combination.

### Interpretation

The root `requirements.txt`, `SiamCAR/requirement.txt`,
`SiamFCpp/SiamFCpp-pysot/requirement.txt`, `SiamDW/SiamDW-RPN/requirement.txt`,
`SiamRPN/SiamRPN/requirement.txt`, and
`SiamFCpp/SiamFCpp-video_analyst/requirements.txt` describe historical
compatibility environments. Their pins are evidence about the code's era, not
instructions to downgrade a working host or to install obsolete CUDA blindly.

### Safe response

1. Record the selected snapshot and the exact conflicting requirement.
2. Use a fresh isolated environment; do not mutate a user-provided environment
   without approval.
3. Probe imports and versions one package at a time before installing broad
   extras.
4. Prefer the smallest environment that supports the requested scope. A
   catalog-only answer needs no ML installation; a region-only check needs
   Cython and a compiler; a tracker smoke needs the model stack; training and
   framework evaluation need more.
5. If a package cannot be built for the target Python, either choose a
   supported isolated interpreter or mark the alternative blocked. Do not
   replace the snapshot with NanoTrack while reporting it as the same variant.
6. Preserve both the historical pin and the tested modern/compatibility choice
   in the run record.

The private inspection environment used during construction was Python 3.13
with PyTorch 2.13.0+cu130, CUDA preparation smoke passing on an A100 SM80 when a
free device was selected, and yacs/Cython/colorama/wget installed; `pip check`
passed. Those facts support inspection and preparation only. They do not prove
that every legacy snapshot runs on that stack.

## 2. `region` import/build failures

### Symptoms

- `ImportError: ... region`;
- “cannot import name region” from toolkit evaluation;
- `undefined symbol`, “wrong ELF class”, or a filename tagged for Python 3.6,
  3.7, or 3.8;
- Cython compilation failure after a stale `.so` is found;
- `setup.py` cannot be found for a snapshot that has `region.pyx`.

### Safe diagnosis

- Inspect the selected snapshot's own region wrapper, C source, package path,
  and setup metadata.
- Confirm that the active interpreter is the one used to build the extension.
- Remove stale build outputs only inside the authorized working copy, then
  rebuild using the selected snapshot's own metadata or an explicitly reviewed
  equivalent.
- Import the extension in a clean process and run a tiny geometry operation.
- Keep the build log and interpreter/ABI facts outside the runtime skill.

The checkout contains a prebuilt `NanoTrack/toolkit/utils/region.so` that is
ABI-incompatible with Python 3.13. Never cite that file as evidence of current
evaluation import. Other Python-version-tagged binaries are likewise historical
artifacts. Final verification must build an isolated extension.

### Snapshot-specific interpretation

- **Explicit setup.py:** NanoTrack, SiamBAN, SiamMask, SiamRPN-pysot,
  SiamRPNpp, and TrTr have local setup metadata for the common extension.
- **Region sources but no top-level setup.py found:** DaSiamRPN, SiamCAR,
  SiamFCpp-pysot, UpdateNet, and the video-analyst VOT benchmark. Require a
  reviewed build plan; do not borrow a sibling setup file implicitly.
- **No common region family found:** SiamDW-FC, SiamDW-RPN, SiamFC, and the
  classic SiamRPN root. Do not add a region build gate unless the selected
  workflow actually imports it.

## 3. Missing or mismatched data

### Symptoms

- loader says a dataset directory, JSON, annotation, image, or crop is absent;
- zero samples are discovered from a non-empty-looking dataset directory;
- VOT restart/EAO evaluation cannot parse result files;
- training starts with a shape/key error;
- mask training finds boxes but no segmentation labels.

### Response

Validate the dataset contract before launching the tracker:

- exact dataset/protocol and split;
- root directory and expected nested names;
- image extension/readability;
- annotation schema and coordinate convention;
- crop/preprocessing format for training;
- mask labels for SiamMask;
- result filename/schema expected by the selected toolkit.

Do not acquire data from an unapproved archive or assume the collection's README
links remain live. Ask for an authorized local artifact or stop with a precise
missing-data report. A small source-tree `data/`, `datasets/`, or `results/`
directory may contain code, placeholders, logs, or sample outputs rather than a
complete benchmark.

## 4. Missing or mismatched model/checkpoint/config

### Symptoms

- default snapshot path does not exist;
- `state_dict` keys do not match the package;
- config names a backbone/head absent from the selected snapshot;
- model loads but output shape or mask branch is wrong;
- a shell loop requests numbered checkpoints that are not supplied.

### Response

Treat variant, config, and checkpoint as an atomic tuple. Check:

1. exact selected variant and package root;
2. config schema and model family;
3. checkpoint format (`.pth`, `.pkl`, `.tar`, or other);
4. expected key names and device map;
5. preprocessing/input size and output heads;
6. checksum or trusted provenance supplied by the user.

Never substitute a NanoTrack checkpoint for an alternative, or an AlexNet
checkpoint for a ResNet/mask/transformer config, merely to make an import pass.
If the README lists a model archive but the user has not supplied it, classify
model acquisition as unresolved.

## 5. Wrong variant selection

Use the following disambiguation rules:

- “lightweight/mobile/embedded/ONNX/NCNN” → NanoTrack unless the user names a
  different model explicitly;
- “LightTrack” or “Ocean” → reference-only response; no local build claim;
- “SiamFC++” + `pysot` → SiamFCpp-pysot; + `video_analyst` → the separate
  video-analyst snapshot;
- “SiamRPN” without qualifier → ask or state whether classic root, RPN-pysot,
  or SiamRPNpp is intended;
- “mask/segmentation” → SiamMask;
- “update/template learning” → UpdateNet layered over its DaSiamRPN base;
- “face Siamese” → SiamFace is a face-classification exclusion, not a tracker;
- “anchor-free” → SiamBAN/SiamCAR/Ocean may be semantically relevant, but only
  the first two have local implementation evidence here; Ocean is reference-only;
- “transformer” → TrTr, with explicit GPU/checkpoint/config gates.

If the user's wording spans incompatible variants, do not silently choose the
one with the easiest import. Return the candidate set and the missing decision.

## 6. Training and distributed-launch failures

### Symptoms

- shell launcher hard-codes two GPUs, a CUDA device list, or a master port;
- `torch.distributed.launch` is unavailable or deprecated;
- out-of-memory, deadlock, worker failure, or a dataloader returns no samples;
- resume checkpoint is incompatible with the chosen config;
- training script assumes a particular cropped-data layout.

### Response

- Convert the shell launcher into a reviewed plan: GPU count, process count,
  port, batch size, data root, config, checkpoint, log root, and stop condition.
- Verify a single-process bounded data/model smoke before distributed training.
- Check CUDA visibility and memory; a successful CUDA preparation probe is not a
  training result.
- Use an explicit modern launcher adaptation only if the user accepts the
  compatibility change and the selected code supports it.
- Do not claim training completion from a created log directory or checkpoint
  filename.

## 7. Test/evaluation failures

### Symptoms

- `my_test.py` runs but produces no result files;
- evaluation wildcard matches the wrong checkpoint family;
- result paths are confused with model paths;
- VOT toolkit build fails separately from tracker inference;
- metrics differ from README tables.

### Response

Separate these gates:

1. model load;
2. one-sequence inference;
3. result serialization;
4. protocol toolkit import/build;
5. dataset-wide evaluation;
6. metric comparison.

Report which gate failed. Keep `tracker_path`, `model_path`, `snapshot`, config,
result directory, and dataset root distinct. Inspect shell wildcard patterns
before running checkpoint loops. README metrics are historical claims and may
use different code, data, hardware, or protocol versions.

## 8. Deployment/demo failures

A `demo.py` accepting a video path proves only that a demo-shaped entry point is
present. It does not prove ONNX, NCNN, mobile, CPU, or real-time compatibility.
For NanoTrack, route conversion and deployment to the export sibling and verify
operator support, stateful template behavior, tensor names/shapes,
pre/postprocessing, numerical tolerance, and target-device latency. For other
snapshots, treat deployment as a custom adaptation unless a separate verified
artifact is supplied.

## 9. Safe stop report template

When a run cannot proceed, report:

```text
selected variant and evidence level:
requested operation:
source/config/model tuple:
last passed gate:
first failing gate:
observed error:
missing or conflicting prerequisite:
what was not attempted:
minimal next artifact or decision required:
```

This prevents a historical README, stale extension, partial dataset, or
successful environment probe from being misreported as a completed tracker
workflow.

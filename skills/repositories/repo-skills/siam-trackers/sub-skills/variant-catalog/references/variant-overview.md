# Variant overview

This is a distilled catalog, not a copy of the source tree. Relative names in
backticks are provenance labels from the inspected checkout; they are not
runtime paths. A future Researcher must use an authorized current checkout or
self-contained artifacts supplied for the task.

## Evidence vocabulary

| Label | Meaning | What it does not mean |
|---|---|---|
| **Complete maintained** | Source, configuration, metadata, and representative workflow families are present; NanoTrack is the collection's maintained path. | A full run is not proven without user data, model files, and a fresh compatible build. |
| **Substantive snapshot** | A local implementation root and representative Python/bin/toolkit/config evidence are present. | Current dependency compatibility, complete models, and end-to-end results are not guaranteed. |
| **Reference-only** | The collection contains a thin README/reference pointer but no local implementation root. | The referenced upstream project or its archive is not bundled or automatically available. |
| **Excluded** | The entry is not a visual-tracking variant for this catalog. | It should not be installed or routed as a tracker. |

The checkout contains no complete benchmark dataset/checkpoint set for the
collection as a whole. Some small model/result files exist in individual
snapshots, but their presence does not establish a complete or reproducible
benchmark package. No full tracking, training, evaluation, or export execution
is claimed.

## At-a-glance comparison

| Variant / snapshot | Local evidence | Core orientation | Typical request to route here | Build/dependency signal | Main gap or warning |
|---|---|---|---|---|---|
| **NanoTrack V1/V2/V3** | Complete maintained | Lightweight Siamese, BAN-style head, MobileNetV3; ONNX/NCNN-shaped deployment | Fast, small, CPU/mobile/embedded tracking; collection default | `NanoTrack/setup.py`; region extension; no pinned requirements file | Data/checkpoint selection and full benchmark still require user artifacts; deep details belong to siblings |
| **DaSiamRPN** | Substantive snapshot | Distractor-aware Siamese RPN | Named DaSiamRPN baseline or distractor-aware comparison | Region sources and a Python-37 prebuilt artifact; no local `setup.py` or requirements file found | Do not treat the prebuilt artifact or README model names as a runnable install |
| **LightTrack** | Reference-only | Lightweight one-shot architecture-search tracker | Literature/reference comparison only | No local implementation or package metadata | Not buildable from this collection |
| **Ocean** | Reference-only | Object-aware anchor-free tracker | Literature/reference comparison only | No local implementation or package metadata | Not buildable from this collection |
| **SiamBAN** | Substantive snapshot | Anchor-free box-adaptive Siamese tracker | Named BAN baseline; anchor-free box tracking | `SiamBAN/SiamBAN/setup.py`; region Cython; no requirements file found | Checkpoint/data/config must be supplied and paired |
| **SiamCAR** | Substantive snapshot | Siamese fully convolutional classification/regression | Named CAR baseline; anchor-free classification/regression | `SiamCAR/SiamCAR/requirement.txt`; region sources but no local `setup.py` found | Singular historical requirement file pins PyTorch 1.2.0; build recipe is incomplete |
| **SiamDW-FC** | Substantive snapshot | Deeper/wider fully-convolutional Siamese tracker | FC-style deeper/wider comparison | No local setup/region recipe; launcher expects numbered model files | Model/data and exact environment are unresolved |
| **SiamDW-RPN** | Substantive snapshot | Deeper/wider RPN tracker | RPN-style deeper/wider comparison | `requirement.txt`; no local setup/region recipe | Requirement names include legacy/misnamed packages; validate before install |
| **SiamFC** | Substantive snapshot | Classic fully-convolutional Siamese tracker | Small historical FC baseline or nine-dataset-shaped evaluation | No local setup/requirements file found; numbered model path in bin scripts | Dataset tree in checkout is not proof of complete benchmark data |
| **SiamFCpp-pysot** | Substantive snapshot | SiamFC++-style implementation adapted to pysot-shaped toolkit | Named SiamFC++ comparison using pysot-shaped workflow | `requirement.txt`; region Cython but no local `setup.py` found | Historical PyTorch 1.2.0 pin and sibling-like layout can be confused with SiamCAR |
| **SiamFCpp-video_analyst** | Substantive snapshot | SiamFC++ in a video-analyst-shaped framework | Request specifically naming video_analyst, its config system, or its SOT workflow | `requirements.txt`, `compile.sh`, nested VOT setup; pins Torch 1.4/Cython 0.27-era packages | Separate framework and config/model conventions; legacy pins are not blind install instructions |
| **SiamMask** | Substantive snapshot | Siamese tracking plus segmentation/masks | Mask output or mask benchmark request | `SiamMask/SiamMask-pysot/setup.py`; region Cython; no requirements file found | Mask data and mask-compatible config/checkpoint are mandatory |
| **SiamRPN** | Substantive snapshot | Classic Siamese region-proposal tracker | Named classic RPN baseline | `SiamRPN/SiamRPN/requirement.txt`; no local setup/region recipe | Distinguish this root from the separate pysot snapshot |
| **SiamRPN-pysot** | Substantive snapshot | Pysot-shaped RPN++/AlexNet snapshot | Request names pysot or this exact RPN tree | `SiamRPN/SiamRPN-pysot/setup.py`; region Cython | Config, snapshot, and toolkit must remain from this snapshot |
| **SiamRPNpp** | Substantive snapshot | SiamRPN++ with AlexNet and ResNet model roots | Deeper SiamRPN++ comparison or named root | `SiamRPNpp/SiamRPNpp/setup.py`; region Cython | Multiple model roots and historical checkpoint recipes make accidental mixing easy |
| **TrTr** | Substantive snapshot | Transformer tracking | Named TrTr or transformer-specific comparison | `TrTr/TrTr-pysot/setup.py`; region Cython; no requirements file found | Transformer/GPU resource and checkpoint/config pairing are unresolved |
| **UpdateNet** | Substantive snapshot / layered extension | Learned template update on a DaSiamRPN base | Model-update experiments or template-generation pipeline | Region sources and updater files; no local setup/requirements file found | Not a drop-in standalone tracker; multi-stage data/model pipeline required |
| **SiamFace** | Excluded | Siamese face classification demo | Face classification only, outside tracker selection | Three small Python files and an archive | Do not call it single-object tracking or include it in tracker comparisons |

The table is intentionally conservative: “substantive” describes local code
volume and workflow evidence, not a verified package release.

## Per-variant routing cards

### NanoTrack (collection default)

**Source/evidence:** root `README.md`, variant `NanoTrack/README.md`,
`NanoTrack/setup.py`, `NanoTrack/bin/`, `nanotrack/`, `models/`, `toolkit/`, and
`got10k/`. It has V1/V2/V3 model/config branches, train/test/eval-shaped
launchers, hyperparameter search, FLOPs/speed utilities, and PyTorch-to-ONNX
shaped tooling. The README describes an NCNN/mobile direction.

Route requests for a practical lightweight tracker here first. Verify the
variant branch (V1/V2/V3), config/checkpoint pairing, data format, and device
before using the detailed sibling skills. This catalog does not repeat the
NanoTrack API, evaluation protocol, or export procedure.

### DaSiamRPN

**Source/evidence:** root `DaSiamRPN/README.md`, variant
`DaSiamRPN/DaSiamRPN/README.md`, `dasiamrpn/`, `bin/`, and `toolkit/`. The
variant README exposes `my_test.py` and `my_eval.py` patterns plus named VOT/OTB
model artifacts. It has implementation and toolkit roots, but no local setup.py
or requirements file was found. Region Cython sources and a Python-37-named
shared object are present; the shared object is not a modern ABI proof.

Route only a named DaSiamRPN request. Treat it as a legacy snapshot requiring
an explicit environment/build plan and authorized model/data artifacts.

### LightTrack and Ocean

**Source/evidence:** `LightTrack/README.md` and `Ocean/README.md` each contain a
small reference-oriented README. No local source root, setup.py, requirements
file, bin workflow, or model/data package accompanies either entry. They are
reference-only in this collection. Do not offer a local build, training run,
benchmark run, or deployment command for either one.

### SiamBAN and SiamCAR

Both have substantive pysot-shaped snapshots with `bin/`, a tracker package,
models, results, toolkit, and root/variant README evidence. SiamBAN includes a
local setup.py for `toolkit.utils.region`; SiamCAR has `requirement.txt`, region
sources, and shell/Python train/test/eval/hyperparameter patterns but no local
setup.py found. SiamBAN's README is comparatively terse; do not infer missing
workflow details from SiamCAR or NanoTrack.

Route named BAN/CAR requests to the exact snapshot. Use BAN for a box-adaptive
anchor-free baseline and CAR for the fully-convolutional classification and
regression snapshot. Their historical VOT tables are claims from README
provenance, not newly verified results.

### SiamDW-FC and SiamDW-RPN

The two `SiamDW` directories are separate substantive snapshots. FC has a
`siamfc/` root and model-number test patterns; RPN has a `siamrpn/` root, a
requirement file, and model-number test/train/hyperparameter patterns. Neither
contains the common `toolkit/utils/region.pyx` setup family found in several
pysot snapshots. Do not silently graft a region build recipe from a sibling.

Route by the user's FC versus RPN wording. Both need a current source/config/
checkpoint/data inspection before launch.

### SiamFC

`SiamFC/SiamFC/` is a substantive classic FC snapshot with `siamfc/`, GOT-10k
and benchmark-shaped directories, model-number test/eval/train scripts, and
README claims of multiple dataset evaluation. No local setup.py or requirements
file was found. Treat the dataset directory names and result tables as
protocol clues, not proof that the data or model files are complete.

### SiamFCpp: pysot and video_analyst

These are two different substantive snapshots and must not be merged:

- `SiamFCpp/SiamFCpp-pysot/` resembles the SiamCAR/pysot family, has a
  `requirement.txt`, region sources, config/model roots, and Python/shell train,
  test, eval, and HPO patterns. It has no local setup.py found.
- `SiamFCpp/SiamFCpp-video_analyst/` is a larger framework-shaped tree with
  `requirements.txt`, `compile.sh`, `siamfcpp/` config/engine/pipeline/model
  roots, shell test recipes, and a nested VOT benchmark setup. Its requirements
  explicitly record Torch 1.4.0, torchvision 0.5.0, NumPy 1.16.0, Cython
  0.27.3, and other old pins.

Use the user's `pysot` or `video_analyst` qualifier as the primary selector.
The latter's framework and nested evaluation extension are distinct build
surfaces.

### SiamMask

`SiamMask/SiamMask-pysot/` is a substantive mask-capable snapshot with a local
setup.py, Cython region toolkit, mask model/config roots, mask-aware train/test/
eval/demo files, and README dataset requirements including mask datasets. Route
segmentation or mask-output requests here, not to SiamRPNpp merely because the
package layout is similar. A box-only request may still prefer NanoTrack or a
box tracker unless the user specifically needs SiamMask.

### SiamRPN, SiamRPN-pysot, and SiamRPNpp

There are three distinct routes:

- `SiamRPN/SiamRPN/`: classic root with `siamrpn/`, a singular requirement file,
  model-number scripts, and no local setup.py/region source family.
- `SiamRPN/SiamRPN-pysot/`: pysot-shaped root whose package is named
  `siamrpnpp`, with setup.py, region Cython, AlexNet config/model roots, and
  standard train/test/eval/demo files.
- `SiamRPNpp/SiamRPNpp/`: separate SiamRPN++ snapshot with setup.py, region
  Cython, both AlexNet and ResNet model roots, and train/test/eval/HPO files.

Preserve the exact source root, configuration, checkpoint naming convention,
and toolkit together. “RPN” alone is ambiguous; ask for or infer the desired
classic, pysot, or RPN++ route from the request, then state the choice.

### TrTr

`TrTr/TrTr-pysot/` is a substantive transformer-shaped snapshot with a `trtr/`
package, config/model roots, setup.py, Cython region toolkit, and train/test/
eval/HPO/tuning patterns. Its README records encoder/decoder layer variants,
but that is not a verified quality or resource guarantee. Route named TrTr or
transformer requests here only after confirming GPU memory, model/checkpoint,
config, and legacy dependency compatibility.

### UpdateNet

`UpdateNet/UpdateNet-DaSiamRPN/` contains a DaSiamRPN base, an `updatenet/`
package, region sources, updater training/data code, and test/eval patterns. Its
README documents template creation and staged updater training (1.1 through
3.2), plus a known geometry workaround. It is a layered experiment, not a
standalone replacement for a tracker. Route model-update/template-learning
requests here and require a compatible base tracker, template data, updater
checkpoint, and evaluation data.

### SiamFace exclusion

`SiamFace/README.md` labels the entry “Siamese network for face
classification”; its train/test files operate on that demo. It is explicitly
excluded from the visual-tracker catalog. A face-recognition request must use a
different skill or task scope rather than being mapped to SiamFC.

## How to report a selection

Return a compact record with:

1. selected variant and exact evidence level;
2. reason it matches the natural request;
3. source root and available metadata (setup/requirements/region/build);
4. required data, checkpoint, config, and backend;
5. next sibling skill for detailed work, if applicable;
6. missing evidence and a stop condition.

Example: “Select `SiamFCpp-video_analyst` (substantive snapshot), not
`SiamFCpp-pysot`, because the request names the video-analyst framework. The
snapshot has a framework requirements file, compile-shaped VOT step, and
model-path/config launchers, but no supplied benchmark bundle; validate an
isolated legacy-compatible environment and obtain matching model/data artifacts
before testing.”

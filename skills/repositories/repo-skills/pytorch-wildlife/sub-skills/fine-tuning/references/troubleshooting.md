# Fine-tuning troubleshooting

Classify the failure before changing code. These companions are legacy and
may not match the installed PytorchWildlife 1.3.0 environment.

| Symptom | Likely cause | Safe action |
|---|---|---|
| CSV header error or missing image | Wrong root, relative `path`, or unsupported file | Print the resolved root, check one row manually, and run the safe splitter on a copy. Do not rewrite paths in place. |
| Class id/name mismatch | Duplicate label spelling, sparse ids, or changed class order | Produce an explicit id-to-name map; align `num_classes`/YAML `names` before training. |
| Random split looks unusually strong | Camera burst or same scene appears in multiple partitions | Re-split by `Location` or 30-second `Photo_Time` sequence and inspect group intersections. |
| Location split fails | `Location` missing, too few groups, or positional size confusion | Add/validate the exact column, check group counts, and pass `val_size`/`test_size` by keyword in adapted code. |
| Sequence split fails | Timestamp spelling/format, timezone, or too few 30-second bins | Normalize to `Photo_Time`, parse timestamps, document timezone, and inspect bins before rerunning. |
| Detection labels are ignored | Labels are not under the matching split/stem or YAML points at labels | Rebuild the parallel `images/<split>` and `labels/<split>` check; verify one image/label pair. |
| “Expected 5 values” or invalid boxes | Pixel coordinates, `xyxy`, commas, or malformed lines | Convert explicitly to normalized `class x_center y_center width height`; never silently clip. |
| Dataset YAML cannot find images | Relative `path` is resolved from an unexpected working directory | Use a copied YAML with an explicit root, resolve every split, and review any launcher rewrite. |
| Unsupported model error | Wrong capitalization or model identifier | Use exactly `YOLO`/`RTDETR` and one of the five documented `MDV6-*` names. |
| Validation says `plots` is missing | YAML uses documented `plot`, source branch reads `plots` | Reconcile the versioned launcher/config in a copy; do not add unrelated keys. |
| `CUDA`/device error | Device id unavailable, CPU run with GPU-only trainer setting, or memory pressure | Run syntax/data checks on CPU, verify `torch.cuda.is_available()`, reduce workers/batch for an approved smoke load, and record any compatibility edit. |
| Classification launcher help/import fails | Eager package imports or old companion dependencies | Capture the first traceback and verify the companion dependency set separately; do not claim the CLI is usable from a partial import. |
| Legacy `yolov5` import breaks in a modern environment | Old dependency/API assumptions conflict with current Python/Torch packages | Use an isolated, maintained compatible environment or a reviewed compatibility layer; keep private shim mechanics out of the runtime skill and do not mix arbitrary package versions. |
| Pretrained constructor starts network traffic | ResNet/MegaDetector weights are not cached | Stop the run. Obtain explicit approval and a local, provenance-checked weight, or limit the check to parsing/signatures. |
| Lightning/Ultralytics option is ignored | Companion launcher forwards only some YAML fields | Inspect the actual call arguments, record the ignored field, and do not infer behavior from its presence in YAML. |
| Comet/W&B authentication error | Credential-bound logger selected | Switch to local CSV/TensorBoard for a safe run; never place tokens in config or generated files. |
| Output already exists or is scattered | Relative log/weights/run roots and experiment collisions | Use a new copied output root, list expected paths before running, and preserve config/checkpoint pairing. |
| Core wrapper rejects checkpoint | Companion checkpoint format/class head differs from core | Keep the weight in the companion workflow, compare loader/model/class mapping contracts, and route inference to the core sub-skill only after a real compatibility check. |

## Environment boundaries

The classification companion's old Python/Torch/Lightning pins and the
current core package's Python >=3.10 requirement are not a single guaranteed
environment. The detection companion has its own Ultralytics and Torch
expectations. Prefer isolated environments and record exact versions. The
root package imports many model families eagerly, so a failure in an optional
or legacy dependency can prevent an apparently unrelated import; diagnose the
first failing import rather than repeatedly retrying training.

For the legacy yolov5 compatibility problem, the actionable boundary is to
use a modern environment known to support the installed package or a reviewed,
version-controlled compatibility adaptation. Do not expose private paths,
local monkey-patches, or undocumented shims as user instructions.

## Stop conditions

Stop and ask for a decision when a fix would download weights, install a
broad legacy stack, launch a long run, upload logs, overwrite annotations,
or change class semantics. A parser/tiny-fixture failure is enough to block a
safe handoff; do not label it verified merely because the source command is
known.

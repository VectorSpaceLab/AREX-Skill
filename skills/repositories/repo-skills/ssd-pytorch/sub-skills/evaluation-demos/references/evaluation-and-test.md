# VOC evaluation and test-output planning

This reference covers the repository's two VOC-facing evaluation entry points:

- `eval.py`: runs SSD300 VOC2007 test-set detection, writes VOC-style per-class
  detection result files, pickles detections/PR curves, and prints AP plus mean
  AP summaries.
- `test.py`: runs over VOC2007 test images and appends human-readable ground
  truth plus prediction blocks to a text file, primarily for inspection rather
  than official mAP reporting.

Do not treat either entry point as self-contained: both require repository code,
compatible weights, and VOC data. Modern PyTorch may also require a compatibility
patch for the legacy `Detect(Function)` forward path; route that patching to the
model-inference sub-skill.

## Hard requirements

For full evaluation or test-output generation, verify all of the following before
running the repository scripts:

1. **VOC2007 test data** rooted at the VOCdevkit directory:
   - `VOC2007/Annotations/*.xml`
   - `VOC2007/JPEGImages/*.jpg`
   - `VOC2007/ImageSets/Main/test.txt`
2. **Compatible SSD300 VOC weights**:
   - `eval.py` defaults to a VOC0712 SSD300 mAP-style weight name.
   - `test.py` defaults to an older VOC0712 SSD300 weight name.
   - A state_dict with incompatible layer names, class count, or model size will
     fail before any metric can be trusted.
3. **Runtime dependencies**: PyTorch, NumPy, OpenCV Python bindings, PIL for
   `test.py`, and repository imports.
4. **Device consistency**: choose CPU or CUDA deliberately. The legacy scripts
   set default tensor types and may produce CPU/CUDA mismatch errors if the
   model, priors, input tensors, and loaded weights are not on the same device.

Use a VOC root that names the VOCdevkit directory. In unmodified `eval.py`, the
`VOC2007` devkit path is built by string concatenation, so a trailing separator
on the VOC root is safest when writing command templates.

## CLI surfaces

### `eval.py` flags

The evaluation parser exposes:

| Flag | Default intent | Planning note |
| --- | --- | --- |
| `--trained_model` | VOC0712 SSD300 mAP-style `.pth` | Must exist and match `build_ssd('test', 300, 21)`. |
| `--save_folder` | `eval/` | The folder is created if absent; primary VOC result files are written elsewhere. |
| `--confidence_threshold` | `0.01` | Low threshold is appropriate for mAP-style recall. In this codebase, effective thresholding may also be fixed inside the model's Detect layer. |
| `--top_k` | `5` | Parser passes it into `test_net`; the Detect layer also has its own top-k behavior. Avoid small values when recall matters. |
| `--cuda` | `True` | Uses a robust string-to-bool parser: values like `true`, `false`, `1`, `0` are accepted. |
| `--voc_root` | repository config default | Must contain `VOC2007` test data. |
| `--cleanup` | `True` | Parser exposes it, but the observed source does not remove result files; do not rely on automatic cleanup. |

### `test.py` flags

The test-output parser exposes:

| Flag | Default intent | Planning note |
| --- | --- | --- |
| `--trained_model` | older VOC0712 SSD300 `.pth` | Must match the model architecture and VOC class count. |
| `--save_folder` | `eval/` | Source forms output as `save_folder + 'test1.txt'`; use a trailing separator. |
| `--visual_threshold` | `0.6` | Parser exposes it, but the observed loop uses a hardcoded `0.6` comparison. Treat the flag as potentially ineffective unless patched. |
| `--cuda` | `True` | Source uses `argparse type=bool`; strings such as `False` may parse truthy. CPU-safe use may require a small parser patch or wrapper. |
| `--voc_root` | repository config default | Must contain VOC2007 test data. |
| `-f` | none | Dummy Jupyter argument accepted by the parser. |

## Command templates

Use the bundled planner instead of hand-assembling commands when possible:

```bash
python scripts/plan_evaluation_command.py \
  --mode eval \
  --trained-model weights/ssd300_mAP_77.43_v2.pth \
  --voc-root '<VOCDEVKIT_ROOT>/' \
  --save-folder eval/ \
  --cuda false \
  --confidence-threshold 0.01 \
  --top-k 5 \
  --cleanup true
```

```bash
python scripts/plan_evaluation_command.py \
  --mode test \
  --trained-model weights/ssd_300_VOC0712.pth \
  --voc-root '<VOCDEVKIT_ROOT>/' \
  --save-folder eval/ \
  --cuda false \
  --visual-threshold 0.6
```

The planner prints a command template and warnings; it never runs `eval.py` or
`test.py`.

If writing commands manually, keep paths shell-quoted and prefer explicit values:

```bash
python eval.py \
  --trained_model weights/ssd300_mAP_77.43_v2.pth \
  --voc_root '<VOCDEVKIT_ROOT>/' \
  --save_folder eval/ \
  --cuda false \
  --confidence_threshold 0.01 \
  --top_k 5 \
  --cleanup true
```

```bash
python test.py \
  --trained_model weights/ssd_300_VOC0712.pth \
  --voc_root '<VOCDEVKIT_ROOT>/' \
  --save_folder eval/ \
  --visual_threshold 0.6 \
  --cuda false
```

For unmodified `test.py`, treat the CPU command as a template only: the legacy
boolean parser may still interpret `--cuda false` as true.

## `eval.py` outputs

When a full eval run succeeds, expect these artifacts and console messages:

- Per-image detection timing lines such as `im_detect: i/N ...s`.
- Pickled all-box detections at `ssd300_120000/test/detections.pkl`.
- VOC result text files under the VOC2007 devkit result folder:
  `VOC2007/results/det_test_<class>.txt`.
- Per-class precision/recall pickles under `ssd300_120000/test/`, one
  `<class>_pr.pkl` file per VOC class.
- Console AP lines: `AP for <class> = ...`.
- Console mean AP: `Mean AP = ...`.
- A note that the metrics are computed with unofficial Python eval code and
  should be close to the official MATLAB code.

The `--save_folder` argument is created by the parser setup, but observed
metric artifacts are driven by the hardcoded `ssd300_120000/test` output dir and
VOCdevkit `results` folder. Check both locations before deciding that an eval
produced no files.

## VOC result file schema

Each VOC detection result file is class-specific and contains one line per kept
detection:

```text
<image_id> <confidence> <xmin> <ymin> <xmax> <ymax>
```

Important details:

- File name pattern: `det_test_<class>.txt` for VOC2007 test.
- `image_id` is the VOC image id without the `.jpg` suffix.
- Confidence is formatted to three decimal places by the source writer.
- Coordinates are written in VOC one-based convention after converting from
  internal zero-based boxes.
- Missing or empty class files lead to AP `-1` or metric failures depending on
  where the run stopped.

## AP metric notes

- The evaluator uses VOC2007's 11-point AP metric by default.
- IoU overlap threshold is `0.5`.
- `difficult` objects are ignored for true-positive counting.
- Mean AP is the arithmetic mean over the 20 VOC classes.
- README performance values are reference points, not guarantees. Reproducing
  them depends on the exact weights, data split, model compatibility, CUDA/CPU
  numerical behavior, and dependency versions.

## `test.py` output format

`test.py` writes or appends to `test1.txt` inside the chosen save folder. The
file is inspection-oriented, not VOC metric input. It contains repeated blocks:

```text
GROUND TRUTH FOR: <image_id>
label: <xmin> || <ymin> || <xmax> || <ymax> || <class_index>
PREDICTIONS:
1 label: <class_name> score: <score> <xmin> || <ymin> || <xmax> || <ymax>
```

Planning implications:

- Delete or rotate an old `test1.txt` before a new run if appending is not
  desired.
- Use a trailing separator in `--save_folder`; otherwise legacy string
  concatenation can create a path like `evaltest1.txt`.
- Treat the output as a qualitative sanity check of labels and boxes, not a
  replacement for VOC AP evaluation.

## Threshold and top-k decisions

- **mAP evaluation**: prefer a low confidence threshold such as `0.01` so recall
  is not artificially clipped before AP computation. Avoid overly small top-k
  settings when measuring recall.
- **Text/visual inspection**: `0.6` is the repository's common threshold for
  readable outputs. Raising it reduces clutter; lowering it helps diagnose low
  confidence detections.
- **Legacy caveat**: some threshold/top-k parser arguments are not fully wired
  through in the observed scripts because Detect-layer defaults and hardcoded
  loops also control filtering. If exact threshold behavior is required, route
  code patching and validation to the model-inference sub-skill.

## Safe pre-run checklist

Before running a full eval/test:

1. Confirm VOC2007 test data exists and the VOC root is the VOCdevkit directory.
2. Confirm the weight file exists and is for SSD300 VOC with 21 classes.
3. Decide CPU vs CUDA; if CUDA is required, verify `torch.cuda.is_available()`.
4. Confirm modern PyTorch Detect compatibility through the model-inference
   route if the environment is newer than the original codebase.
5. Choose output folder and clean stale text or result files if needed.
6. Run a command template review with `scripts/plan_evaluation_command.py`.

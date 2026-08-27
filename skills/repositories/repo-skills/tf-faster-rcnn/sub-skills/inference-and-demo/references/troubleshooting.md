# Troubleshooting

## Missing checkpoint `.meta`

**Symptom**

`tools/demo.py` raises an error like:
`<prefix>.meta not found`

**What it means**

The checkpoint prefix does not match the selected backbone/dataset pair, or the pretrained model files were not placed under the expected `output/<net>/<train_imdb>/default/` subtree.

**What to check**

- `--net` is `vgg16` or `res101`.
- `--dataset` is `pascal_voc` or `pascal_voc_0712`.
- The checkpoint family matches the net:
  - `vgg16_faster_rcnn_iter_70000.ckpt`
  - `res101_faster_rcnn_iter_110000.ckpt`
- The checkpoint prefix has the TensorFlow file set beside it, not just the `.meta` file.

Route folder-layout fixes to `../dataset-and-assets/SKILL.md`.

## `nms.gpu_nms` import failure even with `USE_GPU_NMS=False`

**Symptom**

`ImportError` or `ModuleNotFoundError` for `nms.gpu_nms` during import.

**Why it happens**

`nms_wrapper.py` imports `nms.gpu_nms` unconditionally.
`USE_GPU_NMS=False` only changes dispatch after the import succeeds.

**Fix**

Treat it as an installation/build issue and route to `../installation-and-configuration/SKILL.md`.

## OpenCV image read failure

**Symptom**

`cv2.imread(...)` returns `None`, followed by a later `TypeError`, `AttributeError`, or `cv2.error` during resizing.

**Why it happens**

The demo script does not validate the return value from `cv2.imread`.
A missing, unreadable, or replaced file in `data/demo/` will fail later in the pipeline.

**Fix**

- Confirm the sample JPEG exists.
- Confirm the current working directory is the repo root when running the demo command.
- If you copied the script for custom images, make sure the file paths point to real RGB/BGR image files.

## ResNet101 memory pressure

**Symptom**

CUDA OOM, `ResourceExhaustedError`, or a very slow demo on a small GPU.

**Why it happens**

The demo enables `allow_growth`, but ResNet101 inference still needs several gigabytes of memory for the default test scale.

**Fix**

- Try `--net vgg16` first.
- Use a larger GPU if you need ResNet101.
- For debugging only, use a CPU-oriented environment, but remember the `nms.gpu_nms` import caveat above.

## Headless visualization

**Symptom**

The command runs but the shell appears to hang, or matplotlib errors because there is no display.

**Why it happens**

`tools/demo.py` ends with `plt.show()`.

**Fix**

- Run with X forwarding or another display backend.
- Set a noninteractive matplotlib backend in a local copy of the script.
- Save figures instead of showing them if you only need artifacts.

## Wrong class labels or label count

**Symptom**

The demo shows the wrong class names or you expected COCO-style labels.

**Why it happens**

`tools/demo.py` is hardwired to the Pascal VOC 20-class label list.
The dataset selector changes the checkpoint folder, not the label set.

**Fix**

Use the stock demo only for VOC-style checkpoints, or move to a different workflow and sub-skill if you need a different label space.

## Command-builder output looks fine but runtime still fails

The bundled helper only checks the expected repo layout and checkpoint files.
It does not import TensorFlow, build native extensions, or execute inference.
If the printed command looks correct but the runtime still fails, check the NMS installation and image files next.

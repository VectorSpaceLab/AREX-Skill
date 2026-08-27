# Cross-cutting troubleshooting

## `ModuleNotFoundError: facenet`, `align`, `models`, or `compare`

Cause: Facenet is not an installed distribution with console scripts. Its modules live in a source-style tree.

Fix:

1. Verify that the environment can import `facenet`, `lfw`, `align.detect_face`, and `models.inception_resnet_v1`.
2. Add the Facenet source module directory to the environment's module search path or install the source tree with an equivalent mechanism.
3. For contributed helpers that import `face` or other peer files, make the contributed module directory importable too.

## TensorFlow 2.x or missing `tf.contrib`

Cause: Facenet model definitions and training scripts use TF1 sessions, queues, savers, and `tensorflow.contrib.slim`.

Fix: use a TensorFlow 1.x environment. A task to port Facenet to TF2 is a code migration task, not ordinary Facenet usage.

## Protobuf descriptor error during TensorFlow import

Symptom: `TypeError: Descriptors cannot not be created directly`.

Fix: use a protobuf version compatible with TensorFlow 1.x, commonly `protobuf<3.20`, then rerun the import smoke check.

## Deprecated SciPy image functions

Symptom: `AttributeError: module 'scipy.misc' has no attribute 'imread'` or `imresize`.

Cause: scripts were written for older SciPy versions.

Fix options:

- Use an environment with older SciPy image helpers for faithful execution.
- Patch the script to read/resize/save with Pillow or OpenCV when modernizing.
- Prefer bundled validators and command builders in this skill when only planning or checking commands.

## Pretrained model or dataset download failures

Many original tests and examples call Google Drive or public dataset URLs for pretrained models and LFW subsets. Treat these as network-dependent. Do not run them by default in automated verification. Ask the user to provide model and dataset paths when reproducible execution matters.

## Model path confusion

Facenet accepts either:

- a checkpoint directory containing one `.meta` file and matching checkpoint state/files; or
- a frozen `.pb` graph.

Read [`../sub-skills/model-export-and-checkpoints/references/model-files.md`](../sub-skills/model-export-and-checkpoints/references/model-files.md) before debugging model loading.

## Fixed image standardization mismatch

The README notes that newer pretrained models, including 2018 VGGFace2/CASIA models, require fixed image standardization for comparable results. If LFW accuracy or embedding distances look wrong, check whether the workflow needs a `--use_fixed_image_standardization` flag or matching preprocessing.

## Long or unsafe workflows

- Full softmax/triplet training is expensive and writes logs/checkpoints.
- LFW evaluation requires aligned LFW images, a pairs file, and a model.
- Webcam recognition opens a camera/display and may run forever.

Bound these workflows, use temporary output directories, and get user approval before running long, networked, or hardware-interactive commands.

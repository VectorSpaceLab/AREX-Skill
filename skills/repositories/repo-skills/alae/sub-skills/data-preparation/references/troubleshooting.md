# Data-Preparation Troubleshooting

## Fast triage

1. Run `python scripts/validate_alae_data_layout.py --help` to confirm the bundled validator is reachable.
2. Validate the user's config with `--repo-root <ALAE repository root>` so relative `dataset_samples`, `style_mixing`, and `OUTPUT_DIR` paths resolve as the source scripts expect.
3. If the failure comes from an original dataset script, confirm the command is run from the ALAE repository root with `PYTHONPATH` pointing to that root.
4. For face alignment, run `scripts/align_faces_alae.py --dry-run` before writing aligned images.

## Symptoms, likely causes, and recovery

| Symptom/error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'defaults'`, `net`, or another root module when running a dataset script from `dataset_preparation/` | The source script imports repository-root modules but the checkout root is not on `PYTHONPATH`. | Run from the ALAE repository root and prefix the command with `PYTHONPATH="$PWD"`, or otherwise add the checkout root to `PYTHONPATH`. Do not use a hard-coded production checkout path. |
| `AttributeError: module 'tensorflow' has no attribute 'python_io'` or missing `tf.Session` | TensorFlow 2.x or an environment without TF1 compatibility is being used. | Use a legacy TensorFlow 1.x-capable environment for original dataset scripts, or patch the source workflow to use `tf.compat.v1` with eager execution disabled. Keep this separate from modern Python environments when dependency conflicts appear. |
| `ImportError` for `dareblopy`, `dlutils`, `torch`, `torchvision`, or `yacs` | The repo's script dependencies are incomplete. | Install the minimal dependencies for the workflow. Data conversion needs TensorFlow 1.x plus PyTorch utilities for downsampling; MNIST/SVHN additionally trigger downloader/torchvision code. |
| `shape_predictor_68_face_landmarks.dat` not found, dlib `RuntimeError`, or `ImportError: No module named dlib` | Face alignment optional dependency or landmark model is missing. | Obtain the dlib 68-landmark predictor locally, install dlib, then pass `--predictor <path>` to `scripts/align_faces_alae.py`. Use `--dry-run` to verify inputs without importing dlib. |
| Validator reports malformed `DATASET.PATH` or `PATH_TEST` | The pattern does not accept `(lod, part_index)` old-style formatting. | Use a pattern such as `.../dataset-r%02d.tfrecords.%03d`. Quote it in shell commands so `%` placeholders survive. |
| Training loader assertion involving part count and world size | `DATASET.PART_COUNT` is not divisible by the number of training processes/GPUs. | Adjust `PART_COUNT`, regenerate/split shards, or train with a compatible world size. Run the validator with `--world-size <n>` before launching training. |
| Missing files under `/data/datasets/...` | Source configs and scripts assume a host-specific data prefix. | Override `DATASET.PATH`, `PATH_TEST`, `FFHQ_SOURCE`, or raw-data paths where the script allows it, or create a deliberate `/data/datasets` symlink to the real data. Do not rely on this skill's construction checkout. |
| Permission denied or no space left while creating TFRecords | Multi-resolution TFRecord conversion writes many large files. | Check writable parent directories and free space before running. Start with a small approved fixture or a single-part custom config when possible. |
| `prepare_mnist_tfrecords.py` or `prepare_svhn_tfrecords.py` unexpectedly downloads data | The source script downloads MNIST/SVHN by design. | Get explicit network approval, pre-populate the downloader cache, or avoid the source script and prepare equivalent TFRecords offline. |
| `prepare_celeba.py` downloads at import time or fails on `scipy.misc` APIs | This is a legacy pickle script, not the current TFRecord pipeline. | Do not use it for current training. Prefer `prepare_celeba_tfrecords.py` with prepared raw CelebA files, or document why the legacy pickle workflow is intentionally excluded. |
| `prepare_imagenet.py` only creates samples and then exits | The source script has an early `exit()` before the full conversion branch and default `configs/imagenet.yaml` is absent in this checkout. | Treat it as reference-only unless a maintainer intentionally edits it and supplies a valid ImageNet config/raw-data tree. |
| Style mixing fails on missing `src/0.png`, `dst/0.png`, or an image-size assertion | `DATASET.STYLE_MIX_PATH` lacks the expected `src/`/`dst/` files or images are smaller than the model resolution. | Create `src/0..4` and `dst/0..5` as `.png` or `.jpg` under the configured style path. Use images at least as large as `2 ** (MODEL.LAYER_COUNT + 1)`. Run the validator to count and check expected files. |
| Reconstruction/preview scripts fail on missing sample images | `DATASET.SAMPLES_PATH` is absent, empty, or points to the wrong resolution. | Align/copy sample images into the configured directory, or set `DATASET.SAMPLES_PATH` deliberately for the workflow. For training-only debug runs, `no_path` disables sample previews. |
| `OUTPUT_DIR` missing warnings from the validator | Checkpoints or logs have not been created/downloaded yet. | For pure data prep this can be a warning. For generation/training continuation, route to the training or generation sub-skill to check `last_checkpoint` and artifact readiness. |

## Network and destructive-side-effect guardrails

- Original dataset scripts can download data, scan huge raw datasets, and overwrite TFRecord outputs. Do not run them as a casual verification step.
- The bundled validator is read-only. It reports missing files and layout issues without creating directories.
- The bundled face aligner writes only when the user supplies explicit paths and omits `--dry-run`.
- Avoid running metric or full training scripts to validate data layout; use the validator first and route to the owning sub-skill only after the data contract is clear.

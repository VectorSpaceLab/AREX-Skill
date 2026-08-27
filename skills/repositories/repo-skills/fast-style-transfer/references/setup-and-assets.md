# Setup and Assets

## Purpose

Read this when preparing a Fast Style Transfer runtime before training, image stylization, or video stylization. The repository is not packaged as a normal Python distribution; it is a set of TensorFlow scripts plus external data/model assets.

## Dependency surfaces

The public scripts import these packages:

| Surface | Required packages/tools | Notes |
| --- | --- | --- |
| Training with the bundled training runtime | TensorFlow, numpy, scipy, imageio, Pillow, VGG `.mat`, training images | GPU strongly recommended for full training. |
| Image stylization with the bundled image stylization runtime | TensorFlow, numpy, scipy, imageio, Pillow, trained checkpoint | CPU can run small cases but is slower. |
| Video stylization with the bundled video stylization runtime | Image stylization dependencies, moviepy, ffmpeg or imageio-ffmpeg, trained checkpoint | CPU video processing is usually very slow. |

Public documentation mentions older dependencies such as TensorFlow 0.11/Python 2.7 and also a later Conda example with `tensorflow-gpu=2.1.0`. Modern environments may need small compatibility fixes or a newer TensorFlow that still supports `tf.compat.v1` APIs used by the scripts. Always verify imports and CLI help in the target environment.

## External assets

This skill does not bundle any of these files:

| Asset | Used by | Expected shape/location |
| --- | --- | --- |
| VGG19 `.mat` file | Training style/content losses through the bundled VGG module | Pass with `--vgg-path`; documented default is `data/imagenet-vgg-verydeep-19.mat`. |
| Training content image corpus | `run_training.py --train-path` | Directory containing image files; README uses COCO `train2014`. |
| Style image | `run_training.py --style` | Any readable RGB or grayscale image. Grayscale images are stacked to RGB by the bundled image utility. |
| Trained checkpoint | the bundled image and video stylization runtimes | Checkpoint directory with TensorFlow checkpoint state or an exact checkpoint file/prefix accepted by TensorFlow Saver. |
| Video input | `run_video_stylization.py --in-path` | Moviepy-readable video file. |

The source setup script creates a `data/` directory, downloads the VGG19 `.mat`, downloads COCO `train2014.zip`, and unzips it. Treat that script as reference-only: it performs network downloads and creates large local data. Run equivalent commands only after the user authorizes network/disk use.

## Safe preflight sequence

1. Confirm Python dependencies:

   ```bash
   python - <<'PY'
   import tensorflow as tf, numpy, scipy, imageio, PIL
   print(tf.__version__)
   print(tf.config.list_physical_devices('GPU'))
   PY
   ```

2. Confirm bundled runtime parser imports from the skill root:

   ```bash
   python sub-skills/training/scripts/run_training.py --help
   python sub-skills/image-stylization/scripts/run_image_stylization.py --help
   python sub-skills/video-stylization/scripts/run_video_stylization.py --help
   ```

3. Validate workflow-specific inputs with bundled helpers before running expensive commands:

   ```bash
   python sub-skills/training/scripts/validate_training_inputs.py --checkpoint-dir checkpoints --style style.jpg --train-path train2014 --vgg-path imagenet-vgg-verydeep-19.mat
   python sub-skills/image-stylization/scripts/validate_image_stylization_inputs.py --checkpoint ckpt-dir --in-path input.jpg --out-path out.jpg
   python sub-skills/video-stylization/scripts/validate_video_stylization_inputs.py --checkpoint ckpt-dir --in-path input.mp4 --out-path out.mp4 --check-dependencies
   ```

4. Only after preflight passes, run the skill-owned runtime wrappers with user-supplied assets and a compatible TensorFlow environment.

## Backend choice

- CPU is enough for parser checks, image IO checks, graph-building checks, and very small debugging runs.
- GPU is recommended for full training and high-throughput image/video stylization. Validate that TensorFlow sees a GPU before advertising GPU runtime coverage.
- The repository's default device strings use TensorFlow syntax such as `/gpu:0` and `/cpu:0`.

## Checkpoint handoff

Training saves checkpoints through `tf.compat.v1.train.Saver()` to a path ending in `fns.ckpt` under the chosen checkpoint directory. Image and video stylization consume either a checkpoint directory with TensorFlow checkpoint state or a checkpoint path/prefix that Saver can restore.

If checkpoint restore fails, first confirm that the checkpoint was produced by a compatible graph and TensorFlow version. A parser/input validation pass cannot prove checkpoint compatibility.

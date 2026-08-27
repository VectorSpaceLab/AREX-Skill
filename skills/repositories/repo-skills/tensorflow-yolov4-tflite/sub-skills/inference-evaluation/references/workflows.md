# Inference, Evaluation, and Benchmark Workflows

Commands assume a target checkout root as the current working directory.

## Image detection

Use `detect.py` for a single image. TensorFlow SavedModel example:

```bash
python detect.py \
  --weights ./checkpoints/yolov4-416 \
  --size 416 \
  --model yolov4 \
  --image ./data/kite.jpg \
  --output result.png \
  --framework tf
```

Tiny variant:

```bash
python detect.py \
  --weights ./checkpoints/yolov4-tiny-416 \
  --size 416 \
  --model yolov4 \
  --tiny \
  --image ./data/kite.jpg \
  --output result-tiny.png
```

Important behavior:

- The script loads `tf.saved_model.load(..., tags=[SERVING])` unless
  `--framework tflite` is used.
- It resizes images directly with OpenCV to `--size` and divides by 255.
- It applies `tf.image.combined_non_max_suppression` using `--iou` and `--score`.
- It shows the PIL image and writes the OpenCV BGR result to `--output`.

## TFLite inference

Use `detect.py --framework tflite` with a `.tflite` file:

```bash
python detect.py \
  --weights ./checkpoints/yolov4-416.tflite \
  --size 416 \
  --model yolov4 \
  --image ./data/kite.jpg \
  --output result-tflite.png \
  --framework tflite
```

TFLite output order is model-specific in the source code. `detect.py` reverses
bbox/prob tensors for `--model yolov3 --tiny`; otherwise it uses output 0 as
boxes and output 1 as scores. `evaluate.py` has a different tiny-condition
branch, so validate a known image before trusting mAP results for tiny TFLite
models.

## Video detection

Use `detectvideo.py` for webcam/video-file style processing:

```bash
python detectvideo.py \
  --weights ./checkpoints/yolov4-416 \
  --size 416 \
  --model yolov4 \
  --video ./data/road.mp4 \
  --output road-detections.avi \
  --output_format XVID \
  --dis_cv2_window
```

Notes:

- `--output` is optional. Without it, no video file is written.
- `--dis_cv2_window` disables OpenCV windows and is important for notebooks,
  servers, or headless containers.
- The script raises `ValueError: No image! Try with another video format` when
  frames cannot be decoded before the reported frame count is exhausted.

## mAP evaluation

`evaluate.py` creates detection text files for the mAP tool, then `mAP/main.py`
computes metrics.

README-style sequence:

```bash
python evaluate.py \
  --weights ./checkpoints/yolov4-416 \
  --framework tf \
  --model yolov4 \
  --size 416

cd mAP/extra
python remove_space.py
cd ..
python main.py --output results_yolov4_tf
```

Important side effects and traps:

- `evaluate.py` removes and recreates `./mAP/predicted`, `./mAP/ground-truth`,
  and `cfg.TEST.DECTECTED_IMAGE_PATH` before writing outputs.
- It computes `num_lines` from `FLAGS.annotation_path`, but iterates over
  `cfg.TEST.ANNOT_PATH`. If the user passes a non-default `--annotation_path`,
  update `core.config.cfg.TEST.ANNOT_PATH` or patch the target checkout so the
  same file is used consistently.
- Annotation lines must follow the converted format documented by the
  training-data sub-skill: `image_path xmin,ymin,xmax,ymax,class ...`.

## FPS benchmarking

Use `benchmarks.py` for speed checks:

```bash
python benchmarks.py \
  --size 416 \
  --model yolov4 \
  --weights ./data/yolov4.weights \
  --image ./data/kite.jpg \
  --framework tf
```

For `--framework tf`, the script builds a Keras model and loads Darknet weights.
For `--framework trt`, it loads a SavedModel and uses the TF-TRT path. It loops
1000 times, skips the first iteration in the average, and prints average FPS.

Benchmark interpretation checklist:

- Include hardware, TensorFlow version, backend, precision, batch assumptions,
  image size, and whether CPU or GPU was actually used.
- Do not compare CPU, GPU, TFLite, and TF-TRT results without naming the exact
  artifact and backend.
- If TensorFlow logs missing CUDA/cuDNN libraries, the benchmark is CPU even on
  a GPU host.

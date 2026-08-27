# Python Paddle Inference Deployment

The deployment Python scripts consume an exported model directory rather than a training config. The general detection command shape is:

```bash
python deploy/python/infer.py --model_dir=<exported-model-dir> \
  --image_file=<image.jpg> --device=CPU --threshold=0.5 --output_dir=<out>
```

Important options documented and inspected from the deployment code include:

- inputs: `--image_file`, `--image_dir`, `--video_file`, `--camera_id` depending on script;
- device/runtime: `--device=CPU/GPU/XPU`, `--run_mode=paddle/trt_fp32/trt_fp16/trt_int8`, `--enable_mkldnn`, `--cpu_threads`;
- TensorRT: `--trt_min_shape`, `--trt_max_shape`, `--trt_opt_shape`, `--trt_calib_mode`;
- output/performance: `--threshold`, `--output_dir`, `--run_benchmark`, `--save_images`, `--save_results`, `--batch_size`.

Specialized scripts cover keypoint, detector+keypoint, FairMOT/JDE/ByteTrack-style MOT, and MOT+keypoint union deployment. Use the generic preflight first, then pick the specialized runner only when the exported model family and input type match.

For COCO evaluation from deployment outputs, enable result saving and category mapping options where the runner supports them, then evaluate with the matching metric tooling.

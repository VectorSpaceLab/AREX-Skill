# Industrial Pipeline Troubleshooting

- **Pipeline tries to download models**: config model paths are URLs or missing local directories. Stage model directories and update YAML before offline/reproducible runs.
- **Input error or wrong mode**: specify exactly one input source. `camera_id`/video paths and RTSP streams have different code paths from image files/directories.
- **Codec/video failure**: verify OpenCV can open the clip/stream outside the pipeline, check frame count, and use a short local clip before RTSP.
- **TensorRT/GPU mode fails**: confirm the Paddle build, TensorRT runtime, exported model support, and shape settings. Run CPU/paddle mode first for input/config validation.
- **Counting/region output is wrong**: check polygon coordinate order, `region_type`, static-camera assumptions, object class, and whether tracking IDs remain stable.
- **Plate/attribute/action modules fail**: ensure every required component model directory exists and the module is enabled in YAML. These are multi-model chains; one missing model can break the whole pipeline.
- **MTMCT/ReID results look unstable**: confirm synchronized multi-camera inputs, ReID model path, ID thresholds, and whether enough frames were processed.
- **Performance is far below docs**: docs often quote GPU/TensorRT/Jetson-style environments. Record hardware, run mode, model size, input resolution, and warmup before comparing numbers.

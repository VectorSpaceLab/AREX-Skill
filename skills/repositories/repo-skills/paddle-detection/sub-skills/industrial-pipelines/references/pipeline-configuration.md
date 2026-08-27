# Pipeline Configuration

The pipeline CLI uses a dedicated parser with required `--config` and optional `-o key=value` overrides. Confirmed input/runtime flags include:

- inputs: `--image_file`, `--image_dir`, `--video_file`, `--video_dir`, `--rtsp`, `--camera_id`;
- output: `--output_dir`, `--pushurl`;
- runtime: `--run_mode`, `--device`, `--enable_mkldnn`, `--cpu_threads`, TensorRT min/max/opt shape, `--trt_calib_mode`;
- counting/regions: `--do_entrance_counting`, `--do_break_in_counting`, `--illegal_parking_time`, `--region_type`, `--region_polygon`, `--secs_interval`, `--draw_center_traj`.

The parser merges top-level args and `-o` overrides into nested YAML. If an override references a missing module/key, the merge helper prints a warning and leaves the config unchanged.

Typical target-checkout shape:

```bash
python deploy/pipeline/pipeline.py --config <pipeline.yml> \
  --image_file=<image.jpg> --device=CPU --run_mode=paddle --output_dir=<out>
```

For video or RTSP, check codecs, frame rate, output storage, and whether modules require temporal buffers. For multi-camera/MTMCT, each stream must be stable and synchronized enough for the configured ReID process.

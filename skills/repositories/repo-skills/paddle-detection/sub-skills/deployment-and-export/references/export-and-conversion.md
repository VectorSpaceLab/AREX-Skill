# Export and Conversion

`tools/export_model.py` exports a trained PaddleDetection config/weights pair for deployment. Confirmed flags: `-c/--config`, `-o/--opt`, `--output_dir`, `--export_serving_model`, `--slim_config`, and `--for_fd`.

Basic shape for a target checkout:

```bash
python tools/export_model.py -c <config.yml> --output_dir=<export-root> \
  -o weights=<model.pdparams> use_gpu=false
```

Expected exported model directory contents:

- `infer_cfg.yml`: preprocessing/model metadata used by deployment scripts;
- `model.pdmodel`: static graph model;
- `model.pdiparams`: parameter file;
- `model.pdiparams.info`: parameter metadata.

For TensorRT and ONNX, fixed input shape constraints may apply. YOLO-style ONNX export usually needs `TestReader.inputs_def.image_shape=[3,H,W]`. Some RCNN families need special `export_onnx=True` behavior and a higher opset. Always confirm the current converter/runtime supports the selected architecture.

`--export_serving_model=True` adds `serving_client/` and `serving_server/` directories for Paddle Serving. `--for_fd` targets FastDeploy export format and must not be combined with serving export.

Post-training quantization uses `tools/post_quant.py` and a `--slim_config`; it needs calibration/eval data and should be treated as a separate verification workload.

Benchmarks are not smoke tests. `deploy/benchmark/benchmark.sh` and related benchmark docs exercise CPU/MKLDNN and GPU/TensorRT modes and require exported models, logs, and often accelerator runtimes.

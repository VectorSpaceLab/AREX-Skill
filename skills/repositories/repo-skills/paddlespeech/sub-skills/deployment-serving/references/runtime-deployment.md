# Runtime Deployment Reference

## Paddle Inference / Static Models

Static engine sections such as `asr_inference`, `tts_inference`, and `cls_inference` use exported `.pdmodel` and `.pdiparams` files plus predictor config fields. They are not interchangeable with dynamic Python checkpoint paths.

Check for:

- `am_model`, `am_params`, `model_path`, `params_path`, or task-specific static paths.
- `predictor_conf`, `am_predictor_conf`, and `voc_predictor_conf` device settings.
- `switch_ir_optim`, `glog_info`, and `summary` fields.

## ONNX Streaming TTS

`tts_online-onnx` uses ONNXRuntime sessions and model-specific block/pad settings:

- `am` may be `fastspeech2_csmsc_onnx` or `fastspeech2_cnndecoder_csmsc_onnx`.
- `voc` may be `mb_melgan_csmsc_onnx` or `hifigan_csmsc_onnx`.
- `am_block`, `am_pad`, `voc_block`, `voc_pad`, and `voc_upsample` affect streaming quality and chunk behavior.
- `am_sess_conf` and `voc_sess_conf` control device, TensorRT, and CPU threads.

## C++ / Paddle Lite / Android / ARM

The runtime and mobile demos are reference-only until the user explicitly asks for them. They can require CMake, compilers, Paddle Inference or Paddle Lite packages, Android toolchains, ARM boards, model export, and device-specific setup.

Do not replace Python server verification with C++/mobile instructions. Treat those as separate deployment targets.

## Docker and Audio Search

Audio search demos can require Milvus, MySQL, Docker Compose, service config, and dataset/model downloads. Plan the service architecture first:

1. Decide vector model and embedding dimension.
2. Prepare external Milvus/MySQL services.
3. Configure service host/ports and table/collection names.
4. Run small data ingestion only after service and download approval.

Route embedding model questions to `../audio-analysis/SKILL.md`.

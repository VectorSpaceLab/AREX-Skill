# Repository provenance

## Source snapshot

- Repository: ASRT SpeechRecognition (`nl8590687/ASRT_SpeechRecognition`)
- Source commit: `6c7571ac41ed6ab1669d2ee8eee32dc00a34334e`
- Branch: `master`
- Exact tag: `none`
- Remote URL: public GitHub repository `https://github.com/nl8590687/ASRT_SpeechRecognition.git`
- Dirty state at generation: dirty
- Relative changed/untracked paths at generation: `skills/`

The generated skill was produced from a shallow checkout. The dirty paths are generated skill and review artifacts under `skills/`; they are not part of the upstream source baseline.

## Package/version evidence

ASRT is source-style and has no packaged distribution metadata in the inspected checkout. Version evidence therefore comes from repository files rather than `pip show`:

- README badges/documentation: Python 3.9+ and TensorFlow 2.5-2.11+.
- `requirements.txt`: pins `tensorflow-gpu==2.8.4` plus Flask, h5py, matplotlib, NumPy, protobuf, requests, SciPy, urllib3, waitress, and Wave.
- `Dockerfile`: CPU service image using `tensorflow-cpu==2.5.3` and gRPC/Flask serving dependencies.

A private creation-time CPU inspection environment verified TensorFlow CPU 2.11 model construction and safe utility/language/feature smokes. That environment path is intentionally omitted from public runtime guidance.

## Evidence paths used

- `README.md`, `README_EN.md`
- `requirements.txt`, `Dockerfile`
- `asrt_config.json`, `dict.txt`
- `datalist/thchs30/*`, `datalist/st-cmds/*`
- `data_loader.py`
- `utils/config.py`, `utils/ops.py`, `utils/ops_test.py`, `utils/thread.py`
- `speech_features/__init__.py`, `speech_features/base.py`, `speech_features/sigproc.py`, `speech_features/speech_features.py`
- `model_zoo/speech_model/keras_backend.py`, `model_zoo/speech_model/pytorch_backend.py`
- `speech_model.py`, `torch_speech_model.py`
- `train_speech_model.py`, `train_speech_model_pytorch.py`, `evaluate_speech_model.py`, `predict_speech_file.py`
- `language_model3.py`, `model_language/language_model1.txt`, `model_language/language_model2.txt`
- `asrserver_http.py`, `asrserver_grpc.py`, `client_http.py`, `client_grpc.py`
- `assets/asrt.proto`, `assets/default.html`, generated protobuf stubs
- `download_default_datalist.py`, `speech_recorder.py` as reference-only source scripts

## Refresh triggers

Refresh this skill when ASRT changes any of the following:

- public model class names, default model dimensions, output-size/dictionary relationship, CTC decoding, or weight filenames;
- `asrt_config.json` schema, datalist/label format, dictionary format, or feature extractor constraints;
- HTTP/gRPC endpoint paths, request/response schemas, status codes, or proto messages;
- dependency ranges for TensorFlow, Flask/Werkzeug, grpc/protobuf, NumPy, SciPy, or PyTorch;
- bundled language-model count files or pinyin dictionary content.

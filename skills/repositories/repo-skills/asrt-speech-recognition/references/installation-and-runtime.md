# Installation and runtime guidance

ASRT is a source-style Python project rather than a packaged distribution. There is no `pyproject.toml`, `setup.py`, or console-entry-point metadata in the inspected source. Use the project files or copied modules in a Python environment whose dependencies match the workflow being run.

## Dependency surfaces

Repository evidence shows three dependency paths:

| Surface | Dependencies | Notes |
| --- | --- | --- |
| Core utilities, config, pinyin language model, feature extraction | `numpy`, `scipy`, `matplotlib`, Python `wave` | Sufficient for datalist checks, feature shape diagnostics, and language-model decoding. |
| Keras acoustic model construction/training/evaluation/prediction | TensorFlow/Keras, `h5py`, `numpy`, `scipy` | README documents TensorFlow 2.5-2.11+ and Python 3.9+. `requirements.txt` pins `tensorflow-gpu==2.8.4`; Docker uses `tensorflow-cpu==2.5.3`. |
| HTTP/gRPC serving clients/servers | `Flask`, `waitress`, `requests`, `grpcio`, `protobuf` | Server scripts also import the Keras acoustic model and load trained weights at startup. |

The checked requirements file pins:

```text
Flask==2.2.2
h5py==3.8.0
matplotlib==3.6.3
numpy==1.24.1
protobuf==3.19.6
requests==2.28.2
scipy==1.10.0
tensorflow-gpu==2.8.4
urllib3==1.26.14
waitress==2.1.2
Wave==0.0.2
```

`Wave==0.0.2` is not needed for ordinary ASRT source use because the standard-library `wave` module is used by the code. Avoid installing it unless a target environment explicitly requires it.

## CPU versus GPU

The ASRT README treats GPU as the normal training path: Linux, 16 GB+ RAM, NVIDIA GPU with roughly 11 GB+ VRAM, large storage for corpora, Python 3.9+, and TensorFlow 2.5-2.11+. Full training/evaluation over real corpora is expensive and data-dependent.

CPU can still be useful for:

- config/datalist/dictionary validation;
- feature-shape and sample-rate checks;
- pinyin language-model decoding;
- Keras model construction and weight-loading diagnostics;
- CPU-only inference service when trained weights are available, as reflected by the Dockerfile's `tensorflow-cpu` path.

Do not report a CPU import or CPU model-construction smoke as proof that CUDA training works. A GPU training claim needs a compatible TensorFlow GPU build, CUDA/cuDNN runtime, visible NVIDIA GPU, data, and a bounded training/evaluation case.

## Minimal import checks

When working inside an ASRT project or a copied ASRT module tree, a useful smoke sequence is:

```bash
python - <<'PY'
from language_model3 import ModelLanguage
from speech_features import Spectrogram
from model_zoo.speech_model.keras_backend import SpeechModel251BN
from speech_model import ModelSpeech

ml = ModelLanguage('model_language')
ml.load_model()
print(ml.pinyin_to_text(['ni3', 'hao3', 'ya5']))
print(SpeechModel251BN().output_shape)
PY
```

Expected successful signals are text like `你好呀` and model output shape `(200, 1428)` for default `SpeechModel251BN`.

If the task only needs this generated skill's helpers, run:

```bash
python scripts/run_asrt_smokes.py
python scripts/check_asrt_runtime.py --help
```

## File prerequisites by workflow

| Workflow | Must have |
| --- | --- |
| Data loading/training/evaluation | `asrt_config.json`, `dict.txt`, all selected datalist/label files, audio corpora under configured `data_path`. |
| Feature extraction/prediction | 16 kHz WAV samples for ASRT spectrogram-style default models; audio short enough for the selected model input length. |
| Acoustic prediction/evaluation | Matching Keras model class plus trained `.model.h5` or `.model.base.h5` weights. |
| Pinyin language model | `dict.txt`, `language_model/language_model1.txt`, `language_model/language_model2.txt`. The generated `language-model` sub-skill bundles these files. |
| HTTP/gRPC service | Trained weights at the server's expected path, language-model files, selected HTTP/gRPC dependencies, and open ports. |

## Version caveats

- `fit_generator` is used in the source training wrapper; newer Keras releases may prefer `fit` with a generator and `steps_per_epoch`.
- The source `decode_wav_bytes` uses deprecated `np.int` for 4-byte samples; newer NumPy versions may fail on that path. Prefer 16-bit WAVs or adapt to `np.int32`/`np.int_`.
- `Werkzeug` 3.x may be incompatible with older Flask 2.2 environments; pinning `Werkzeug<3` is a common compatibility choice when using Flask 2.2.
- gRPC generated stubs should be regenerated with versions compatible with the installed `grpcio` and `protobuf` packages if import errors appear.

# Cross-cutting troubleshooting

Use this root troubleshooting reference for failures that span more than one ASRT sub-skill. For workflow-specific details, continue to the nearest sub-skill troubleshooting file.

## Install and import failures

| Symptom | Likely cause | Response |
| --- | --- | --- |
| `ModuleNotFoundError` for ASRT modules such as `speech_model` or `language_model3` | Running outside the ASRT module tree or without installing/copying the source | Put the ASRT source root on `PYTHONPATH`, run from the project root, or adapt the generated helper that does not require ASRT imports. |
| `ModuleNotFoundError: tensorflow` | Acoustic model/server path needs TensorFlow | Install a TensorFlow version compatible with the user's Python and backend. For CPU inspection or CPU service, `tensorflow-cpu` may be sufficient. |
| TensorFlow GPU imports but no GPU is usable | CPU-only wheel, missing CUDA/cuDNN runtime, driver/library mismatch, or container GPU passthrough absent | Do not claim GPU training readiness. Probe `nvidia-smi`, TensorFlow physical devices, CUDA/cuDNN availability, and wheel compatibility. |
| Flask import errors around Werkzeug | Flask 2.2 with incompatible Werkzeug 3.x | Pin `Werkzeug<3` or use a mutually compatible Flask/Werkzeug pair. |
| gRPC stub import/version errors | Generated `asrt_pb2*.py` files do not match installed `grpcio`/`protobuf` or package paths | Regenerate stubs from `asrt.proto` with the target environment and adjust imports before debugging model logic. |

## Data and model-file failures

| Symptom | Likely cause | Response |
| --- | --- | --- |
| `FileNotFoundError: asrt_config.json` or `dict.txt` | Stock ASRT code expects these names relative to the current working directory | Run from a directory containing the files, adjust the working directory, or use the generated validators/helpers with explicit paths. |
| Datalist loads but training fails on first batch | WAV files under configured `data_path` are absent or label IDs do not match WAV IDs | Use `data-and-features/scripts/validate_asrt_config.py` before training. |
| Pinyin token `KeyError` | Label list contains a pinyin not present in `dict.txt` | Validate labels against the dictionary and normalize tone-number format. |
| Server fails immediately with missing `save_models/SpeechModel251bn.model.h5` | ASRT server scripts load acoustic weights at module import time | Provide the expected trained weights or edit the server path in a project copy. Route to `acoustic-models` for weight naming. |
| Prediction/evaluation works with base weights but resume training fails | `.model.base.h5` contains the inference graph weights, not the training CTC graph layout | Load base weights through `get_eval_model().load_weights(...)` for inference/evaluation; use `.model.h5` for training resume. |

## Audio and request failures

| Symptom | Likely cause | Response |
| --- | --- | --- |
| `ASRT currently only supports wav audio files with a sampling rate of 16000 Hz` | Spectrogram-style features received non-16 kHz audio | Resample to 16 kHz mono before ASRT prediction/training, then rerun feature inspection. |
| Broadcast/shape errors during `forward` | Extracted feature frame count exceeds model `input_shape[0]` or is too short/malformed | Validate duration and feature shape. Default model input length is 1600 frames, roughly 16 seconds. |
| HTTP `/speech` or `/all` returns `500000` | Bad JSON shape, invalid base64, wrong raw sample bytes, unsupported byte width, sample-rate mismatch, or model failure | Rebuild payload with `serving-clients/scripts/make_http_payload.py`, inspect WAV metadata in `data-and-features`, and check server logs for model/weight errors. |
| HTTP client sends `b'...'` string in `samples` | Encoded bytes were converted with `str(bytes)` rather than decoded to ASCII | URL-safe-base64 encode raw frames, then `.decode('ascii')` before JSON serialization. |
| 4-byte WAV request fails with `np.int` | Source code uses deprecated `numpy.int` for `byte_width == 4` | Prefer 16-bit PCM WAV (`byte_width == 2`) or patch the server-side decode path to `np.int32`/`np.int_`. |

## Scope and verification limits

This generated skill does not bundle trained acoustic weights or full corpora. It can verify and guide data schema, feature shape, language-model decoding, model construction, client payloads, and deployment prerequisites. It cannot by itself verify:

- full GPU training throughput or convergence;
- speech recognition accuracy on THCHS30/ST-CMDS/AIShell/etc.;
- prediction from a user's trained weights;
- a live HTTP/gRPC service round trip without an already running server and weights.

When a user asks for those outcomes, state the missing artifact/backend/data prerequisite and produce a bounded verification plan instead of implying the skill has already proven it.

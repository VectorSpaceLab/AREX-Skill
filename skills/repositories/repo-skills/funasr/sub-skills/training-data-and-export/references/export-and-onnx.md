# Export, ONNX, and local inference

Use this reference after data and training configuration are already understood. Export may load/download a model and may require optional ONNX tooling, so keep it reference-backed unless the user asks for a live export.

## Export command surface

The packaged export command is Hydra-based:

```shell
funasr-export \
  ++model=paraformer \
  ++type=onnx \
  ++quantize=false \
  ++device=cpu
```

Equivalent module form:

```shell
python -m funasr.bin.export \
  ++model=paraformer \
  ++type=onnx \
  ++quantize=false \
  ++device=cpu
```

Key options:

| Option | Default | Notes |
|---|---|---|
| `++model` | required by the model loader | Model id or local model directory. |
| `++device` | `cpu` when omitted by the export module | Use CPU for safe export planning unless the user requests GPU. |
| `++type` | `onnx` | Some model examples use `torchscript`; verify the selected model supports it. |
| `++quantize` | `false` | Quantization may need representative calibration input. |
| `++input` | unset | Optional sample input passed to `model.export(...)`. |
| `++fallback-num` | `5` | Export fallback count used by the module. Note the hyphenated Hydra key. |
| `++calib_num` | `100` | Calibration count for quantized export paths. |
| `++opset_version` | `14` | ONNX opset version. |

Python API:

```python
from funasr import AutoModel

model = AutoModel(model="paraformer", device="cpu")
result = model.export(type="onnx", quantize=False)
print(result)
```

## Local inference after training

### When `configuration.json` exists

If the trained model directory contains `configuration.json`, FunASR can usually load it as a local model:

```shell
python -m funasr.bin.inference \
  ++model="${MODEL_DIR}" \
  ++input="${AUDIO_OR_SCP}" \
  ++output_dir="${OUTPUT_DIR}" \
  ++device=cpu
```

Python form:

```python
from funasr import AutoModel

model_dir = "MODEL_DIR"
audio_file = "audio.wav"
model = AutoModel(model=model_dir, device="cpu")
result = model.generate(input=audio_file)
print(result)
```

Use the user's actual session paths when running this; do not hard-code paths from examples.

### When `configuration.json` is missing

If the model directory only has training artifacts such as `config.yaml`, `model.pt`, token files, and CMVN files, pass the exact config and checkpoint explicitly:

```shell
python -m funasr.bin.inference \
  --config-path "${CONFIG_DIR}" \
  --config-name "config.yaml" \
  ++init_param="${CHECKPOINT}" \
  ++tokenizer_conf.token_list="${TOKEN_LIST}" \
  ++frontend_conf.cmvn_file="${CMVN_FILE}" \
  ++input="${AUDIO_OR_SCP}" \
  ++output_dir="${OUTPUT_DIR}" \
  ++device=cpu
```

Required choices:

- `CONFIG_DIR`: directory that contains the training `config.yaml` or `config.json`.
- `CHECKPOINT`: model parameter file, commonly `model.pt`, `model.pt.avg10`, or a specific epoch/step checkpoint.
- `TOKEN_LIST`: token file referenced by the training config; override it only when the config points somewhere stale.
- `CMVN_FILE`: frontend CMVN file referenced by the training config; override it only when the config points somewhere stale.

If any of these are unknown, inspect the user's model directory and training logs before running inference.

## ONNX optimization and runtime smoke

Optional optimization:

```shell
python -m pip install -U onnxslim
onnxslim model.onnx model.onnx
```

Optional ONNX runtime package smoke:

```python
from funasr_onnx import Paraformer

model = Paraformer("MODEL_DIR_OR_ID", batch_size=1, quantize=True)
result = model(["audio.wav"])
print(result)
```

The ONNX runtime package is separate from the main training package. Its release contract keeps the runtime install torch-free: it depends on ONNX Runtime, librosa/scipy/numpy, kaldi-native-fbank, PyYAML, jieba, and sentencepiece rather than `torch`.

## Package-data expectations

When building or validating the main FunASR wheel, confirm runtime package data is included. Important package-data classes include:

- normalizer JSON data used by SenseVoice/Whisper-style components;
- RWKV BAT CUDA/C++ source files that are packaged as runtime data.

A missing file in an installed wheel can look like an export or inference bug, but the fix is packaging data, not an inference command change. If the user reports files missing from a wheel, inspect the built wheel contents before changing export parameters.

## What this sub-skill does not deploy

Exported artifacts can later be served, but HTTP servers, realtime WebSocket servers, Docker validation, Triton, GGUF, and runtime SDK deployment belong to `../serving-and-runtime/`. vLLM/Nano acceleration belongs to `../llm-asr-and-vllm/`.

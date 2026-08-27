# vLLM and Docker plan

This reference covers local serving of DeepAnalyze-8B with vLLM and the Docker GPU path.

## Public model sources

The model is published in two public locations:

- Hugging Face: `RUC-DataLab/DeepAnalyze-8B`
- ModelScope: `RUC-DataLab/DeepAnalyze-8B`

Use whichever source matches the download toolchain you already trust. This reference only plans the deployment; it does not fetch weights for you.

## Memory table

Use the following table to choose the launch row. The table is reproduced from the repo guidance and should stay the source of truth for context sizing.

| GPU memory | Model type | Recommended max-model-len | FP8 KV cache |
|------------|------------|--------------------------|--------------|
| 16GB | 8-bit quantized | 8192 | yes |
| 16GB | 4-bit quantized | 49152 | yes |
| 24GB | original model | 16384 | yes |
| 24GB | 8-bit quantized | 98304 | yes |
| 24GB | 4-bit quantized | 131072 | yes |
| 40GB | original model | 131072 | yes |
| 40GB | 8-bit quantized | 131072 | no table flag |
| 80GB | original model | 131072 | no table flag |

### Quick selection notes

- 16GB: prefer 4-bit plus FP8 KV cache when you want the longest supported context.
- 24GB maximum-context case: prefer 4-bit plus FP8 KV cache with `--max-model-len 131072`.
- 24GB precision-first case: use the original model with `--max-model-len 16384` and FP8 KV cache.
- 40GB: the original model reaches the long-context row.
- 80GB: the original model reaches the long-context row without needing extra memory pressure tricks.

## vLLM command shape

Use the OpenAI-compatible entrypoint and keep the serving name fixed to `DeepAnalyze-8B`:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model <model_path> \
  --served-model-name DeepAnalyze-8B \
  --max-model-len <value_from_table> \
  --gpu-memory-utilization 0.95 \
  --port 8000 \
  [--kv-cache-dtype fp8] \
  --trust-remote-code
```

### Recommended local examples

16GB, 4-bit, longest supported context:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model /path/to/deepanalyze-4bit \
  --served-model-name DeepAnalyze-8B \
  --max-model-len 49152 \
  --gpu-memory-utilization 0.95 \
  --port 8000 \
  --kv-cache-dtype fp8 \
  --trust-remote-code
```

24GB, maximum-context target:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model /path/to/deepanalyze-4bit \
  --served-model-name DeepAnalyze-8B \
  --max-model-len 131072 \
  --gpu-memory-utilization 0.95 \
  --port 8000 \
  --kv-cache-dtype fp8 \
  --trust-remote-code
```

24GB, precision-first target:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model /path/to/original/model \
  --served-model-name DeepAnalyze-8B \
  --max-model-len 16384 \
  --gpu-memory-utilization 0.95 \
  --port 8000 \
  --kv-cache-dtype fp8 \
  --trust-remote-code
```

80GB, original model target:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model /path/to/original/model \
  --served-model-name DeepAnalyze-8B \
  --max-model-len 131072 \
  --gpu-memory-utilization 0.95 \
  --port 8000 \
  --trust-remote-code
```

## Docker GPU path

### Prerequisites

- Docker installed.
- NVIDIA GPU available.
- NVIDIA Container Toolkit installed for GPU pass-through.

### Prebuilt image

The repo documents a prebuilt image path:

```bash
docker pull facdbe/deepanalyze-env:latest
docker run --gpus all -it --rm -p 8000:8000 facdbe/deepanalyze-env:latest
```

### Build from the Dockerfile

```bash
docker build -t deepanalyze-env:latest .
docker run --gpus all -it --rm -p 8000:8000 deepanalyze-env:latest
```

### Run vLLM inside the container

Mount the model directory and point vLLM at the mounted path:

```bash
docker run --gpus all -d \
  -p 8000:8000 \
  -v /path/to/models:/models \
  --name deepanalyze-vllm \
  deepanalyze-env:latest \
  python3 -m vllm.entrypoints.openai.api_server \
    --model /models/your-model-name \
    --host 0.0.0.0 \
    --port 8000 \
    --served-model-name DeepAnalyze-8B \
    --gpu-memory-utilization 0.95 \
    --trust-remote-code
```

Add `--kv-cache-dtype fp8` to the command when the selected memory row calls for it.

### Compose path

The bundled compose file maps ports 8000:8000 and mounts a `./models` directory. Use it when you want a repeatable container wrapper around the same serving command.

## Boundary reminder

This reference stops at model download and serving. If the task becomes client code, file upload, thread persistence, or request/response shape work after the server exists, hand off to `api-and-clients`.

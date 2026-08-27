# Sparrow Parse backend options

This reference summarizes the Sparrow Parse package contract and how to choose a backend without invoking a model.

## Package contract

- Package: `sparrow-parse==1.5.6`.
- Python: use Python 3.12+ for current Sparrow Parse package installs.
- Installed package imports expected by this skill:
  - `from sparrow_parse.extractors.vllm_extractor import VLLMExtractor`
  - `from sparrow_parse.vlmb.inference_factory import InferenceFactory`
- Package self-message: `python -m sparrow_parse` works when the package is installed.
- Upstream console-script caveat: the declared `sparrow-parse` executable points at `sparrow_parse:main`, while the package places `main()` under `sparrow_parse.__main__`; expect that console script to fail unless patched. Prefer imports, `python -m sparrow_parse`, or Sparrow's engine wrapper.

Core code shape:

```python
from sparrow_parse.extractors.vllm_extractor import VLLMExtractor
from sparrow_parse.vlmb.inference_factory import InferenceFactory

config = {"method": "mlx", "model_name": "mlx-community/Qwen3.6-35B-A3B-8bit"}
model = InferenceFactory(config).get_inference_instance()
extractor = VLLMExtractor()
results, num_pages = extractor.run_inference(
    model,
    [{"file_path": "invoice.pdf", "text_input": "retrieve data based on provided JSON schema. return response in JSON format, by strictly following this JSON schema: {\"invoice_number\":\"str\"}"}],
    tables_only=False,
    generic_query=False,
    crop_size=None,
    apply_annotation=False,
    debug_dir=None,
    debug=False,
    mode=None,
)
```

`VLLMExtractor.run_inference` signature:

```text
run_inference(model_inference_instance, input_data, tables_only=False,
              generic_query=False, crop_size=None, apply_annotation=False,
              ocr_callback=None, debug_dir=None, debug=False, mode=None)
```

Return value: `(results, num_pages)`, where `results` is a list of backend responses and `num_pages` is `0` for text-only, `1` for an image, and page count for PDFs.

## Backend selection matrix

| Method | Config keys | Best fit | Required setup | Known limits |
|---|---|---|---|---|
| `mlx` | `method`, `model_name` | Apple Silicon local VLMs | `pip install sparrow-parse[mlx]`; Apple Silicon macOS; model available to MLX | Fails on non-Apple/unsupported wheels. Annotation prompting is meaningful mainly for Qwen-style models. |
| `ollama` | `method`, `model_name` | Local Ollama multimodal models | `pip install sparrow-parse`; Ollama daemon running; model pulled | Annotation is disabled by implementation. Missing daemon/model raises Ollama errors. |
| `vllm` | `method`, `model_name` | NVIDIA CUDA production inference | `pip install sparrow-parse[linux]`; CUDA/vLLM-compatible GPU; model cached or downloadable | Annotation is disabled. Model loads at initialization and can exhaust VRAM. Default multimodal limit is one image per prompt. |
| `mistral` | `method`, `model_name` | Cloud OCR plus structured extraction | `MISTRAL_API_KEY`; Mistral package installed | Uses Mistral OCR first, then a Mistral chat model for JSON extraction. Costs and network/API limits apply. |
| `huggingface` | `method`, `hf_space`, `hf_token` | Hosted Gradio/HF Space inference | `HF_TOKEN` with access; HF Space serving `/run_inference` | `options[1]` is an HF Space, not a model name. The backend parses a Gradio response string. |
| `local_gpu` | `method`, `device`, model supplied externally | Custom PyTorch-style model | Caller must provide/load a compatible model | Default factory path calls a placeholder loader and raises `NotImplementedError`. |

## Pipeline options mapping

When using the Sparrow Parse pipeline or engine wrapper, backend options are parsed as a list:

```text
[backend_method, model_or_space, optional_flag, optional_flag, ...]
```

Supported optional flags:

- `tables_only`: detect/crop tables before VLM inference.
- `validation_off`: skip the pipeline JSON schema validator.
- `apply_annotation`: request value/bbox/confidence style output where supported.

Examples:

```text
["mlx", "mlx-community/Qwen3.6-35B-A3B-8bit"]
["mlx", "mlx-community/Qwen3.6-35B-A3B-8bit", "tables_only"]
["vllm", "mistralai/Mistral-Small-3.2-24B-Instruct-2506", "validation_off"]
["huggingface", "owner/space-name"]
["mistral", "mistral-ocr-latest"]
```

If fewer than two options are supplied, the pipeline raises `ValueError("Invalid options provided for inference backend configuration.")`.

## Optional setup commands

Choose one installation path based on the backend. Do not install every extra unless needed.

```bash
# Generic package, Ollama, Hugging Face client, PDF helpers, table helper dependencies from base package metadata
python -m pip install 'sparrow-parse==1.5.6'

# Apple Silicon MLX backend
python -m pip install 'sparrow-parse[mlx]==1.5.6'

# Linux CUDA/vLLM backend
python -m pip install 'sparrow-parse[linux]==1.5.6'

# Mistral/HF credentials are environment variables, not command-line query values
export MISTRAL_API_KEY='...'
export HF_TOKEN='...'
```

For PDF inputs, install poppler separately so `pdf2image` can call `pdftoppm`:

```bash
# macOS
brew install poppler

# Debian/Ubuntu
sudo apt-get install poppler-utils
```

## Backend behavior notes

- `mlx`, `ollama`, `vllm`, and `mistral` clean JSON from markdown fences or embedded object/array text before returning the response where possible.
- `mlx` resizes images for memory efficiency and rescales returned bbox coordinates when `apply_annotation=True` and JSON parsing succeeds.
- `ollama` and `vllm` catch per-image errors and continue with other images; an empty `results` list usually means all images failed or paths were missing.
- `mistral` image flow encodes each image, runs OCR with HTML table extraction and footer capture, then asks `mistral-small-latest` to produce a JSON object from OCR markdown plus the extraction prompt.
- `huggingface` expects `input_data[0]["file_path"]` to be a list of existing files and sends them to a Gradio endpoint named `/run_inference`.

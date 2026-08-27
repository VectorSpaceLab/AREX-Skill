# Troubleshooting Sparrow Parse document extraction

Use this guide to identify which layer failed before changing models or prompts.

## Quick triage

1. **Query preparation fails before inference**: likely invalid JSON query, invalid hints JSON, or missing backend options.
2. **Package import fails**: installation/environment mismatch or backend extra missing.
3. **Backend initialization fails**: model name, credentials, platform, CUDA/VRAM, Ollama daemon, or cloud access.
4. **PDF fails before model call**: poppler/PDF conversion issue.
5. **Inference returns no result or malformed result**: missing file, unsupported model prompt format, VLM quality, output length, or schema complexity.
6. **Validation says false**: output is JSON but does not match Sparrow's example-schema-derived validator.

## Invalid JSON query

Symptoms:

- `JSONDecodeError` printed while preparing the query.
- `Caught an exception: Error preparing query: Invalid query. Please provide a valid JSON query.`

Fix:

- Validate the query with `python -m json.tool` or the bundled request builder before inference.
- Use double quotes in JSON. Python-style single quotes are not valid JSON.
- Use `"*"` only for generic extraction or page-type detection; do not wrap `*` in a JSON object.
- For arrays, provide at least one object example: `[{"field":"str"}]`.

## Invalid JSON output

Symptoms:

- Pipeline output includes `"message": "Invalid JSON format in LLM output"`.
- Table extraction returns a nested invalid JSON message for a crop.
- Direct package output is prose, markdown fences, or partial JSON.

Fix:

1. Confirm the user query was valid JSON; this is separate from model output validity.
2. Retry a minimal schema with one or two fields.
3. Add a hint such as `Return only raw JSON. Do not include markdown fences or explanations.`
4. Use markdown-first extraction for table-heavy or OCR-heavy pages.
5. Turn off annotation unless coordinates are required.
6. Keep validation enabled for normal schema extraction; do not use `validation_off` unless diagnosing the raw backend output.
7. If output is valid JSON but validation fails, inspect `valid` for a schema error and adjust field types, especially numbers with currency symbols or nullable fields.

## Missing backend options

Symptoms:

- `ValueError("Invalid options provided for inference backend configuration.")`.
- Pipeline receives `options=None` or only one option.

Fix:

- Provide at least backend method and model/space:
  - `mlx,<model-name>`
  - `ollama,<model-name>`
  - `vllm,<model-name>`
  - `mistral,<ocr-model-name>`
  - `huggingface,<owner/space>`
- Place flags after the first two options: `tables_only`, `validation_off`, `apply_annotation`.
- For direct package calls, build a config dict matching the selected method instead of passing CLI-style strings.

## MLX on non-Apple or wrong install

Symptoms:

- Import errors for `mlx`, `mlx_vlm`, or MLX wheels.
- Installation fails on Linux/Windows.
- Runtime platform is not macOS Apple Silicon.

Fix:

- Use MLX only on Apple Silicon macOS.
- Install `sparrow-parse[mlx]==1.5.6` in a Python 3.12+ environment.
- On Linux/Windows, select `ollama`, `vllm`, `huggingface`, or `mistral` instead.
- For annotation, prefer Qwen-compatible MLX models; other model families may ignore bbox-style schema transformation.

## vLLM, CUDA, model, and VRAM issues

Symptoms:

- vLLM import errors.
- CUDA initialization failure.
- Model loads slowly then crashes or exits due to memory.
- `allowed_local_media_path`, multimodal limit, or image prompt errors.

Fix:

- Use Linux with a CUDA/vLLM-compatible GPU and install `sparrow-parse[linux]==1.5.6`.
- Verify CUDA outside Sparrow before loading the model.
- Start with a known model and enough VRAM. Full precision 24B VLMs can require very large GPUs; reduce model size or use a quantized backend when memory is limited.
- Reduce concurrent model loads. The vLLM backend loads the model at initialization and keeps it resident.
- Crop large scans, process fewer pages, or use page-level runs if prompts/images exceed limits.
- Remember vLLM implementation disables annotation and uses one image per prompt by default.

## Ollama daemon or model missing

Symptoms:

- Connection refused or client connection error.
- Model not found.
- Test code advises `ollama serve` or `ollama pull <model>`.

Fix:

```bash
ollama serve
ollama list
ollama pull <model-name>
```

Then retry with `method="ollama"` and the exact local model name. Use a multimodal-capable model; text-only models will not process document images correctly. Annotation is disabled in the Ollama backend.

## Mistral and Hugging Face credentials

### Mistral

Symptoms:

- `KeyError: 'MISTRAL_API_KEY'`.
- Cloud request authentication or quota errors.

Fix:

```bash
export MISTRAL_API_KEY='...'
```

Use `method="mistral"` and a Mistral OCR model name. Image flow performs OCR first and then asks a chat model for JSON; network, quota, and billing limits can affect both stages.

### Hugging Face

Symptoms:

- Missing/invalid token.
- Space not found or endpoint `/run_inference` unavailable.
- Gradio response cannot be parsed.

Fix:

```bash
export HF_TOKEN='...'
```

Use `method="huggingface"`, `hf_space="owner/space"`, and `hf_token=os.getenv("HF_TOKEN")`. Confirm the Space is running and accepts `input_imgs`, `text_input`, and API name `/run_inference`.

## Poppler and PDF conversion

Symptoms:

- `pdf2image` errors about missing `pdftoppm`.
- PDF conversion fails before any model output.
- Empty or partial page image list.

Fix:

```bash
# macOS
brew install poppler

# Debian/Ubuntu
sudo apt-get install poppler-utils

# verify
pdftoppm -h
```

Also check the PDF page count with a lightweight PDF reader. If conversion of all pages is too slow or memory-heavy, split the document and process selected pages.

## Table detection and model downloads

Symptoms:

- First `tables_only` run is slow.
- Download errors for `microsoft/table-transformer-detection`.
- No tables found despite visible tables.
- `page_tables` contains invalid JSON for one or more crops.

Fix:

- Ensure `transformers`, `torch`, `torchvision`, and model cache access are available.
- Run once with debug enabled and a `debug_dir` to inspect table crops.
- For dense or large tables, try markdown/table-template flow with dots.ocr rather than direct table crops.
- Increase image resolution if table detector misses lines; reduce crop/border removal if table edges are cut off.
- If no tables are found, the extractor returns a structured `status: empty` message rather than throwing.

## Crop, page, and debug issues

### Crop problems

Symptoms:

- `Crop size is too large for the image dimensions`.
- Header/footer fields disappear.
- Debug cropped images show important content removed.

Fix:

- Start with `crop_size=0` or no crop.
- Increase slowly (`20`, `40`, `60`) only when scans have noisy borders.
- Avoid crop on invoices where totals, VAT IDs, or page numbers are near edges.

### Multi-page problems

Symptoms:

- Expected combined output but only first page appears.
- Page numbers are missing from direct package output.
- PDF table results are nested under `page_tables` and hard to merge.

Fix:

- Remember direct `VLLMExtractor` returns raw results; page-number wrapping is a pipeline feature.
- For package calls, merge `results` yourself and attach page indexes based on result order.
- For page-type workflows, classify pages first and then run page-specific schemas.

### Debug artifacts

Symptoms:

- Debug directory fills with page and crop images.
- Confusion between temporary conversion files and retained debug copies.

Fix:

- Use `debug_dir` only for inspection runs.
- Temporary directories created by the extractor are cleaned automatically; `debug_dir` files are intentionally retained.
- Keep debug outputs outside the runtime skill tree unless they are intentionally bundled examples.

## Local GPU placeholder

Symptoms:

- `NotImplementedError("Model loading logic not implemented")` from `InferenceFactory`.

Fix:

- Do not select `local_gpu` through the default factory unless you have patched `_load_local_model` or constructed `LocalGPUInference(model=..., device=...)` directly with a compatible model object.
- For ordinary GPU document extraction, prefer `vllm` or `ollama`.

## Upstream console script issue

Symptoms:

- Running `sparrow-parse` fails because `sparrow_parse.main` cannot be imported.
- `python -m sparrow_parse` works.

Fix:

- Use `python -m sparrow_parse` for package self-message.
- Use package imports or Sparrow's engine wrapper for real extraction.
- If a deployment requires the executable name, patch the entry point to `sparrow_parse.__main__:main` in that environment.

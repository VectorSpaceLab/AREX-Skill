# Inference and Deployment Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Output repeats prompt or answers in the wrong style | Wrong model family or missing Alpaca prompt wrapper. | Use Chinese Alpaca for instruction/chat tasks and pass `--with_prompt` in HF inference. |
| Very slow generation | CPU-only path or an undersized GPU for the chosen model. | Confirm `--only_cpu` is intentional. Otherwise use GPU and/or smaller model size. |
| `tokenizer_path` not provided and wrong tokenizer gets loaded | Script defaults to `--lora_model` or `--base_model`. | Set `--tokenizer_path` explicitly when debugging. LLaMA and Alpaca tokenizers are not interchangeable. |
| `PeftModel.from_pretrained` load error | LoRA path incompatible with base model or adapter files missing. | Re-check family compatibility and ensure the LoRA directory contains the expected adapter artifacts. |
| `CUDA_VISIBLE_DEVICES` surprises | `--gpus` or `--only_cpu` changed the visible device list. | Inspect the effective flag combination before generation. |
| `load_in_8bit` errors | Installed stack or backend does not support 8-bit loading. | Remove the flag or install a compatible GPU-enabled stack. 8-bit loading is a memory-saving option, not a substitute for compatible weights. |
| `xformers is not installed correctly` warning | Optional xFormers backend is missing. | The scripts fall back to regular attention. Only install xFormers if the user wants that optimization and the wheel matches the torch/CUDA stack. |
| `Alpha can only be a float or 'auto'` | Invalid NTK alpha string. | Pass a float or `auto`. |
| Batch inference exits but no file is written | `--predictions_file` path missing or directory unwritable. | Use a writable output directory. The script creates `generation_config.json` next to predictions. |
| Gradio launch exposes a public link unexpectedly | `--share=True` default or user requested sharing. | Confirm whether share/public exposure is allowed. Set `--share False` for local-only use if needed. |
| Gradio/queue errors during launch | Missing `gradio` or version mismatch. | Install the optional Gradio dependency and rerun `--help` first. |
| FastAPI request fails with message schema errors | The bundled server expects dictionaries with `role` and `message` keys, then converts them to internal `ChatMessage` objects. | Adapt the client or patch deliberately. Do not assume OpenAI-style `content` works for this repository version without checking. |
| `/v1/embeddings` returns poor vectors | Demo uses mean-pooled final hidden states, not a specialized embedding model. | Treat embeddings as demo output only; do not use as benchmark-quality semantic embeddings. |
| `ModuleNotFoundError` for `fastapi`, `uvicorn`, `shortuuid`, `pydantic`, or `gradio` | Optional packages missing from the runtime. | Install only the missing workflow-specific dependency set after confirming the user wants the server/UI workflow. |
| `ModuleNotFoundError` for `langchain` or `faiss` | Optional LangChain stack not installed. | Install the missing optional backend only if the user wants the QA/summarization demo. |
| `merge_llama_with_*` or `PeftModel` errors before inference | Model was not reconstructed or adapter/base family mismatch. | Route back to model reconstruction guidance. |
| `RuntimeError: CUDA out of memory` during inference | Model too large, 8-bit not enabled, or too many GPU allocations. | Reduce model size, enable 8-bit if supported, or use CPU only for a minimal test; do not claim CPU is equivalent to GPU throughput. |

## Quick Recovery Flow

1. Confirm model family and tokenizer family.
2. Run `python scripts/inference_hf.py --help` or the corresponding server/UI help check in the target environment.
3. Check whether the model is merged or still a LoRA adapter.
4. Review `--gpus`, `--only_cpu`, `--load_in_8bit`, and `--alpha`.
5. For servers, confirm port/share/network policy before launch.
6. For LangChain, verify the optional dependency set and local file/model paths first.

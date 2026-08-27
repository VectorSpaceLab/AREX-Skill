# HF inference workflows

## Main execution modes

### One-off generation
- `inference_hf.py` can run in instruction mode, file mode, or interactive mode.
- `--with_prompt` wraps raw instructions in the Alpaca-2 prompt template.
- `--only_cpu` disables GPU usage and forbids quantized loading in the bundled CLI.

### Chat / multi-turn
- `gradio_demo.py` runs a browser chat UI with history handling and optional streaming behavior.
- The UI can use the local HF model directly or proxy through the optional vLLM branch.

### Acceleration helpers
- `--load_in_8bit` and `--load_in_4bit` are the quantized loading paths.
- `--use_flash_attention_2` enables the FlashAttention-2 patch path when the optional package is present.
- `--use_ntk` applies the long-context NTK patch.
- `--speculative_sampling` requires a draft base model and optionally a draft LoRA adapter.

## Prompting rules

- The bundled prompt assets provide the default minimal Alpaca-2 system prompt and a longer-response variant.
- The first user turn is usually wrapped with a system prompt; subsequent turns use the chat history structure already handled by the scripts.
- Negative prompts and classifier-free guidance are only meaningful when the chosen code path supports them.

## Practical model-loading rules

| Situation | Expected behavior |
| --- | --- |
| Model and tokenizer vocabulary differ | The scripts resize embeddings to match the tokenizer |
| CPU-only mode with quantized loading | The script rejects the configuration |
| Speculative sampling without a draft model | The script raises an argument error |
| vLLM branch with LoRA or quantization | The script rejects the configuration |

## Generated outputs

- File-based generation writes a JSON list of input/output pairs.
- Interactive mode writes console responses only.
- The Gradio demo keeps history in memory and can truncate earlier turns when the prompt gets too long.

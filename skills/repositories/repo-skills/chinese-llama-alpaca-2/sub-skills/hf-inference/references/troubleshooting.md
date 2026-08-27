# HF inference troubleshooting

## Common failures

- `--speculative_sampling` without a draft base model is invalid.
- `--load_in_8bit` or `--load_in_4bit` cannot be combined with CPU-only mode.
- `--use_vllm` does not support LoRA, quantization, speculative sampling, or CFG branches in the bundled CLI.
- Missing FlashAttention/xformers is usually only a warning; the base inference path still works.

## Tokenizer and prompt issues

- If the model seems to answer in the wrong style, check whether the task needs `--with_prompt`.
- If the chat history grows too long, the Gradio demo will truncate older turns according to its `max_memory` setting.
- Always verify that the tokenizer path belongs to the same model family as the base checkpoint.

## Backend and hardware issues

- GPU acceleration is optional for the basic inference path, but required for the optional quantized/flash-attention branches.
- `flash_attn` and `xformers` are acceleration helpers and should not be treated as core runtime dependencies.
- If the runtime complains about classifier-free guidance or speculative sampling, check the transformer version and the selected branch before changing the prompt.

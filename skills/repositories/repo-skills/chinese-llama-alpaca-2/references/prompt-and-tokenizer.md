# Prompt and tokenizer assets

## Bundled prompts

- `assets/prompts/alpaca-2.txt`
  - Minimal Alpaca-2 system prompt.
  - Best for standard chat and instruction-following flows.
- `assets/prompts/alpaca-2-long.txt`
  - Slightly longer system prompt that encourages more detailed replies.
  - Use it when the user wants longer responses or a more verbose assistant style.

## Bundled tokenizer files

- `assets/tokenizer/tokenizer.model`
- `assets/tokenizer/tokenizer_config.json`
- `assets/tokenizer/special_tokens_map.json`

## Usage notes

- The tokenizer bundle belongs to the second-generation Chinese-LLaMA/Alpaca model family.
- Do not mix these tokenizer files with first-generation tokenizer assets.
- If a script accepts `--tokenizer_path`, the bundled tokenizer directory is the safest local fallback when the user does not already have a compatible tokenizer next to the model weights.
- Training and inference scripts may resize embeddings when the tokenizer vocabulary and model vocabulary differ.

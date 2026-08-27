# Multimodal Prompt Templates

## LLaVA-Style Templates

The multimodal conversation library exposes these useful template families:

- `plain` / `v0_plain`
- `llava_v0`
- `v0_mmtag`
- `llava_v1`
- `v1_mmtag`
- `llava_llama_2`

## When To Use Them

- Use `plain` for a simple one-image, one-answer exchange.
- Use `llava_v0` or `v0_mmtag` when the prompt uses `###Human:` / `###Assistant:` separators.
- Use `llava_v1` or `v1_mmtag` when the prompt follows the alternating USER/ASSISTANT style.
- Use `llava_llama_2` when the multimodal checkpoint expects Llama-2-style system text.

## Token Markers

- `<image>` is the core image sentinel.
- `<im_start>` and `<im_end>` are used when the model wants explicit start/end wrappers.
- MiniGPT-style chat prompts use `<Img><ImageHere></Img>` in the archived compatibility recipes.

## Selection Guidance

- Match the prompt family to the checkpoint family first.
- Match the dataset `sep_style` to the same family.
- If the model family is unclear, prefer the simplest plain/LLaVA route and validate before a long run.

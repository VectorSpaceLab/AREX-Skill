# Image Generation API Reference

## Purpose

Read this when adapting Janus or Janus-Pro text-to-image generation.

## Public imports

```python
from transformers import AutoModelForCausalLM
from janus.models import MultiModalityCausalLM, VLChatProcessor
```

## Verified generation building blocks

### `VLChatProcessor`

The same processor used for understanding also provides the generation tags and prompt formatting helpers.

Relevant members:

- `apply_sft_template_for_multi_turn_prompts(...)`
- `image_start_tag`
- `pad_id`
- `tokenizer`

### `MultiModalityCausalLM`

Relevant generation members:

- `language_model.get_input_embeddings()`
- `language_model.model(...)`
- `gen_head(...)`
- `prepare_gen_img_embeds(...)`
- `gen_vision_model.decode_code(...)`

## Verified parameter defaults from the repo

The README and source examples consistently use:

- `temperature=1`
- `parallel_size=16` in the pure script examples, `5` in the demos
- `cfg_weight=5`
- `image_token_num_per_image=576`
- `img_size=384`
- `patch_size=16`

## Canonical generation pattern

1. Build a one-turn user/assistant conversation.
2. Convert it to an SFT prompt.
3. Append `image_start_tag`.
4. Tokenize the prompt.
5. Create a conditional branch and an unconditional branch for classifier-free guidance.
6. Loop over image tokens:
   - run the language model forward pass,
   - take the last hidden state,
   - compute logits with `gen_head`,
   - blend conditional and unconditional logits,
   - sample the next image token,
   - convert the token to an image embedding with `prepare_gen_img_embeds`,
   - continue the loop.
7. Decode the final image token grid with `gen_vision_model.decode_code`.
8. Save or display the resulting image(s).

## Output handling

The repo examples save images under `generated_samples/`. The generated skill's helper should let the caller choose the output directory.

## Family notes

- Use `deepseek-ai/Janus-1.3B` for the base Janus family.
- Use `deepseek-ai/Janus-Pro-1B` or `deepseek-ai/Janus-Pro-7B` for Janus-Pro.
- Do not route JanusFlow text-to-image generation here; it has a different flow-based decoder path.

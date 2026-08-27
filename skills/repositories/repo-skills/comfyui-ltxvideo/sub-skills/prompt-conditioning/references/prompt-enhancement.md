# Prompt Enhancement

Prompt enhancement nodes rewrite raw text into more detailed prompt strings. They do not decode video, run samplers, or by themselves create reusable conditioning files. For model/backend placement basics, see the root [model and backend requirements](../../../references/model-and-backend-requirements.md).

## Two enhancer families

| Family | Nodes | Model source | Network side effect | Optional image input | Output |
| --- | --- | --- | --- | --- | --- |
| Local Gemma enhancer | `LTXVGemmaEnhancePrompt` | Gemma model already loaded by `LTXVGemmaCLIPModelLoader` | None if local files are complete | `image` | enhanced prompt string |
| Generic Hugging Face enhancer | `LTXVPromptEnhancerLoader` + `LTXVPromptEnhancer` | Separate LLM and image-captioner repositories | Downloads to ComfyUI model cache if absent | `image_prompt` | enhanced prompt string |

Use either enhancer before local or API text encoding. If the graph already has `GemmaAPITextEncode` with `enhance_prompt=true`, adding a separate enhancer can double-rewrite the prompt; do that only intentionally.

## `LTXVGemmaEnhancePrompt`

This node uses the same Gemma model loaded for text conditioning. It is useful when the user wants local prompt rewriting and already has the full Gemma folder under ComfyUI `models/text_encoders`.

Inputs:

- `clip`: local Gemma `CLIP` object.
- `prompt`: raw user text.
- `system_prompt`: rewrite instructions. Defaults are loaded from bundled T2V/I2V system prompts.
- `max_tokens`: output-token limit; default `512`, allowed `32` to `1024`.
- `bypass_i2v`: when `true`, ignore the image input and force T2V rewriting.
- optional `image`: image tensor for I2V prompt enhancement.
- optional `seed`: generation seed; default `42`.

Behavior to preserve:

- With no image, it rewrites as T2V.
- With an image and `bypass_i2v=false`, it rewrites as I2V and uses the image processor.
- If the user left the default T2V system prompt connected and then adds an image, the node auto-switches to the default I2V system prompt.
- The node cleans common curly quote/dash/nonbreaking-space characters from generated text.
- For generation stability, internal input padding is left-aligned and padded to an alignment multiple before Gemma generation.

Failure to load the processor is the main gotcha. The text encoder may still load, but image-aware prompt enhancement is unavailable unless the Gemma folder includes `chat_template.json`, `processor_config.json`, and `preprocessor_config.json` beside `config.json` and tokenizer files.

## `LTXVPromptEnhancerLoader`

This loader creates a `LTXV_PROMPT_ENHANCER` model patcher from a separate LLM and image captioner. Source-backed defaults are:

- LLM: `unsloth/Llama-3.2-3B-Instruct`
- image captioner: `MiaoshouAI/Florence-2-large-PromptGen-v2.0`

The loader stores downloaded snapshots under ComfyUI `models/LLM/<repository-name>`. If a target cache folder does not exist, it calls Hugging Face snapshot download. If the download fails, the partial folder is removed before the error is re-raised.

Operational cautions:

- Ask before allowing first-use downloads in noninteractive or budget-sensitive runs.
- Confirm network access and any Hugging Face access/terms requirements before using private/gated alternatives.
- The image captioner is loaded with remote-code trust enabled, so only use trusted model names.
- The enhancer estimates memory as both model sizes plus about 1 GiB and asks ComfyUI to free/load GPU memory before enhancement.

## `LTXVPromptEnhancer`

This node consumes the loaded `prompt_enhancer` and returns a string.

Inputs:

- `prompt`: raw text or prompt text to improve.
- `prompt_enhancer`: output from `LTXVPromptEnhancerLoader`.
- `max_resulting_tokens`: default `256`, allowed `32` to `512`.
- optional `image_prompt`: image tensor; if present, the node extracts first-frame conditioning for image captioning.

Behavior:

- Text-only path uses the LLM with a cinematic T2V system prompt.
- Image path first captions the image and then asks the LLM to produce an I2V-style prompt aligned with that caption.
- The utility appends one random scene-style sentence to decoded prompts, so outputs can differ even with identical text if generation/model behavior differs.
- The optional image path expects the number of first frames to match the number of prompts; a mismatch raises an assertion.

## Choosing an enhancer

Prefer `LTXVGemmaEnhancePrompt` when:

- the workflow already loads local Gemma;
- prompts should stay local/offline;
- the user wants the repo's T2V/I2V system-prompt behavior;
- the Gemma processor files are complete.

Prefer `LTXVPromptEnhancerLoader` + `LTXVPromptEnhancer` when:

- the user wants prompt rewriting without relying on Gemma prompt generation;
- separate LLM/captioner downloads are acceptable;
- optional image captioning is desired before text encoding;
- the result should be reused by either local or API encoding.

Prefer `GemmaAPITextEncode` with `enhance_prompt=true` when:

- external API use is acceptable;
- no local Gemma folder is available;
- the user wants a single node that both enhances and encodes.

## Prompt hygiene before encoding

- Keep the user's required content intact; enhancement should expand style, motion, camera, environment, and audio details rather than change intent.
- For I2V, describe changes from the reference image and avoid introducing scene cuts unless the user explicitly requests them.
- For speech or audio-capable LTX-2.3/LTX-2.5 workflows, include exact quoted words only when speech is requested; otherwise describe ambient sound and effects naturally.
- Negative prompts usually need concise exclusion terms, not elaborate cinematic prose. Avoid enhancing negatives unless the target workflow has proven that behavior.
- Save the enhanced prompt text externally if reproducibility matters; enhancer outputs are strings, not the saved conditioning artifacts covered in [conditioning artifacts](conditioning-artifacts.md).

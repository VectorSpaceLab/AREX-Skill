# Conversation and Image Formatting

## When to read

Read this when the output looks malformed, the wrong template was chosen, or the worker complains about image-token or image-count mismatches.

## Image token rules

- LLaVA uses `<image>` as the canonical multimodal placeholder.
- For some model configurations, the token is wrapped with `<im_start>` and `<im_end>`.
- The package inserts the image token into the first user turn when needed.
- In worker flows, the number of provided images must match the number of `<image>` tokens in the final prompt.

## Prompt construction patterns

### `run_llava`

- Read the image.
- Build the conversation template from the model family.
- Prepend the image token to the first user message.
- Generate until the stop string.

### Serving worker

- The Gradio UI stores chat state and images.
- The controller routes a request to a registered worker.
- The worker preprocesses the images with the model's image processor, then calls `model.generate`.

## Aspect ratio behavior

`process_images` and the conversation image utilities honor model config fields such as `image_aspect_ratio`:

| Value | Behavior |
| --- | --- |
| `pad` | Pad to square using the image processor mean before preprocessing |
| `anyres` | Use any-resolution processing with grid pinpoints |
| other / default | Use the processor's normal resize/preprocess behavior |

## Choosing a conversation mode

The auto-selection logic uses the model name. A practical reading table is:

| Name contains | Default mode |
| --- | --- |
| `llama-2` | `llava_llama_2` |
| `mistral` | `mistral_instruct` |
| `v1.6-34b` | `chatml_direct` |
| `v1` | `llava_v1` |
| `mpt` | `mpt` |
| otherwise | `llava_v0` |

If the user supplies `--conv-mode`, use it intentionally and explain when it overrides the auto-detected mode.

## URL versus file image inputs

`run_llava` accepts both URLs and local files. For serving flows, the UI image is already loaded as a PIL object and should not be treated like a URL.

## Why image mismatch errors happen

Likely causes:

- prompt has more or fewer `<image>` placeholders than actual images
- model config expects start/end tokens and the prompt omitted them
- the worker received a wrong `images` list from the caller
- the user reused a prompt designed for a different conversation mode

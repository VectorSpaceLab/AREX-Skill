# Gemma Conditioning

Use this reference to choose between local Gemma text encoding and the API text-encoding node, and to fix the common file-placement errors before touching sampler wiring. For install/backend prerequisites, see the root [model and backend requirements](../../../references/model-and-backend-requirements.md).

## Local Gemma CLIP loader

`LTXVGemmaCLIPModelLoader` creates a ComfyUI `CLIP` object for LTX-2 conditioning. It has three required inputs:

- `gemma_path`: a selectable file under ComfyUI `models/text_encoders`.
- `ltxv_path`: an LTX checkpoint under ComfyUI `models/checkpoints`.
- `max_length`: token length for Gemma tokenization. The node default is `1024`; the accepted range is `16` to `131072` in steps of `8`.

The loader resolves the Gemma model directory as the parent directory of the selected `gemma_path`. Therefore the full Gemma repository contents must live together in one folder, for example:

```text
<ComfyUI>/models/text_encoders/gemma-3-12b-it-qat-q4_0-unquantized/
  config.json
  tokenizer.json or tokenizer.model
  tokenizer_config.json
  model weights and index files
  processor_config.json
  preprocessor_config.json
  chat_template.json
  any other files shipped with the Gemma model repository
```

The repo README specifically expects the Gemma text encoder files under ComfyUI `models/text_encoders/gemma-3-12b-it-qat-q4_0-unquantized`. The exact folder name can differ, but it must be a complete local Gemma model directory.

### Local-files behavior

The local loader uses offline-style `local_files_only=True` calls for tokenizer, model, and image processor loading. It does **not** download missing Gemma files. If a file is absent, repair the ComfyUI model folder rather than expecting the node to fetch it.

The first hard gate is `config.json` at the Gemma model folder root. If the selected file's parent folder lacks `config.json`, the node raises:

```text
No config.json found for the selected Gemma model (...). Ensure the model's config, tokenizer and processor files are present.
```

Action:

1. Put the full Gemma repository contents in one folder under `models/text_encoders`.
2. In the node, select a file from inside that complete folder, not a bare file placed directly in `models/text_encoders`.
3. Confirm tokenizer files are beside `config.json`.
4. If Gemma prompt enhancement is needed, also confirm processor and chat-template files are present.

### What the loader combines

The Gemma model produces hidden states. The node then loads the LTX text-embedding projection/connectors from the selected LTX checkpoint and builds a compatible embedding pipeline:

- video-only checkpoints produce video text embeddings;
- audio-video checkpoints can produce both video and audio text embeddings;
- newer dual-aggregate checkpoints are validated against expected projection settings;
- older checkpoints may use a standalone `proj_linear.safetensors` fallback if the projection is not stored in the LTX checkpoint.

Practical implication: choose the `ltxv_path` that matches the downstream LTX model family. A prompt encoder built against the wrong checkpoint family can fail during projection loading or produce conditioning that does not match the sampler/model graph.

### `max_length` tradeoffs

`max_length` is passed to the tokenizer as `model_max_length`, and tokenization pads to exactly that length with truncation enabled. Gemma chat-style prompts are left-padded; plain text is less sensitive but still uses the configured maximum. Use the default `1024` unless the workflow has a strong reason to handle unusually long prompts. Larger values increase memory and latency and can mask prompt truncation problems because every prompt is padded to the selected length.

## Gemma prompt enhancement with the local loader

`LTXVGemmaEnhancePrompt` consumes the local `CLIP`, loads the underlying Gemma model, and returns an enhanced prompt string. It does not return `CONDITIONING`.

Required inputs:

- `clip`: output of the local Gemma loader or a compatible Gemma CLIP object.
- `prompt`: raw user prompt.
- `system_prompt`: rewrite policy text. The node ships defaults for T2V and I2V prompt styles.
- `max_tokens`: generated rewrite length; default `512`, range `32` to `1024`.
- `bypass_i2v`: when `false`, an attached `image` switches to image-to-video enhancement.

Optional inputs:

- `image`: ComfyUI image tensor for I2V prompt enhancement.
- `seed`: generation seed; default `42`.

If an image is provided and `bypass_i2v` is `false`, the node uses image-to-video mode and auto-selects the I2V system prompt when the default T2V system prompt is still present. If no image is connected, or `bypass_i2v` is `true`, it uses T2V mode.

Processor files matter here. The local loader can still create a text encoder when the image processor is unavailable, but Gemma prompt enhancement later raises:

```text
Processor not loaded - enhancement not available. Ensure your model directory has chat_template.json, processor_config.json, and preprocessor_config.json files.
```

Action: add the missing processor/chat-template files to the same Gemma model folder, then restart or reload ComfyUI so the model list and cached loader state are refreshed.

## API text encoding

`GemmaAPITextEncode` replaces the local CLIP text-encoding step. It sends a prompt to the LTX Video API and returns `CONDITIONING` directly.

Required inputs:

- `api_key`: bearer credential for the LTX Video API.
- `prompt`: text to encode; empty or whitespace-only text is rejected.
- `enhance_prompt`: boolean; when enabled, the API performs Gemma 3 prompt enhancement before encoding.
- `ckpt_name`: a model file selected from ComfyUI `models/checkpoints` or `models/diffusion_models`.

The node reads `ckpt_name` with safetensors and extracts the model id from metadata key `encrypted_wandb_properties`. If the selected file lacks that metadata, it raises:

```text
Model ID cannot be identified from the provided model file
```

Action: choose an LTX checkpoint/diffusion model file that carries the LTX API model metadata. A random converted or stripped safetensors file may run locally but still be unusable for API encoding.

Other source-backed errors:

```text
API key is required
Text prompt cannot be empty
Model path is required
Invalid API key. Please generate a new API key at the LTX Video console.
API request failed with status <code>: <body>
```

The source wraps request errors with an update hint. After confirming credentials, network access, and checkpoint metadata, update ComfyUI-LTXVideo if the API contract appears stale.

## Local vs API decision table

| Requirement | Prefer local `LTXVGemmaCLIPModelLoader` | Prefer `GemmaAPITextEncode` |
| --- | --- | --- |
| Offline/private prompt handling | Yes; no prompt leaves the machine after model files are installed | No; prompt and model id are sent to an external service |
| Avoid large Gemma local model files | No; full local Gemma folder is required | Yes; still needs checkpoint metadata and credentials |
| Output type | `CLIP`, used by downstream text encode/enhance nodes | `CONDITIONING` directly |
| Positive/negative prompts | Encode via local CLIP path as the graph expects | Use separate API encode nodes for positive and negative conditioning |
| Missing files | Repair `models/text_encoders` folder | Repair API key, network, and checkpoint metadata |
| Prompt enhancement | Local Gemma enhancement requires processor files | API has `enhance_prompt` switch |

## Practical wiring patterns

### Local Gemma text path

1. Place the full Gemma model folder under ComfyUI `models/text_encoders`.
2. Place the LTX checkpoint under ComfyUI `models/checkpoints`.
3. Load `LTXVGemmaCLIPModelLoader` with the Gemma file, matching LTX checkpoint, and `max_length`.
4. Use the returned `CLIP` wherever the workflow expects text encoding or Gemma prompt enhancement.
5. Keep positive and negative conditioning consistent: same Gemma/LTX pair, different prompt text.

### API conditioning path

1. Put an LTX checkpoint or diffusion model with preserved metadata in ComfyUI `models/checkpoints` or `models/diffusion_models`.
2. Add one `GemmaAPITextEncode` for the positive prompt and one for the negative prompt if the graph expects both.
3. Set the same `ckpt_name` on both unless the workflow intentionally compares model families.
4. Enable `enhance_prompt` only where desired; negative prompts usually remain literal unless the workflow deliberately enhances them.
5. Connect returned `CONDITIONING` directly to guider/sampler nodes; do not feed it into CLIP text encoders.

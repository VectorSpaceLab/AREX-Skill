# Model Inference Troubleshooting

Use this reference when a plan is blocked by environment, prompt-shape, or backend mismatches. It is written for planning and diagnosis, not for running the model in this session.

## CUDA, VRAM, and dtype issues

### Symptom: the model does not fit on one GPU

Likely causes:

- the chosen model family is too large for the available VRAM;
- `hd_num` is too high for a high-resolution image or document task;
- a long video or many images inflate the visual-token budget;
- KV cache is large because `max_new_tokens`, `session-len`, or `cache_max_entry_count` are too aggressive.

Planning fixes:

- switch from Transformers to LMDeploy for accelerated/low-memory plans;
- use the corresponding 4-bit/AWQ checkpoint when available;
- lower `hd_num` for multi-image or document-heavy prompts;
- lower `cache_max_entry_count` in LMDeploy;
- split the model across multiple GPUs with `dispatch_model` when the checkpoint supports it.

### Symptom: dtype or autocast confusion

The source README shows bf16 checkpoint loading followed by `.half()` and `torch.autocast(..., dtype=torch.float16)` in examples.

Planning fixes:

- choose one execution dtype intentionally for the target GPU family;
- use bf16 only when the GPU and runtime support it well;
- prefer fp16 on more common consumer CUDA cards;
- do not mix bf16 checkpoint loading with an unreviewed fp32 fallback in the same execution plan.

## `trust_remote_code` and API mismatch issues

### Symptom: `chat` or composition methods are missing

Likely cause: the checkpoint was loaded without `trust_remote_code=True` or a legacy model family was used with a current-2.5 snippet.

Planning fixes:

- always include `trust_remote_code=True` in the planned Transformers load;
- verify whether the target is current 2.5, legacy 2.0, legacy 1.0, or OmniLive base;
- keep `write_webpage`, `resume_2_webpage`, `screen_2_webpage`, and `write_artical` only for the current 2.5 model code.

### Symptom: `write_article` fails

Likely cause: the source method is spelled `write_artical`.

Planning fix: use the misspelled source API name in every runnable example.

## Prompt and placeholder issues

### Symptom: output ignores some images or the model warns about placeholder count

Likely causes:

- the prompt has fewer `<ImageHere>` placeholders than images;
- the images are passed in the wrong order;
- single-image mode was used for a multi-image task;
- the prompt text and image count disagree after a renderer or copy/paste step.

Planning fixes:

- count images and placeholders together before execution;
- for multi-image chat, write one `<ImageHere>` per image and keep explicit labels such as `Image1`, `Image2`, etc.;
- for single-image tasks, keep the prompt simple and let the model inject the placeholder if the source code does so automatically;
- use the bundled renderer helper to validate the count before a user runs anything.

### Symptom: the video prompt does not behave like the image prompt

Likely cause: the current code treats the video as a visual input path and samples frames internally.

Planning fixes:

- pass the video path in the list form used by the source examples;
- keep the wording aligned with a video-description task;
- confirm Decord/video-codec support before execution.

## `hd_num` and high-resolution issues

### Symptom: document, chart, or 4K-style analysis is fuzzy or truncated

Likely causes:

- `hd_num` is too low for the image complexity;
- the wrong model family is being used for 4KHD-era behavior;
- the plan is trying to use legacy 1.0/2.0 defaults for current 2.5 tasks.

Planning fixes:

- increase `hd_num` for single-image high-resolution analysis;
- keep `hd_num` modest for multi-image prompts;
- if the user explicitly wants 2.0 4KHD behavior, use the 2.0 legacy branch and its documented `hd_num=55` style.

## LMDeploy and 4-bit/AWQ issues

### Symptom: LMDeploy installation fails or the runtime cannot import the expected wheel

Likely cause: the installed LMDeploy wheel targets a different CUDA family than the host.

Planning fixes:

- note that the source docs say the default LMDeploy package targets CUDA 12.x;
- treat CUDA 11.x as a special compatibility path requiring the LMDeploy installation guide;
- verify the model id matches the 4-bit/AWQ checkpoint before planning an `awq` backend.

### Symptom: AWQ plan uses the wrong checkpoint

Likely cause: the checkpoint id is the FP16 model, not the 4-bit model.

Planning fix: pair `model_format='awq'` only with `internlm/internlm-xcomposer2d5-7b-4bit` or the corresponding local 4-bit folder.

## Gradio issues

### Symptom: the app opens but resources look stale or files land in the wrong temp directory

Likely cause: the demo sets `GRADIO_TEMP_DIR` to a repo-local `tmp/` folder, and browser cache or temp cleanup expectations may differ from the user's environment.

Planning fixes:

- mention the temp directory in the plan if the user expects browser-uploaded files to persist;
- confirm where generated HTML and article files are written;
- keep `server_name`, `server_port`, and `share` policy explicit.

### Symptom: the user expects a local-only demo but the plan shares publicly

Likely cause: the chat demo launches with `share=True` by default.

Planning fix: switch to a private or loopback-only plan if the user does not want a public share link.

### Symptom: composition image search fails

Likely causes:

- the external caption-search service is unavailable;
- network access is blocked;
- requests are being intercepted by a proxy.

Planning fixes:

- plan a fallback that does not depend on remote image search;
- document any proxy or firewall assumptions;
- treat the image-search helper as optional rather than guaranteed.

## Generated HTML and file-output issues

### Symptom: webpage generation appears to do nothing

Likely cause: the model may have generated HTML text, but the plan did not mention the file write location or the working directory.

Planning fixes:

- explicitly state that `write_webpage`, `resume_2_webpage`, and `screen_2_webpage` write `.html` files into the current directory;
- set a dedicated output folder in the plan when possible;
- remember that `resume_2_webpage` reads a Markdown resume from disk before generation.

### Symptom: the user cannot find the article output

Likely cause: `write_artical` returns text rather than a file in the source examples.

Planning fix: say whether the downstream script should print the article, save it, or both.

## Legacy compatibility issues

### Symptom: a legacy 1.0 or 2.0 snippet fails with a current-2.5 prompt shape

Likely causes:

- `model.generate(text)` was used for a current 2.5 VLM task;
- `hd_num` or `interleav_wrap_chat` assumptions came from a different model family;
- the device-map keys no longer match the checkpoint.

Planning fix: keep legacy 1.0/2.0 snippets separate from current 2.5 snippets and note the model family explicitly in every plan.

## Fast blocker checklist

If a request is still blocked after planning, check these in order:

1. Exact model family and checkpoint id.
2. GPU count, VRAM, dtype, and CUDA version.
3. `trust_remote_code=True` and matching API shape.
4. Image/video placeholder count.
5. `hd_num`, `max_new_tokens`, and LMDeploy cache settings.
6. Gradio `share` policy and port choice.
7. Output file location for HTML/article tasks.

# Troubleshooting Modalities, Adapters, and Pooling

Use this checklist when vLLM errors involve media loading, multimodal processor kwargs, LoRA adapters, pooling tasks, or output shapes.

## Local file refused

Likely signals:

- `Cannot load local files without --allowed-local-media-path`
- `must be a subpath of --allowed-local-media-path`
- Server rejects `file://...` media in an OpenAI payload.

Fix:

1. Put files under a narrow deployment media directory.
2. Start the server with `--allowed-local-media-path <media-root>` or pass `allowed_local_media_path` to `LLM(...)`.
3. Use `file://` URLs that resolve under that directory, or load files as Python objects in offline code.
4. Run the static validator:

   ```bash
   python scripts/validate_multimodal_payload.py payload.json \
     --allowed-local-media-path /srv/vllm-media
   ```

Do not work around this by allowing `/` in production unless the deployment is fully isolated and trusted.

## Remote media domain refused

Likely signal:

- `The URL must be from one of the allowed domains: ... Input URL domain: ...`

Fix:

1. Add only the required hostnames to `--allowed-media-domains` or `allowed_media_domains=[...]`.
2. Avoid wildcard-like broad allowlists.
3. Prefer stable CDN/object-storage domains.
4. Disable media URL redirects in the deployment environment when domain allowlists are security boundaries.

## Payload content shape wrong

Likely signals:

- OpenAI request with media has `content` as a string instead of a list of parts.
- A content part lacks `type`.
- `image_url` is a string in some client payloads but the server expects an object with `url`, or vice versa for the specific endpoint/client.
- Offline `multi_modal_data` count does not match prompt placeholders.

Fix:

- Chat/OpenAI: use `messages[].content` as a list of `{type, ...}` parts when media is present.
- Offline generation: use `{ "prompt": ..., "multi_modal_data": {"image": image_or_list} }`.
- Score/rerank multimodal: use `{"content": [parts...]}` without chat `role` fields for offline score inputs.
- Match `limit_mm_per_prompt` to the actual media count.

## Missing `mm_processor_kwargs` or media metadata

Likely signals:

- Errors mentioning max pixels, frame counts, video metadata, audio sampling, missing metadata, or processor-specific kwargs.
- Good payload shape but model processor rejects dimensions or media count.

Fix:

1. Check the model card for expected processor kwargs, image/video size limits, frame sampling, and audio format.
2. Pass `mm_processor_kwargs={...}` at `LLM(...)` construction when supported.
3. For images with transparency, set `media_io_kwargs={"image": {"rgba_background_color": [R, G, B]}}` if RGB conversion matters.
4. For video/audio arrays, include metadata or sample rate when the processor expects it.

## LoRA ID/path mismatch

Likely signals:

- Server request uses base model ID but expects adapter output.
- Offline request reuses one `lora_int_id` for different adapter paths.
- Dynamic load says success for one name but client requests another model name.

Fix:

- Offline: `LoRARequest("name", unique_int_id, "/adapter/path")` and pass it on the request.
- Server static: request `model` must equal the `--lora-modules` adapter name.
- Dynamic: `lora_name` in the load request must match later request `model`.
- Keep a small adapter registry in application code mapping adapter names to IDs and paths.

## LoRA rank or target incompatibility

Likely signals:

- `max_lora_rank` errors.
- Target modules are unsupported or missing.
- MoE/fully sharded adapter shape or rank divisibility errors.

Fix:

1. Increase `max_lora_rank` to cover the adapter's rank.
2. Ensure adapter `target_modules` match vLLM-supported wrapped modules for the base model.
3. Verify the adapter was trained for the same base model/revision and hidden size.
4. For MoE adapters, confirm 2D/3D layout flags and tensor/expert parallel divisibility.
5. Reduce concurrency or raise `max_loras` when the error is adapter slot exhaustion.

## Pooling endpoint or API confusion

Likely signals:

- `LLM.encode() is only supported for pooling models. Try passing --runner pooling`
- `pooling_task required for LLM.encode`
- `Embedding API is not supported by this model. Try converting the model using --convert embed`
- `Classification API is not supported by this model. Try converting the model using --convert classify`
- Online route returns `The model does not support ... API`.

Fix:

1. Use `runner="pooling"` for offline pooling.
2. Prefer the specialized method: `embed`, `classify`, or `score`.
3. Use `encode(..., pooling_task="token_embed" | "token_classify" | "plugin" | ...)` for raw/token/plugin outputs.
4. Use `/v1/embeddings` for embeddings, `/score` or `/v1/score` for scalar pair scores, and `/rerank`/`/v1/rerank`/`/v2/rerank` for ranked documents.
5. Convert/configure the model only if the architecture supports the target task.

## Embedding shape validation errors

Likely signal:

- `pooled_data should be a 1-D embedding vector`

Fix:

- Confirm the call is `LLM.embed` or `encode(pooling_task="embed")` with an embedding-compatible model.
- If using token embeddings or multi-vector retrieval, do not convert to `EmbeddingOutput`; consume `PoolingRequestOutput.outputs.data` and document its rank.

## Classification shape validation errors

Likely signal:

- `pooled_data should be a 1-D probability vector`

Fix:

- Confirm the model has a classification head or was converted/configured for classification.
- If output is token classification, use token-specific handling rather than `LLM.classify` conversion.

## Scoring shape validation errors

Likely signal:

- `pooled_data should be a scalar score`

Fix:

- Confirm the model is a scalar scorer/reranker, commonly with one label for cross-encoder scoring.
- Do not use an embedding model's vector output as a score without an explicit similarity calculation.
- For rerank, use the rerank endpoint or score API post-processing, not `embed` output extraction.

## Hard usability cases to test

- Local-file OpenAI payload: a request contains `file:///tmp/image.png` and no `--allowed-local-media-path`; the correct answer identifies the safety block, proposes a narrow allowlist root, and uses the validator without downloading media.
- Mixed pooling outputs: a user uses `LLM.embed` for reranking and then reads `outputs[0].outputs.score`; the correct answer switches to `LLM.score` or `/rerank`, explains scalar vs vector outputs, and validates extraction paths.

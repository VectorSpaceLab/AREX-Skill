---
name: modalities-adapters-pooling
description: "Handle vLLM multimodal payloads, media allowlists, LoRA/prompt
  adapters, pooling/embedding/classification/rerank/score/token outputs, and
  model/output compatibility checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# vLLM Modalities, Adapters, and Pooling

Use this sub-skill when a task involves multimodal inputs, image/audio/video payloads, media safety limits, LoRA adapters, pooling runners, embeddings, classification, rerank/score APIs, token-level pooling outputs, or validating output shapes.

## Route by task

- **Multimodal payloads and media safety**: read [references/multimodal.md](references/multimodal.md) for offline `multi_modal_data`, OpenAI/chat content parts, `allowed_local_media_path`, `allowed_media_domains`, media limits, and `mm_processor_kwargs`.
- **LoRA adapters and resolvers**: read [references/lora.md](references/lora.md) for `LoRARequest`, `--enable-lora`, `--lora-modules`, runtime loading, resolver plugins, rank/target checks, and adapter/model ID mismatches.
- **Pooling APIs and outputs**: read [references/pooling.md](references/pooling.md) for `runner="pooling"`, `LLM.embed`, `LLM.classify`, `LLM.score`, `LLM.encode`, OpenAI-compatible `/v1/embeddings`, `/score`, `/rerank`, and output shape expectations.
- **Failure diagnosis**: read [references/troubleshooting.md](references/troubleshooting.md) when errors mention local files, domains, malformed media content, missing processor kwargs, LoRA rank/targets, unsupported pooling tasks, or output conversion shape errors.

## Fast checks

1. Confirm the model supports the requested modality/task before writing code. Multimodal generation, pooling, classification, token embedding, rerank, and score are model-dependent and often require `trust_remote_code`, templates, or conversion flags.
2. For local or remote media in server/OpenAI flows, inspect the request before running a server:

   ```bash
   python scripts/validate_multimodal_payload.py request.json \
     --allowed-local-media-path /srv/media \
     --allowed-media-domain upload.wikimedia.org
   ```

3. Keep offline generation responsibilities separate from pooling responsibilities. Route general `LLM.generate`/`SamplingParams` basics to the root/offline inference skill; use this sub-skill only for multimodal, adapter, and pooling-specific decisions.
4. Treat GPU execution, model downloads, and live server calls as user-provided and hardware-gated. The bundled validator performs static JSON inspection only and does not download media.

## Minimal decision table

| If the user asks for | Prefer | Key extraction |
| --- | --- | --- |
| Caption/question over images/video/audio | Multimodal generation | `outputs[0].outputs[0].text` |
| Text/image embedding vector | Pooling embed | `outputs[0].outputs.embedding` |
| Class probabilities/logits | Pooling classify | `outputs[0].outputs.probs` |
| Pair similarity | Score API | `outputs[0].outputs.score` offline or `data[].score` online |
| Ranked documents | Rerank API | `results[].index`, `results[].relevance_score` |
| Per-token labels/vectors/rewards | Token pooling task | inspect `PoolingRequestOutput.outputs.data` shape before converting |
| Adapter-specific generation/pooling | LoRA | `LoRARequest(name, int_id, path)` offline or request `model=<adapter-name>` online |

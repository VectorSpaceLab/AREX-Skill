# Model-development troubleshooting

Use this matrix before sending a model problem to evaluation. It is distilled from `README.md`, `docs/en/Quickstart.md`, `docs/en/EvalByLMDeploy.md`, `run.py`, `vlmeval/vlm/base.py`, `vlmeval/api/base.py`, `vlmeval/api/litellm_api.py`, `vlmeval/api/lmdeploy.py`, `vlmeval/api/openai_sdk.py`, `vlmeval/api/adapters/base.py`, and `tests/test_litellm_api.py`.

## Important verification boundary

Creation-time checks covered import/signature probes, `LiteLLMAPI`, `APIEvalPipeline`, `build_dataset`, `supported_VLM` discovery, `run.py --help`, `vlmutil dlist`, native mocked LiteLLM/API pipeline tests, and a torch CUDA smoke probe. They did **not** verify live API calls, dataset downloads, Gradio services, LMDeploy/VLLM server availability, or large local model evaluations.

## Quick diagnosis matrix

| Symptom | Likely cause | What to check or change |
| --- | --- | --- |
| `Model "X" not found in supported_VLM` | Typo, unregistered model, or API endpoint should use `--base-url`. | Run `vlmutil mlist all`; use exact key, JSON `--config`, or `run.py --base-url`. |
| JSON config says class unsupported | Class is not exported from `vlmeval.api` or `vlmeval.vlm`. | Add the import and `__all__` entry in the relevant `__init__.py`, or change `class` to an exported name. |
| `LiteLLM is required for LiteLLMAPI` | Optional LiteLLM package missing. | Install a compatible LiteLLM package for the current environment, then re-run only a construction/mock smoke before live calls. |
| LiteLLM call omits credentials | `key` and `LITELLM_API_KEY` are unset, or provider expects a provider-specific env var. | Pass `key=...` for providers that support it or set the provider credential environment expected by LiteLLM. Do not hard-code credentials in `config.py`. |
| LiteLLM uses wrong proxy/base | `api_base` or `LITELLM_API_BASE` is wrong. | Pass `api_base=` or set `LITELLM_API_BASE`; verify the provider expects that shape. |
| LiteLLM returns `Failed to obtain answer via API.` | Provider exception caught and returned with ret code `-1`. | Set `verbose=True`, inspect the log string returned by `generate_inner()`, and reduce to a text-only prompt before image/video debugging. |
| `--base-url` endpoint returns 404 or double path | Passed full `/chat/completions` URL to `--base-url`. | For `run.py --base-url`, pass the API root such as `http://host:port/v1`; `run.py` appends `/chat/completions`. For `LMDEPLOY_API_BASE` or config kwargs, use the full endpoint expected by `LMDeployAPI`. |
| LMDeploy wrapper asserts missing base | `api_base` and `LMDEPLOY_API_BASE` are unset. | Provide `--base-url` via `run.py`, `api_base` in JSON/config, or `LMDEPLOY_API_BASE` for direct `LMDeployAPI` construction. |
| LMDeploy wrapper asserts missing key | `key` and `LMDEPLOY_API_KEY` are unset for direct construction. | Provide a key value through CLI/config/env that is accepted by the server. Avoid copying example credentials into reusable config. |
| Local service cannot read images/videos | Media was sent as local `file://` paths to a service that cannot access the same filesystem. | Disable `--local-media` so base64 data URLs are sent, or run the service where those file paths are accessible. |
| Payload too large with base64 media | Large images/videos are encoded inline. | Use provider-side local media only when safe, reduce image size where supported, or use a dataset/frame strategy routed through evaluation. |
| `Invalid input type` assertion | Message dict lacks `type`/`value`, or the parsed media MIME conflicts with declared type. | Use VLMEvalKit message dicts with `text`, `image`, or `video`; ensure file extension/content matches the type. |
| Non-interleaved model ignores later images | `INTERLEAVE=False` and `message_to_promptimg()` uses first image except BLINK concat behavior. | Set `INTERLEAVE=True` only if the wrapper can actually preserve interleaving, or implement explicit multi-image handling in `generate_inner()`. |
| Video prompt fails with unsupported-video error | Wrapper lacks `VIDEO_LLM=True` or does not implement video handling. | Use `message_to_promptvideo()` only for native video models; otherwise rely on frame-based video dataset flow routed through evaluation/benchmark authoring. |
| `chat()` fails or returns fallback after dropped turns | Missing or brittle `chat_inner()`, invalid role order, or context too long. | Ensure role-keyed turns alternate and last role is `user`; implement `chat_inner()` only for true multi-turn support. |
| Custom prompt not applied | `use_custom_prompt(dataset)` returned `False`, adapter not selected, or dataset name/type branch does not match. | Check `--custom-prompt`/`custom_prompt`, `build_adapter()` registry, and `use_custom_prompt()` branches for the exact dataset name. |
| Adapter name not found | Module not imported into `vlmeval/api/adapters/__init__.py` or name typo. | Import the adapter module/class in `__init__.py`; call `get_adapter_registry()` to inspect names. |
| Adapter modifies wrong layer | HTTP payload changes were attempted in `build_prompt()` or internal message changes in `process_payload()`. | Keep `build_prompt()` and `process_inputs()` on VLMEvalKit messages; keep provider JSON edits in `process_payload()`. |
| Thinking text breaks exact matching | Model returns `<think>...</think>` content before the final answer. | Use `SPLIT_THINK=True` when preserving thinking in prediction records, or adapter `postprocess()` when the answer returned to evaluators should exclude thinking. Avoid double-stripping. |
| No `thinking` field appears | `SPLIT_THINK` not enabled, or adapter already stripped thinking. | Decide whether splitting belongs to `vlmeval/inference.py` or adapter `postprocess()`; do not expect both outputs simultaneously. |
| API mode refuses multi-process | `WORLD_SIZE > 1` with `--api-mode`. | Run API mode in a single process; use API concurrency settings instead of `torchrun` multi-process. |
| Local model device split is surprising | `run.py` divides visible GPUs across `LOCAL_WORLD_SIZE`, and model build temporarily hides `WORLD_SIZE` to avoid some device-map issues. | Check `CUDA_VISIBLE_DEVICES`, `RANK`, `LOCAL_RANK`, `WORLD_SIZE`, and `LOCAL_WORLD_SIZE`; prefer `python run.py` for huge models that need all visible GPUs. |
| Torchrun with `device_map='auto'` fails on newer transformers | WORLD_SIZE/device-map interaction noted in inference code comments. | Use the current `run.py`/inference wrappers that hide `WORLD_SIZE` during model construction; if editing wrappers, preserve that behavior. |
| Import/runtime failure in local model family | Incompatible `transformers`, `torchvision`, `flash-attn`, CUDA, or model-specific optional package. | Consult README compatibility recommendations for the model family; change only the minimal dependency set required for that wrapper. |
| Model scores differ from leaderboard | Environment, dependency versions, CUDA/torch, prompt policy, and answer extraction mode differ. | Inspect prediction records and prompt construction first; do not assume wrapper correctness from scores alone. |

## Dependency compatibility reminders

- README gives model-family-specific `transformers` recommendations. Follow the family guidance rather than upgrading blindly.
- Moondream series and Aria call out `torchvision>=0.16`.
- Aria calls out `flash-attn` installation with `--no-build-isolation`.
- LiteLLM is optional and mocked in native tests; install it only for LiteLLM provider usage.
- LMDeploy, VLLM, decord, Gradio, model weights, and provider SDKs are optional for this sub-skill unless the task explicitly needs them.

## Safe reduction steps

1. Reduce to construction/import: import the class and print its signature.
2. Reduce to registry: verify the alias appears in `supported_VLM` or JSON config resolves to an exported class.
3. Reduce to text-only input: call the provider wrapper with a single text message when safe.
4. Add one image: verify PIL can open the file and the provider accepts `image_url` payloads.
5. Add custom prompt: confirm adapter registry name, `use_custom_prompt()` result, and output message order.
6. Add video/native media only after the endpoint/model documents support for `video_url` or `VIDEO_LLM`.
7. Only then route to evaluation for dataset/job behavior.

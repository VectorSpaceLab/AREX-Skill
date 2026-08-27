# Offline Inference Troubleshooting

Use this guide when a Python offline vLLM script imports but gives confusing outputs, API errors, or runtime failures.

## Raw Chat Messages Passed to `generate`

Symptom examples:

- Code passes `[{"role": "user", "content": "..."}]` into `llm.generate`.
- Output quality looks like the model saw Python/dict text instead of a chat prompt.
- Type validation complains about prompt format.

Fix:

- Use `llm.chat(messages, sampling_params=params)` for offline chat.
- Or manually apply the tokenizer chat template with `add_generation_prompt=True` and pass the resulting strings to `generate`.
- Remember that `generate` does not auto-apply chat templates.

## Missing or Wrong Chat Template

Symptom examples:

- `llm.chat` fails with a missing chat template error.
- Chat output includes role markers incorrectly or ignores system/user roles.

Fix:

- Prefer a chat/instruct model whose tokenizer provides a chat template.
- Pass `chat_template=` to `LLM(...)` or to `llm.chat(...)` when the installed API supports per-call templates.
- Keep model and tokenizer revisions aligned.
- Do not borrow a template from an unrelated model family unless the user explicitly asks and accepts behavior risk.

## Model Download, Access, or Offline Cache Failures

Symptom examples:

- Hugging Face 401/403, gated repo access, or revision not found.
- Network timeout during model load.
- Local path does not contain expected model/tokenizer files.

Fix:

- Ask the user for a valid public model id, local model path, or preconfigured gated-model access.
- Pin `revision` and `tokenizer_revision` for reproducibility.

## `trust_remote_code` Risk

Symptom examples:

- Model load asks for `trust_remote_code=True`.
- Custom model repository code is required.

Fix:

- Keep `trust_remote_code=False` by default.
- Explain that enabling it executes code from the model repository.
- Enable it only after explicit user approval and only for trusted model sources.

## GPU, CPU, Dtype, or Backend Errors

Symptom examples:

- CUDA, ROCm, Triton, XPU, or driver import/runtime errors.
- `bfloat16` or `float16` unsupported on selected hardware.
- Out-of-memory during `LLM(...)` construction.

Fix:

- Treat GPU execution as hardware-gated; import success does not prove GPU kernels work.
- Start with `dtype="auto"`; only override dtype when the user knows the target hardware supports it.
- For CPU-oriented checks, use a tiny compatible model if available and short `max_tokens`.
- Reduce memory pressure with a smaller model, lower `gpu_memory_utilization`, smaller `max_model_len` if accepted by the installed engine args, or appropriate offload settings.
- Keep deployment/performance tuning in the deployment-performance sub-skill.

## Unexpectedly Short or Long Outputs

Symptom examples:

- Output stops around a small token count.
- Smoke check returns almost nothing.
- Generation runs too long.

Fix:

- Set `SamplingParams(max_tokens=...)` explicitly; installed defaults include `max_tokens=16`.
- Inspect `finish_reason` and `stop_reason` on `output.outputs[0]`.
- Check `stop`, `stop_token_ids`, and model `generation_config.json` effects.
- Use `generation_config="vllm"` on `LLM` when supported and when the task requires vLLM defaults rather than model-recommended defaults.

## Pooling Output Extraction Confusion

Symptom examples:

- Code tries `output.outputs[0].text` after `embed`, `classify`, `score`, or `encode`.
- User asks why pooling calls return objects rather than text.

Fix:

- `embed`: use `output.outputs.embedding` and optionally `output.outputs.hidden_size`.
- `classify`: use `output.outputs.probs` and optionally `output.outputs.num_classes`.
- `score`: use `output.outputs.score`.
- `encode`: use generic pooling data at `output.outputs.data` unless a typed wrapper is returned.
- Verify the model supports the selected pooling task and construct `LLM(..., runner="pooling")` when required.

## SamplingParams Length Mismatch

Symptom examples:

- A batch of prompts is passed with a shorter or longer list of `SamplingParams`.
- Validation error mentions request count or sampling parameter count.

Fix:

- Use one `SamplingParams` instance to apply the same settings to all prompts.
- Or pass a list of `SamplingParams` exactly matching the prompt list length.

## Import or Package Availability Errors

Symptom examples:

- `ModuleNotFoundError: No module named 'vllm'`.
- CLI works in one shell but Python import fails in another.
- `pip check`/dependency conflicts after installation.

Fix:

- Ensure the Python interpreter running the script is the environment where vLLM is installed.
- Run `python -c "import vllm; print(getattr(vllm, '__version__', 'unknown'))"` in the same environment.
- Follow the project or deployment environment's installation policy; do not assume system Python is valid.

## When to Exclude a Scripted Run

Do not run the bundled smoke script against a real model when:

- The user has not supplied a model id or local path.
- The environment lacks the required hardware/backend.
- Running would download large model weights unexpectedly.
- The model requires gated access that is not already configured by the user.

In those cases, use `--print-plan` or `--skip-run` to validate the intended code path without model execution.

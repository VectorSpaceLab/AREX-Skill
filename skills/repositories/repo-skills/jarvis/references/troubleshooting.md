# JARVIS troubleshooting

## Purpose

Use this for cross-cutting JARVIS failures that span more than one subproject: package import problems, placeholder credentials, endpoint selection mistakes, path/workdir confusion, and optional backend assumptions.

## Common failure surfaces

### Missing or placeholder credentials

**Symptoms**

- `OpenAI API key` or `Hugging Face token` errors in HuggingGPT.
- EasyTool requests fail before or during API calls.
- TaskBench inference or data generation cannot contact the model endpoint.

**Likely causes**

- Placeholder values still present in config files.
- Required environment variables are unset.
- The chosen workflow needs a credential the user did not provide.

**Next step**

- Use the sub-skill's config/reference file to check which values are read from config and which can come from environment variables.
- Replace placeholders or export the required credential before retrying.
- If the user only wants inspection, use the bundled helpers instead of running the full workflow.

### HuggingGPT remote vs local confusion

**Symptoms**

- User asks for ControlNet or other local-only multimodal generation in HuggingFace-only mode.
- The server fails at startup because a local model endpoint is missing.

**Likely causes**

- `inference_mode` is `huggingface` but the task requires local ControlNet or a local model server.
- `config.default.yaml` expects local endpoint fields that do not exist in lite mode.

**Next step**

- Route to the `hugginggpt-chat` sub-skill.
- Check whether the request is remote/lite or local/hybrid before suggesting model downloads.
- Do not claim local CUDA server verification unless the user explicitly provided a verified model stack.

### EasyTool import failures

**Symptoms**

- `ModuleNotFoundError: No module named 'util'` when running `easytool/main.py`.

**Likely causes**

- The inner `easytool/` package directory is not on `PYTHONPATH`.
- The command was launched from the wrong working directory.

**Next step**

- Use the bundled EasyTool checker and the EasyTool sub-skill's path workaround.
- If the user wants a one-off help check, make sure the inner package directory is importable before running the CLI.

### TaskBench dependency-type mistakes

**Symptoms**

- Native assertion when Daily Life APIs are evaluated with the wrong dependency type.
- Graph/data tools write outputs beside the source data unexpectedly.
- Evaluation fails because predictions are malformed JSON.

**Likely causes**

- `--dependency_type resource` used for a temporal tool library.
- Using native graph/visualization scripts without explicit output paths.
- Prediction JSONL does not match the expected `result` structure.

**Next step**

- Use the `taskbench` sub-skill and its bundled validator/helper scripts.
- Fix the dependency-type selection first, then validate a tiny fixture before running evaluation.

### Web client / local endpoint issues

**Symptoms**

- Browser UI points at the wrong base URL.
- ChatGPT fallback works but JARVIS endpoint calls fail.
- Web build or dev startup complains about missing npm tooling.

**Likely causes**

- Base URL in the web client config does not match the running server.
- Frontend dependencies are not installed.

**Next step**

- Use the `hugginggpt-chat` web-client reference.
- Update the base URL in the generated skill's guidance, not in the original checkout.

### Large optional backend assumptions

**Symptoms**

- User assumes the local model-server stack is already available.
- Native model downloads or CUDA tasks would require large disk and VRAM.

**Likely causes**

- The request is really for an optional local-model path, not the remote/light workflows this skill prepared.

**Next step**

- Treat the local model-server path as optional and unverified unless the user supplies fresh runtime evidence.
- If the request truly needs it, route to the relevant sub-skill and verify hardware/artifact availability before promising success.

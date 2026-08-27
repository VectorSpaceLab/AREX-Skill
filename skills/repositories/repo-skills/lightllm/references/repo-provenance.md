# Repo provenance

- repository: LightLLM
- source_commit: `fe9bdabfc331b990124f1ec27daf6bb7945cf7ee`
- source_branch: `main`
- exact_tag: none observed
- package_version: `1.2.0`
- dirty_state: dirty checkout at generation time
- dirty_paths:
  - `skills/LightLLM.log`
- remote_url: omitted-private-or-unknown

## Evidence used to generate this skill

Relative evidence paths only; no private absolute paths are included here.

- `README.md`
- `requirements.txt`
- `setup.py`
- `lightllm/server/api_server.py`
- `lightllm/server/api_cli.py`
- `lightllm/server/api_http.py`
- `lightllm/server/api_openai.py`
- `lightllm/server/api_anthropic.py`
- `lightllm/server/api_tgi.py`
- `lightllm/server/api_models.py`
- `lightllm/server/build_prompt.py`
- `lightllm/server/function_call_parser.py`
- `lightllm/server/multimodal_params.py`
- `lightllm/models/registry.py`
- `lightllm/utils/backend_validator.py`
- `lightllm/utils/config_utils.py`
- `lightllm/utils/device_utils.py`
- `lightllm/server/core/objs/start_args_type.py`
- `docs/EN/source/getting_started/installation.rst`
- `docs/EN/source/getting_started/quickstart.rst`
- `docs/EN/source/getting_started/benchmark.rst`
- `docs/EN/source/tutorial/api_server_args.rst`
- `docs/EN/source/tutorial/api_param.rst`
- `docs/EN/source/tutorial/openai.rst`
- `docs/EN/source/tutorial/anthropic.rst`
- `docs/EN/source/tutorial/function_calling.rst`
- `docs/EN/source/tutorial/reasoning_parser.rst`
- `docs/EN/source/tutorial/multimodal.rst`
- `docs/EN/source/tutorial/reward_model.rst`
- `docs/EN/source/tutorial/fp8_kv_quantization.rst`
- `docs/EN/source/tutorial/multi_level_cache_deployment.rst`
- `docs/EN/source/cookbook/qwen35_deployment.rst`
- `docs/EN/source/cookbook/glm4_deployment.rst`
- `test/test_api/*`
- `test/benchmark/*`
- `test/acc/*`
- `test/format_out/*`
- `test/start_scripts/README.md`
- `format_out/*`
- `skills/lightllm-profiler-control/SKILL.md`
- `skills/test_model/SKILL.md`
- `skills/test_model/qwen3-8b-pd-nixl/SKILL.md`

## Refresh baseline

This skill reflects the repository state at the commit above and the installed
package inspection performed in the private environment used for drafting.
Refresh the skill if any of the following change:

- `lightllm/server/*` public API modules or request models.
- `lightllm/server/core/objs/start_args_type.py` CLI/runtime flags.
- `lightllm/models/*` registry or supported-family layout.
- `lightllm/utils/*` backend validation or environment selection logic.
- `docs/EN/source/*` public workflows and deployment docs.
- `test/*` native validation or benchmark scripts.
- `skills/*` repo-local evidence skills used as source material.

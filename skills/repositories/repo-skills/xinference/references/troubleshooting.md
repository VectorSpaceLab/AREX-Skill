# Cross-Cutting Troubleshooting

Read this when an issue appears before a workflow-specific route is clear, or
when install/import, dependency, model-source, frontend-build, or auth-header
symptoms affect several Xinference surfaces.

## Fast triage

| Symptom | Likely cause | First action | Route next |
| --- | --- | --- | --- |
| `ModuleNotFoundError: xinference` | Package not installed in the active Python environment | Run `python scripts/check_xinference_install.py`; reinstall in the selected environment | installation reference |
| Console command not found | Environment `bin`/`Scripts` directory not on `PATH` or package install failed | Run `python -m pip show xinference` and call scripts through the environment explicitly | installation reference |
| Editable install starts a frontend build | Source build backend is staging Web UI assets | Use `NO_WEB_UI=1` for Python-only inspection | installation reference |
| `ImportError` for `vllm`, `sglang`, `mlx`, `diffusers`, `sentence_transformers`, audio engines, or quantization packages | Optional extra/backend missing or incompatible with platform | Identify the selected model family/backend before installing extras | `models-and-backends` |
| Real `launch` hangs or downloads | Model weights or per-model dependencies are being fetched | Confirm model source/cache and whether network is allowed | `serving-and-cli` + `models-and-backends` |
| OpenAI SDK returns `404` | Using service root instead of `/v1` base URL, or model UID not launched | Use the snippet helper and verify endpoint vs `/v1` | `client-and-api` |
| `401`/`403` or missing API-key errors | Advanced auth is enabled and token/key is missing, expired, or wrong | Use `Authorization: Bearer <token-or-api-key>` and check auth policy | `operations-and-security` |
| Web UI static files not found | Custom frontend dist path is wrong or source build skipped assets | Check `XINFERENCE_FRONTEND_DIST_DIR` or install/build assets intentionally | `operations-and-security` |
| Metrics endpoint unavailable | Metrics disabled or worker metrics host/port not exposed | Check `XINFERENCE_DISABLE_METRICS` and metrics exporter flags | `operations-and-security` |

## Dependency and backend conflicts

- Do not install every optional group to fix one backend. vLLM, SGLang, MLX,
  image, audio, video, embedding, and rerank paths have different platform and
  dependency constraints.
- SGLang is intentionally separate from the `all` extra. Install it only for a
  selected SGLang workflow.
- vLLM/SGLang model serving is not equivalent to a CPU import check. Verify
  CUDA, driver, framework, and selected model-family support before claiming the
  backend works.
- MLX is Apple-silicon-specific. Linux or x86 hosts cannot verify MLX launches.
- Quantization stacks can need special wheel/build resolver behavior. When the
  failure mentions AWQ, GPTQ, BNB, or FP4, read the backend compatibility
  reference before changing package versions.

## Model source and cache symptoms

- `XINFERENCE_MODEL_SRC` controls the default model source. Use a supported hub
  value and supply hub credentials only through the environment or a secret
  manager.
- `XINFERENCE_HOME` anchors caches, logs, auth state, and launch history. A
  changed home directory can make a previously cached model or secret appear
  missing.
- Download retries, workers, timeouts, and model-source tokens are operational
  settings, not model registration fields.
- If a local model path is intended, prefer an absolute path in custom model
  JSON and validate it with the bundled model-config checker before registration.

## Auth and header issues

- Xinference's database-backed auth is enabled by default in current docs. Do
  not assume an unauthenticated public endpoint.
- API examples should use placeholders such as `<api-key>`; never echo real
  keys, JWTs, OIDC client secrets, or encryption keys.
- If the user cannot access admin routes, distinguish login/session problems
  from API-key permissions and from IP/trusted-proxy filtering.
- For password reset or auth DB migration, use the package's dedicated auth CLI
  entry points and keep persistent state under a stable home directory.

## Source-build and Web UI issues

- `NO_WEB_UI=1` is appropriate for Python-only editable installs and inspection.
- If the task is to ship a wheel or serve the Web UI, a missing frontend export
  is a packaging/build problem, not a model-serving problem.
- `XINFERENCE_FRONTEND_DIST_DIR` can point to a custom static export at runtime;
  it should be a deployment-specific path supplied by the user.

## Stop conditions

Stop and ask for environment or scope changes when:

- the selected workflow requires a GPU, MPS, vendor accelerator, model download,
  private hub token, or external service that is unavailable;
- fixing the environment would mutate a user-owned environment in a risky way;
- the user asks to claim production backend verification but only import/CLI
  checks have passed;
- secrets, network credentials, or destructive operations would be required.

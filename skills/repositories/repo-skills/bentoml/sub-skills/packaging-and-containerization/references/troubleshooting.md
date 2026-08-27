# Packaging Troubleshooting

## Missing or Wrong Service Path

Symptoms include import errors, `service` not found, or BentoML failing before build starts.

Checks:

- Confirm `service` uses `module:object`, not a file path with `.py` unless the module name actually includes it.
- Confirm the module is importable from `build_ctx`; run Python from the build context and import the module.
- Include all package files needed by the Service, especially `src/**` or package directories.
- For `src/` layout projects, set `python.is_src_layout: true` or use `pyproject.toml` auto-detection so package imports resolve after packaging.

## Dependency Resolver Failures

Symptoms include failures from `uv pip compile`, missing wheels, private index errors, or unexpected CUDA dependencies.

Fixes:

- Pin direct dependencies when reproducibility matters.
- Use `python.requirements_txt` for existing requirements files and avoid also setting `python.packages`.
- Add `index_url`, `extra_index_url`, `trusted_host`, `find_links`, or `pip_args` only when needed.
- Pass build `--platform` when locking dependencies for a non-default target.
- For private Git dependencies, prefer SSH URLs and verify credentials before build.
- Set `lock_packages: false` only when requirements are already fully pinned or resolver side effects must be avoided.

## Docker or OCI Builder Unavailable

Symptoms include `docker` not found, BuildKit failures, permission errors, or daemon connection failures.

Fixes:

- Build the Bento first with `bentoml build`; this does not require Docker.
- Install/start Docker Desktop or configure another backend before `bentoml containerize`.
- Use `bentoml containerize BENTO_TAG --progress plain` for clearer image build output.
- On Apple silicon or mixed architecture hosts, pass `--platform linux/amd64` or the intended target image platform.
- If a custom `setup_script` fails silently, add `set -euxo pipefail` and ensure the script has a shebang and executable bit.

## Invalid Include or Exclude Patterns

Symptoms include missing source files inside the Bento, import errors after build, or accidentally packaged secrets/large files.

Fixes:

- Remember patterns are relative to `build_ctx`.
- `exclude` is applied after `include`.
- `.bentoignore` files under the build context can remove files even when `include` matches.
- Use narrow includes such as `service.py`, `src/**`, and `config/*.json` for production.
- Exclude tests, notebooks, training data, secrets, local caches, and generated artifacts.

## Model Missing From Store

Symptoms include failures while resolving `models` entries or Service code that references `bentoml.models.BentoModel(...)`.

Fixes:

- Run `bentoml models list` or the relevant model-management API to confirm the model tag exists locally before build.
- Use explicit model tags like `classifier:20240601` rather than relying on `latest` for reproducible builds.
- Use model aliases in `models` when Service code expects `bentoml.models.BentoModel("alias")`.
- Keep framework-specific model save/load issues in the model-management workflow.

## Platform Mismatch

Symptoms include packages that install locally but fail in container, macOS wheels packaged for Linux, or Apple silicon build failures.

Fixes:

- Use build `--platform` for dependency locking/build target, for example `bentoml build --platform linux .`.
- Use containerize `--platform` for OCI image target, for example `bentoml containerize svc:latest --platform linux/amd64`.
- Prefer Linux-compatible dependencies for deployment Bentos.
- If using conda, ensure the selected distro supports Miniconda.

## Build Args Errors

Symptoms include missing required argument errors from `bentoml.use_arguments(...)`, type validation failures, or unexpected default values.

Fixes:

- Supply arguments in `args:` in the build file, `--arg key=value`, `--arg-file args.yaml`, or `bentoml.build(..., args={...})`.
- For Pydantic schemas, match expected types; CLI values are strings unless parsed by the schema.
- Keep secrets out of committed build files; use environment variables or secure deployment secret mechanisms when appropriate.
- Remember CLI args override config-file args.

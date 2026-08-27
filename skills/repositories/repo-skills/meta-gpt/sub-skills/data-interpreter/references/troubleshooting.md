# Data Interpreter Troubleshooting

DI failures usually come from configuration, missing datasets, optional tools, or generated-code side effects. Start with the least invasive diagnostic: import/signature checks, path validation, and prompt review before any LLM run.

## Quick Triage

| Symptom | Likely Cause | Safe Response |
| --- | --- | --- |
| Importing DI roles fails before any task runs | Missing/placeholder LLM config, missing optional dependency, version mismatch | Run `python scripts/di_import_check.py`; fix root MetaGPT config/API key setup before DI execution |
| Benchmark task raises dataset not found | `data_dir` points to `di_dataset` instead of its parent, dataset not downloaded, typo in task directory | Validate with `references/data-formats.md`; correct `data_dir` or prompt file paths |
| Titanic train path missing | README/path mismatch such as `4_titanic` vs `04_titanic` | Prefer `04_titanic`; check if downloaded data used a nonstandard folder and rewrite prompt paths explicitly |
| Notebook execution times out | Long model training, network wait, browser hang, package install, infinite loop | Reduce data/sample size, set lower timeout for diagnostics, inspect generated code, avoid package installs inside notebooks |
| `DeadKernelError` or kernel disappears | Generated code crashed the kernel or exhausted resources | Restart executor, inspect last code cell, reduce memory/CPU use, avoid unsafe native extensions |
| Code failure mentions coroutine object | Generated code called async function without `await` | Patch prompt or code to use `await` in notebook context |
| `!pip` output treated as failure | `ExecuteNbCode` intentionally discourages package installs in generated code | Install prerequisites outside DI with user approval; rerun after environment is ready |
| Browser/tool command not found | Tool not registered or wrong tool list/recommender | Use named tools known to the registry; route tool internals to `rag-and-tools` |
| RoleZero reaches max loop and asks to continue | Task too broad, tool failure loop, or insufficient observations | Summarize progress, ask user before continuing, split task into smaller steps |
| Generated files appear in unexpected place | MetaGPT workspace path or editor/terminal working directory was not confirmed | Set or inspect workspace before execution; use explicit output paths in prompt |

## API Keys and Config

MetaGPT DI roles need a valid LLM configuration for real runs. Direct imports or role construction can fail when configuration contains placeholder values such as a dummy `api_key` in `config2.yaml` or equivalent project/user config.

Checklist:

- Confirm the configured provider, model, base URL, and API key are real and allowed for the task.
- Fix root MetaGPT configuration before debugging DI logic; DI generated-code errors are secondary if the LLM cannot initialize.
- Do not paste API keys into prompts, generated notebooks, benchmark requirement strings, or saved histories.
- If the user asks for a planning-only answer, do not instantiate roles or run tasks just to check configuration.

Use root MetaGPT troubleshooting guidance for provider/config precedence and return here for DI-specific role/action diagnostics.

## Missing Datasets and Path Mismatches

Benchmark runners expect `data_dir` to contain `di_dataset/`. If the user gives the dataset folder itself, normalize before formatting prompts.

Common fixes:

- Given `/work/data/di_dataset`, use `data_dir=/work/data` or manually rewrite paths to `/work/data/di_dataset/...`.
- Use `04_titanic`, not `4_titanic`, unless the actual downloaded data differs.
- Ensure ML tasks with file-backed datasets have both `split_train.csv` and `split_eval.csv`.
- Ensure open-ended image tasks have the expected `.png`/`.jpg` files.
- For built-in sklearn tasks, dataset files may not be needed, but Python packages still are.

Do not start a benchmark run to discover path errors; check paths first.

## Credentials and Sensitive Prompts

The email open-ended task includes account/password placeholders in the requirement source. Treat this as unsafe automation evidence, not a pattern to copy.

Before any email workflow:

- Replace embedded credentials with secure secret handling outside the prompt.
- Ask the user to approve the exact account, read scope, reply rules, and whether sending is disabled or enabled.
- Prefer dry-run mode that summarizes the intended reply without sending.
- Avoid saving secrets in notebooks, histories, logs, or generated code.
- Stop if the prompt asks to send messages without explicit user authorization.

The same principle applies to `sd_url`, private datasets, cookies, OAuth tokens, repository credentials, and browser sessions.

## Stable Diffusion Service (`sd_url`)

Text-to-image examples require an external Stable Diffusion service endpoint.

Troubleshooting:

- Missing `sd_url`: ask user for the endpoint; do not invent one.
- Connection refused/timeout: verify the service is running and reachable from the execution environment.
- Authentication/TLS errors: ask for approved access method; do not bypass security.
- Large image generation costs: bound image count, dimensions, and retries.

Route implementation details of SD tool registration or HTTP client internals to `rag-and-tools`.

## Browser, Selenium, and Web Access

Browser/page-imitation/open-web tasks require network access and browser tooling.

Check before running:

- Browser binary and WebDriver compatibility.
- Headless/display availability in the environment.
- Network permission for target sites.
- Login, anti-bot, robots, or ToS constraints.
- Whether page screenshots or site content may be stored.

Failure patterns:

- WebDriver not found or browser version mismatch: install/align browser tooling outside DI after approval.
- Page load timeout: reduce scope, use static requests when allowed, or ask for a cached HTML file.
- Login/blocked page: stop and ask user; do not attempt credential or anti-bot bypass.

## OCR and Image Dependencies

OCR tasks require PaddleOCR or equivalent dependencies, which can be heavy and platform-specific.

Failure patterns and responses:

- `ModuleNotFoundError: paddleocr` or Paddle/PaddleOCR import errors: mark OCR dependency missing; ask before installation.
- Language model missing for Chinese/English OCR: confirm language packs/models.
- Image file not found: validate `open_ended_tasks/<id>_ocr.*` path.
- Poor OCR result: ask for image quality/resolution improvements or manual validation.

Background removal requires `rembg` and image-processing dependencies. Treat missing model downloads as external prerequisites.

## Notebook Execution Errors

`ExecuteNbCode` runs generated Python in a notebook kernel and writes `code.ipynb` in the configured workspace. Kernel support depends on notebook-related packages such as `nbformat`, `nbclient`, and an available Jupyter/IPython kernel; treat missing kernel packages as optional execution prerequisites, not import-smoke-test failures.

Safe debugging sequence:

1. Read the generated code before rerunning.
2. Check whether it accesses files, network, shell commands, or package installs.
3. Reproduce only the smallest failing cell when safe.
4. Use shorter timeouts for diagnostics.
5. Terminate or reset the executor after direct tests.
6. Preserve useful stdout/stderr for the next DI prompt, but strip secrets.

Common error interpretation:

- `Cell execution timed out...`: code exceeded timeout and the kernel was interrupted.
- `DeadKernelError`: restart/reset and inspect for memory/native-code crashes.
- `KeyError`/missing column: print dataframe columns and validate schema before modeling.
- `FileNotFoundError`: correct `data_dir`/prompt path; do not let DI hallucinate paths.
- `ImportError`/`ModuleNotFoundError`: install prerequisites outside DI after approval or skip optional workflow; for notebook execution, check `nbformat`, `nbclient`, `ipykernel`, and IPython/Jupyter availability before rerunning generated code.

## Long or Expensive Runs

DI benchmark runs can consume many LLM calls and execute arbitrary generated code. DABench/all-parallel runs are especially expensive.

Use these limits:

- Prefer one task, one small sample, and one explicit metric before full benchmarks.
- Avoid `tools=["<all>"]` unless the task genuinely needs multiple tool families.
- Set a human approval gate before package installs, network calls, browser automation, repository edits, or deployment.
- Summarize expected cost and runtime when the user requests benchmark reproduction.
- Skip native benchmark execution in verification unless explicitly authorized.

## Unsafe File and Repository Execution

DI can write code, edit repositories, run terminal commands, clone repos, and attempt deployment through RoleZero-family roles.

Required safeguards:

- Use a disposable workspace or clean git worktree.
- Ask before modifying user files or running terminal commands.
- Ask before `git clone`, commits, pushes, pull requests, or deployment.
- Inspect generated code for destructive operations, credential exfiltration, broad file traversal, and unbounded network access.
- Never run generated code against private data without confirming data handling rules.

## Import Diagnostic Failures

If `scripts/di_import_check.py` reports failures:

- `placeholder_config_or_api_key`: fix LLM config and remove placeholder keys.
- `missing_dependency`: install the optional package only if the requested workflow needs it.
- `module_import_failed`: compare installed `metagpt` version and selected DI modules.
- `signature_unavailable`: module imported but object inspection changed; rely on source/version-specific docs or update the skill if this is repo drift.

The diagnostic helper is intentionally conservative: it imports modules and inspects signatures, but it does not instantiate roles, call `run()`, start notebook kernels, ask LLMs, open browsers, or execute arbitrary notebooks.

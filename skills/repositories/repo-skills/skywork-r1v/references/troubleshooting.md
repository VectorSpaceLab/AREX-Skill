# Troubleshooting

Use this file for cross-cutting issues that could apply to more than one Skywork-R1V workflow.

## 1) Generated skill or helper script layout looks wrong

Symptoms:

- A router path points outside `skills/disco/skywork-r1v/`.
- A sub-skill `SKILL.md` frontmatter name does not match its directory.
- A helper script still references the original repository checkout.

Checks:

- Read `references/repo-provenance.md` and confirm the source commit is still the baseline you expect.
- Run `scripts/validate_skill_runtime.py` against the generated tree.
- Re-check the sub-skill references and scripts under `sub-skills/<id>/`.

Recovery:

- Keep runtime links inside the generated skill tree only.
- Move reusable logic into the bundled `scripts/` directory rather than leaving it as prose.

## 2) Missing Python dependencies for the safe helpers

Symptoms:

- `requests`, `tqdm`, `flask`, `pillow`, `pyyaml`, `pandas`, or `openpyxl` fail to import.
- A helper script exits before it can validate a JSONL file or summarize results.

Checks:

- Use the small helper environment described in `references/model-and-backend-overview.md`.
- Run `python -m pip check` in that environment.

Recovery:

- Install only the small helper stack listed in the overview.
- Do not install the full CUDA/model stack unless you are actually using the local inference workflow.

## 3) Local inference failures

Symptoms:

- `CUDA` or `flash-attn` import errors.
- `model_path` cannot be resolved or downloaded.
- `tensor_parallel_size` or GPU count is mismatched.
- OOM during long generation or multi-image prompts.

Checks:

- Switch to the `local-inference` sub-skill.
- Verify the model id/path and GPU count before running.
- Use the bundled command builder to inspect the exact command line first.

Recovery:

- Match the command to the actual GPU count.
- Reduce the prompt/image pressure if you hit memory limits.
- Treat full 38B inference as a CUDA workflow; there is no CPU fallback in the native scripts.

## 4) R1V4 API batch issues

Symptoms:

- 401/403/429/5xx errors from the endpoint.
- Missing or invalid API key.
- Bad image paths or unknown MIME types.
- Parse failures around `<tool_call>` or `<observation>` blocks.

Checks:

- Switch to `r1v4-api-testing`.
- Validate the JSONL input before sending any request.
- Preview the request payload with the bundled payload builder.
- Parse one response string with the bundled parser before batch runs.

Recovery:

- Keep the API key outside runtime files.
- Fix image paths first, then retry parsing and payload generation.
- If the viewer is the problem, use the summary helper instead of the interactive Flask route.

## 5) Evaluation reproduction issues

Symptoms:

- The vLLM server does not answer on port 8000.
- The server model name does not match the client expectation.
- Benchmark output paths are missing or reuse behavior is confusing.
- Judge or API credentials are not configured.
- MMMU/LogicVista post-processing is skipped or scores look inconsistent.

Checks:

- Switch to `evaluation-reproduction`.
- Confirm the command builder output before you launch anything.
- Check that the served model name is `r1v3-alpha` in the stock Skywork flow.
- Confirm dataset and cache prerequisites before a full benchmark run.

Recovery:

- Align the client base URL with the served model endpoint.
- Use the boxed-answer scorer helper for the rule-based post-processing step.
- Keep EMMA/MMK12 keys and base URLs in the environment, not in bundled runtime files.

## 6) When to stop and reassess

Stop and revisit the route when:

- the request is actually about another Skywork workflow family
- the task needs a full GPU/model run but the user only asked for safe command construction
- the helper environment is missing basic Python packages
- the benchmark requires credentials, model weights, or datasets that have not been supplied

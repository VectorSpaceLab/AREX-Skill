# Cross-Cutting Troubleshooting

Use this reference for failures that span multiple DeepResearch/WebAgent routes. For workflow-specific issues, continue to the nearest sub-skill troubleshooting file.

## “I cannot import or install everything”

Symptoms:

- Full requirements install is slow, pulls CUDA packages, or conflicts with an existing environment.
- Python 3.13 is present but compiled ML dependencies fail to resolve.
- A user only wants to validate datasets or choose a family route, not serve a model.

Fix:

1. Do not install the full GPU/serving stack for schema/routing tasks.
2. Use Python 3.10+ and the bundled stdlib helpers for local validation.
3. Install heavyweight requirements only after confirming the selected workflow requires them.
4. For root ReAct local serving, prefer Python 3.10 because the public README recommends it and the requirements include compiled ML packages.
5. If the user supplied an existing environment, ask before upgrading/downgrading torch, vLLM, SGLang, qwen-agent, or CUDA packages.

## “The task says DeepResearch but the paths do not match”

Likely causes:

- The user means the root Tongyi DeepResearch ReAct workflow.
- The user means the `WebAgent` umbrella project or a specific family member.
- The user means official benchmark evaluation, not inference generation.

Fix:

1. Use the root router table in `SKILL.md`.
2. Run `sub-skills/webagent-family/scripts/choose_webagent_variant.py` with the user’s task text if family routing is unclear.
3. Use `scripts/inspect_deepresearch_checkout.py --repo-root <checkout>` to check whether a current checkout contains the expected root and family files.

## Missing or placeholder credentials

Common symptoms:

- Search or Scholar returns no useful results or service errors.
- Visit cannot read/summarize pages.
- PythonInterpreter reports SandboxFusion endpoint errors.
- File parsing fails for PDFs/Office/video.
- Official judge scripts fail before metrics are written.

Likely missing variables:

| Surface | Variables/services |
|---|---|
| Search / Scholar | `SERPER_KEY_ID` |
| Visit page reading | `JINA_API_KEYS` |
| Visit summarization or hosted model calls | `API_KEY`, `API_BASE`, `SUMMARY_MODEL_NAME` |
| File parsing | `DASHSCOPE_API_KEY`, optional Dashscope base/model variables |
| Python tool | `SANDBOX_FUSION_ENDPOINT` |
| Benchmark judging | `OPENAI_API_KEY`, `OPENAI_API_BASE`, `API_KEY`, `BASE_URL`, and tokenizer path variables depending on route |
| WebWatcher image upload | optional Alibaba Cloud OSS keys |
| WebWeaver / WebWalker providers | project-specific provider keys described in the family references |

Fix: validate `.env` shape with the `react-inference` helper, but never ask the user to paste secrets into the chat unless absolutely necessary and safe for the environment.

## Local model serving does not start

Symptoms:

- vLLM/SGLang process exits, hangs, or never opens `/v1/models`.
- CUDA out-of-memory or no visible GPU.
- Port collision on the configured local endpoint.
- NCCL interface or fabric errors.

Fix:

1. Verify GPU count, memory, driver compatibility, and model size.
2. Check whether the workflow assumes a fixed device/port layout. Root DeepResearch assumes eight ports; WebWeaver/WebWatcher/WebResummer have their own serving layouts.
3. Confirm the model path is not a placeholder and is readable by the serving process.
4. Reduce concurrency/rollouts only after confirming the command supports it.
5. For hosted routes, do not launch local servers; adapt the OpenAI-compatible endpoint instead.

## Dataset or rollout files fail validation

Route input dataset failures to `sub-skills/react-inference/references/data-formats.md` and run:

```bash
python sub-skills/react-inference/scripts/validate_deepresearch_dataset.py <dataset.jsonl>
```

Route prediction rollout failures to `sub-skills/benchmark-evaluation/references/prediction-format.md` and run:

```bash
python sub-skills/benchmark-evaluation/scripts/validate_prediction_rollouts.py <rollout-folder> --dataset gaia
```

Typical fixes:

- Use `.jsonl` or `.json` only.
- Ensure every record has string `question` and `answer` fields.
- Provide a file corpus directory when questions reference uploaded files.
- Keep three unsuffixed `iter1.jsonl`, `iter2.jsonl`, `iter3.jsonl` files for official DeepSearch judging.
- Merge split-suffixed rollout files before official judging.

## Unreleased, paper-only, or external assets

Symptoms:

- The user asks for Heavy Mode, WebResearcher demos, ReSumTool, full WebSailor-V2 training, or AgentFounder/AgentScaler training code.
- Local tree contains README/method notes but no runnable scripts.

Fix:

1. Do not invent missing code or checkpoints.
2. State what the inspected public tree includes and what is external or pending.
3. Offer the closest runnable route: root ReAct for text QA, WebWeaver for open-ended reports, WebWalker for traversal/RAG, WebWatcher for multimodal if assets exist, or method-only guidance otherwise.

## Generated-skill staleness

Symptoms:

- Current checkout has a different commit, package layout, or public script interface.
- The user reports command flags not matching this skill.
- Family project READMEs changed or new models/scripts appeared.

Fix:

1. Read `references/repo-provenance.md`.
2. Run `scripts/inspect_deepresearch_checkout.py --repo-root <checkout>`.
3. If commit, dirty state, or major evidence paths differ, refresh the repo skill before relying on exact command or field claims.

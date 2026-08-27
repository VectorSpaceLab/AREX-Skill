---
name: deep-research
description: "Operate Tongyi DeepResearch and its WebAgent family: ReAct
  inference setup, rollout validation, benchmark evaluation, and variant
  routing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DeepResearch Repo Skill

Use this repo skill when a task involves Tongyi DeepResearch, Alibaba-NLP DeepResearch, Tongyi-DeepResearch-30B-A3B, root ReAct inference, DeepResearch rollout files, official benchmark scoring, or the related WebAgent/Agent family variants bundled with the project.

This skill is self-contained operating context. Use its bundled references and scripts first; do not rely on the original repository docs, examples, or scripts for routine setup, routing, and validation questions.

## Fast Routing

| Task signal | Read |
|---|---|
| `.env`, model path, local vLLM ports, OpenRouter/OpenAI-compatible inference, JSON/JSONL questions, file references, Search/Visit/Scholar/Python/File tools, `<tool_call>` or `<answer>` issues | [`sub-skills/react-inference/SKILL.md`](sub-skills/react-inference/SKILL.md) |
| `iter1.jsonl`, `iter2.jsonl`, `iter3.jsonl`, split rollouts, prediction schema, HLE, GAIA, BrowseComp, WebWalker, XBench DeepSearch, Pass@k, judge API costs | [`sub-skills/benchmark-evaluation/SKILL.md`](sub-skills/benchmark-evaluation/SKILL.md) |
| Choosing between WebDancer, WebSailor, WebWatcher, WebWeaver, WebWalker, WebResummer/ReSum, WebShaper, WebLeaper, AgentFold, ParallelMuse, AgentFounder, AgentScaler, or NestBrowse | [`sub-skills/webagent-family/SKILL.md`](sub-skills/webagent-family/SKILL.md) |
| Cross-cutting install/config prerequisites, service variables, model-family overview, or repo staleness checks | Root references and scripts below |

## Operating Procedure

1. **Identify the user’s deliverable.** Distinguish inference generation, prediction validation, official judging, family selection, or method comparison. Many user requests say “DeepResearch” but actually mean a WebAgent subproject.
2. **Check source/release alignment when needed.** Read [`references/repo-provenance.md`](references/repo-provenance.md) and optionally run `scripts/inspect_deepresearch_checkout.py --repo-root <checkout>` against a user-provided checkout before assuming this skill matches it.
3. **Validate before expensive execution.** Use the bundled stdlib validators for `.env`, input datasets, rollout folders, and family routing before launching GPU servers, web tools, or LLM-as-judge APIs.
4. **Surface prerequisites explicitly.** Full local runs usually require model weights, multiple GPUs, vLLM or SGLang, search/visit/file/parser credentials, and benchmark data. Hosted OpenAI-compatible routes can avoid local GPUs but still need API credentials and code/config adaptation.
5. **Keep verification honest.** A schema validator pass is not the same as a successful model rollout or official judge score. Do not treat missing credentials, model weights, large image archives, or required GPUs as ordinary passes.

## Setup Note

- The inspected checkout is not packaged as a normal installable Python distribution. For real local inference or benchmark execution, install `requirements.txt` inside a private Python 3.10 environment that the user authorizes for this task.
- For validation-only or routing-only work, the bundled stdlib scripts are enough: `scripts/inspect_deepresearch_checkout.py`, `sub-skills/react-inference/scripts/build_react_env.py`, `sub-skills/react-inference/scripts/validate_deepresearch_dataset.py`, `sub-skills/benchmark-evaluation/scripts/validate_prediction_rollouts.py`, and `sub-skills/webagent-family/scripts/choose_webagent_variant.py`.
- A minimal health check for the generated skill is to run the inspection helper and the relevant `--help`/fixture validators; there is no public import name to check at the root because the repository is a script/model-release collection rather than a Python package.

## Root References

- [`references/model-and-repo-overview.md`](references/model-and-repo-overview.md) — project purpose, root model facts, WebAgent family relationship, and what is runnable versus method-only.
- [`references/configuration.md`](references/configuration.md) — shared Python, dependency, model, credential, dataset, and backend prerequisites.
- [`references/troubleshooting.md`](references/troubleshooting.md) — cross-cutting install/import, credential, model-serving, path, and dependency failures.
- [`references/repo-provenance.md`](references/repo-provenance.md) — source snapshot and evidence paths used to build this skill.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) — structured scenario metadata for managed repo-skill routing.

## Root Script

- `scripts/inspect_deepresearch_checkout.py --help` — safe stdlib checker for a current checkout’s expected files, Git state, large-blocker hints, and likely staleness relative to this skill’s provenance.

## Important Boundaries

- Do not run full ReAct inference unless the user has provided model weights or a hosted model route, required tool credentials, output/data paths, and permission for long-running GPU/network work.
- Do not run official LLM-as-judge evaluation until rollout shape passes preflight and the user has approved API cost/credentials.
- Do not promise unreleased checkpoints, training data, Heavy Mode, or paper-only pipelines. Route them as documented limitations or method references.
- Do not place secrets in generated `.env` templates, logs, reports, or user-facing plans.
- Route project-maintenance edits, packaging changes, or source-code modifications through ordinary repository-maintenance reasoning; this repo skill is for operating and troubleshooting the public DeepResearch/WebAgent workflows.

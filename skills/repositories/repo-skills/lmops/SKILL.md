---
name: lmops
description: "Route LMOps paper-code workflows for prompt optimization,
  retrieval, adaptation, distillation, experiential learning, RAG, and LLM
  acceleration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LMOps

Use this repo skill when the user asks about the Microsoft LMOps repository or its paper-code projects for prompt intelligence, in-context learning, LLM adaptation, data selection, distillation/post-training, experiential learning, retrieval-augmented generation, or reference-based acceleration.

This skill is a **safe operating map**, not a claim that paper-scale GPU training was run during skill creation. It emphasizes routing, command planning, input validation, prerequisites, and troubleshooting before a later Researcher attempts expensive execution.

## First routing pass

1. Identify the named LMOps project or task shape.
2. If the user has a local LMOps checkout, optionally run `scripts/check_lmops_checkout.py` against their checkout to verify which project directories are present. The helper is read-only and does not import repo code.
3. Choose the nearest sub-skill:
   - `sub-skills/prompt-optimization/SKILL.md` for ProTeGi automatic prompt optimization and Promptist text-to-image prompt rewriting/training planning.
   - `sub-skills/example-retrieval/SKILL.md` for UPRISE, SE2, LLM Retriever, CED-ICL, Structured Prompting, and Understand ICL.
   - `sub-skills/adaptation-and-training/SKILL.md` for AdaptLLM, Instruction Pre-Training, Data Selection via Optimal Control, ResLoRA, and Learning Law.
   - `sub-skills/distillation-and-post-training/SKILL.md` for MiniLLM, DPKD, and Tuna.
   - `sub-skills/rl-experiential-learning/SKILL.md` for OEL, OPCD, LLM-as-a-Coach, GAD, and OPO.
   - `sub-skills/rag-and-acceleration/SKILL.md` for CoRAG and LLMA.
4. Read `references/project-index.md` when the request names a paper, project acronym, or source area but the task family is unclear.
5. Read `references/troubleshooting.md` before turning a paper workflow into executable commands. Many LMOps workflows require old dependency stacks, large model/data downloads, credentials, Docker/Ray/vLLM services, or multi-GPU hardware.

## Root-level facts to preserve

- LMOps is a collection of independent research-code projects, not one installable root Python distribution.
- A single Python environment cannot truthfully validate every subproject. Treat each execution request as a project-specific environment plan.
- Creation-time inspection used static source/API parsing and safe bundled helper checks. End-to-end GPU, model-download, API-scoring, server, and training workflows are documented but not native-executed by this generated skill.
- Do not paste API keys, W&B keys, Hugging Face tokens, OpenAI keys, or private cache paths into commands, logs, config files, or generated plans.
- Do not run shell launchers, Docker setup, Ray clusters, vLLM servers, downloads, or training jobs unless the user explicitly asks and the required environment and budget are present.

## Bundled root references and scripts

- `references/project-index.md`: project/acronym-to-sub-skill map and high-level workflow inventory.
- `references/troubleshooting.md`: shared install, dependency, credential, hardware, data, service, and staleness troubleshooting.
- `references/repo-provenance.md`: source snapshot and evidence paths for refresh decisions.
- `references/repo-routing-metadata.json`: structured import metadata for managed `repo-skills-router`.
- `scripts/check_lmops_checkout.py`: read-only checkout structure checker and sub-skill router.

## Safe checkout check

When a user provides a checkout, run the bundled helper rather than assuming every paper directory is present:

```bash
python scripts/check_lmops_checkout.py --repo-root /path/to/LMOps --json
```

The helper only checks names and expected files. It does not import source modules, execute scripts, download data, or modify the checkout.

## Verification and import status

This runtime skill is staged as a generated repo skill. Verification artifacts are kept outside the runtime tree. The user explicitly requested **not to import**, so do not run the managed repo-skill importer unless a later user instruction changes that decision after verification.

---
name: paper-catalog-and-execution
description: "Locate paper implementations and produce safe catalog-based run or
  adaptation plans."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Paper Catalog and Execution

Use this sub-skill when the user needs to find a paper entry in Papers in 100 Lines of Code, choose the right implementation folder, interpret cataloged README usage/requirements posture, or draft a safe run/adaptation plan without launching original training/rendering programs.

## Read when

- The request names a paper, folder, short alias, implementation script label, or broad phrase such as "find Stable Diffusion", "where is Adam?", or "which NeRF implementation?".
- The user asks whether a compact implementation is safe to run, what dependencies it needs, what assets/weights/datasets it expects, or how to adapt it safely.
- A sibling algorithm sub-skill first needs the exact catalog entry and safety posture.

## Do not use for

- GAN, VAE, flow, diffusion, DreamBooth, or Stable Diffusion algorithm details: route to `../generative-models/` after lookup.
- NeRF, 3D Gaussian Splatting, rendering, camera/ray, or implicit 3D detail: route to `../neural-rendering-3d/` after lookup.
- Optimizers, layers/activations, meta-learning, hypergradients, Deep Image Prior, or RL/Atari details: route to `../optimization-meta-rl/` after lookup.
- Full paper reproduction, native script execution, dependency installation, dataset/model download, or CUDA validation. This skill plans and triages only.

## Operating workflow

1. Load the generated catalog first: `../../references/implementation-index.md` for human browsing and `../../references/implementation-index.json` for tooling. If the JSON is present, use `scripts/plan_paper_run.py --query "<paper or alias>"` for a concise plan.
2. If a query is ambiguous, compare title aliases, folder labels, evidence script labels, owner route, requirements, and safety flags. Present top alternatives instead of guessing.
3. Treat every upstream implementation script label as catalog evidence only, not as a runtime dependency and not as an instruction to run that source file.
4. Build the plan around one selected entry: dependency pins, likely backend, download/asset/output risks, top-level training-loop risk, and sibling sub-skill route.
5. For adaptations, plan a small extracted or rewritten pattern in the user workspace. Do not ask the user to rely on the original repository checkout remaining available.
6. Use `references/catalog-workflows.md` for the full 62-entry catalog and planning checklist; use `references/troubleshooting.md` for common lookup, dependency, CUDA, asset, download, and long-loop failures.

## Safe-plan checklist

A safe catalog plan should state:

- selected paper title/folder and why it matched the query;
- sibling detail route, if algorithm-family guidance is needed;
- evidence script labels and requirements as catalog facts only;
- whether the entry likely writes files, downloads data/weights/tokenizers, hard-codes CUDA, needs external assets, or contains a long top-level train loop;
- an isolated-environment/dependency strategy for the single selected paper, not the whole repository;
- a no-execution default unless the user separately authorizes a bounded run with dependencies, data, hardware, output directory, and stop limits.

---
name: align-anything
description: "Operate the Align-Anything multimodal alignment package, including
  training, serving, remote reward models, and satellite projects."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Align-Anything Repo Skill

Use this root skill when a task involves the Align-Anything package: multimodal instruction tuning, preference/reward/cost alignment, PPO with remote reward models, text/image/audio/video/omni serving, or the repository's satellite project workflows.

## Route first

- **Training, configs, datasets, launchers, and alignment algorithms** → `sub-skills/training-and-alignment/`
- **Model loading, text/multimodal/omni CLIs, media inputs, and inference smoke checks** → `sub-skills/multimodal-serving/`
- **Remote reward server/client, reward functions, math verifier, and PPO remote-RM wiring** → `sub-skills/remote-reward-models/`
- **Satellite projects such as Any-to-Text, Janus, InterMT, language feedback, Chameleon-style text-image-to-text-image, or Eval-Anything** → `sub-skills/project-workflows/`

Read `references/overview.md` for the package map, `references/installation-and-environment.md` before running code, and `references/troubleshooting.md` for cross-cutting failures.

## Fast operating sequence

1. Classify the user request by workflow and backend. CUDA/GPU is usually required for real training, model loading, vLLM, and multimodal generation; CPU imports are only partial evidence.
2. Run the bundled environment check before attempting package operations in a new runtime:

   ```bash
   python scripts/check_align_anything_environment.py --json
   ```

3. Load the most specific sub-skill and its bundled references/scripts.
4. Prefer bundled script templates over source-repository shell snippets. The source scripts were distilled into this skill's `scripts/` trees; avoid relying on a particular checkout layout.
5. Do not run long training, benchmark downloads, remote-code models, or project scripts until model/data paths, credentials, output directories, GPU memory, and network expectations are explicit.

## Core facts

- Package import name: `align_anything`
- Package version observed during construction: `0.0.1.dev0`
- Primary runtime: Python package with PyTorch, Transformers, DeepSpeed, datasets, Gradio, media dependencies, and optional vLLM/Janus/project-specific extras.
- Confirmed construction commit: see `references/repo-provenance.md`.
- Router metadata for managed repo-skill import is in `references/repo-routing-metadata.json`.

## Avoid this skill when

- The task is about a different alignment package or a generic RLHF concept with no Align-Anything artifact.
- The user only needs to import/export DisCo skills, not operate the repository.
- A required backend or model/data asset is unavailable and the user has not accepted a narrowed or planning-only scope.

## Handoff checklist

When handing a plan to execution, include:

- Selected sub-skill and workflow.
- Package/runtime readiness check result.
- Required backend, model weights, processor/tokenizer, dataset files, reward endpoint, output directory, and optional extras.
- Whether source checkout access is necessary for the current task; the skill itself is self-contained, but some bundled helper scripts can inspect a user-provided Align-Anything checkout when the user asks to inventory local project files.
- Known gaps or optional dependencies from `references/troubleshooting.md` and the chosen sub-skill's troubleshooting reference.

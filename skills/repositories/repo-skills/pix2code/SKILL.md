---
name: pix2code
description: "Operate the pix2code research repository for GUI screenshot-to-DSL
  experiments, legacy Keras/TensorFlow training, model sampling, and DSL
  compilation to web, Android, or iOS code."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# pix2code Repo Skill

Use this skill when a task involves the pix2code research codebase: turning GUI screenshot datasets into training examples, training or inspecting the legacy Keras/TensorFlow model, generating the pix2code DSL from screenshots, or compiling `.gui` DSL files into web, Android, or iOS scaffold code.

pix2code is an educational 2017 research prototype. Treat it as historical ML code, not a production UI generator. Prefer small, deterministic checks and explicit artifact validation before attempting model training or inference.

## Start here

1. Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches a checkout or needs a refresh.
2. Read [references/package-overview.md](references/package-overview.md) for repository layout, dependency constraints, and source facts shared across workflows.
3. Run or adapt [scripts/check_pix2code_environment.py](scripts/check_pix2code_environment.py) when the task starts with setup, dependency diagnosis, or legacy TensorFlow/Keras compatibility.
4. Route to the focused sub-skill below; do not reopen original repo scripts unless the user is explicitly maintaining the checkout.

## Install and inspection baseline

The original README listed Python 2 or 3 and these historical pins:

```text
Keras==2.1.2
numpy==1.13.3
opencv-python==3.3.0.10
h5py==2.7.1
tensorflow==1.4.0
```

For modern hosts, expect to use an isolated legacy Python environment. The old OpenCV pin may no longer be available from current package indexes; use the troubleshooting reference before changing versions. A minimal inspection check is:

```bash
python scripts/check_pix2code_environment.py --include-ml
```

The repository is not a packaged Python distribution with console entry points. Its scripts rely on working from either the `model/` or `compiler/` source directories. This generated skill therefore bundles safer helpers that are self-contained and runnable from arbitrary directories.

## Route map

| Task intent | Read this |
| --- | --- |
| Prepare pix2code datasets, validate `.gui`/image pairs, split train/eval sets, convert screenshots to `.npz`, or plan legacy training commands. | [sub-skills/data-and-training/SKILL.md](sub-skills/data-and-training/SKILL.md) |
| Validate trained artifacts, choose greedy versus beam search, diagnose missing `pix2code.json` / `.h5` / `meta_dataset.npy` / `words.vocab`, or explain batch versus single-image generation. | [sub-skills/sampling-and-generation/SKILL.md](sub-skills/sampling-and-generation/SKILL.md) |
| Compile a `.gui` DSL file to web Bootstrap HTML, Android XML, or iOS Storyboard, inspect DSL tokens, or debug malformed DSL nesting. | [sub-skills/dsl-compilation/SKILL.md](sub-skills/dsl-compilation/SKILL.md) |
| Diagnose install/import failures, stale helper behavior, unavailable pretrained results, or research-prototype limitations shared by multiple workflows. | [references/troubleshooting.md](references/troubleshooting.md) |

## Operating rules

- Keep user-facing instructions self-contained. Use bundled scripts and references in this skill rather than relying on original checkout scripts.
- Avoid full training unless the user explicitly accepts a long-running legacy TensorFlow/Keras job and has the data unpacked.
- Treat GPU acceleration as optional for this skill. CPU validates dataset handling and DSL compilers; paper-scale training speed or model quality is not verified by CPU checks.
- Validate generated or user-supplied `.gui` files before compiling them. Unknown tokens raise `KeyError` in the original compiler; use the bundled compiler's clearer diagnostics.
- Verify trained artifact directories before sampling. pix2code inference requires the JSON architecture, HDF5 weights, NumPy metadata, and vocabulary files to agree.
- Record any dependency substitutions separately from model-quality claims. A successful import of modern or substituted packages does not prove the 2017 paper result.

## Common deliverables

- A cleaned or validated pix2code dataset layout with paired `.gui` and `.png`/`.npz` files.
- A command plan for legacy model training that distinguishes in-memory versus generator mode.
- A trained-artifact validation report before sampling screenshots.
- A compiled HTML/XML/Storyboard scaffold from a DSL fixture using bundled compiler logic.
- A troubleshooting note that names whether the blocker is dependency compatibility, missing data, missing trained weights, malformed DSL, or a research-code limitation.

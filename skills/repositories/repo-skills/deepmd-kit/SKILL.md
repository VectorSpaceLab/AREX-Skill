---
name: deepmd-kit
description: "Route DeePMD-kit package workflows for installation, data/config
  preparation, training, inference/model operations, integrations, and
  repository development."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 3.0
---

# DeePMD-kit Repo Skill

Use this skill when the user is working with DeePMD-kit: installing the package, preparing DeePMD data/configs, training or fine-tuning potentials, running inference/model operations, integrating with MD engines/native APIs, or maintaining the repository.

DeePMD-kit is a Python/C++ package for deep learning interatomic potentials and molecular dynamics. It supports TensorFlow, PyTorch, JAX, Paddle, and DP/reference backend routes, plus integrations with LAMMPS, i-PI, C/C++/Node.js, dpdata, and ASE.

## Start Here

1. Identify whether the task is package use, data/config preparation, training, inference/model operations, integration/deployment, or repository maintenance.
2. Confirm the installed runtime before executing commands:

   ```bash
   python -c "import deepmd; print(deepmd.__version__)"
   dp -h
   ```

3. Use explicit backend flags when the backend matters: `dp --tf`, `dp --pt`, `dp --jax`, `dp --pd`, or `dp --backend pytorch-exportable`.
4. Avoid long training, C++ builds, downloads, or native MD runs unless the user asks for execution or approves the cost.
5. Read `references/repo-provenance.md` when deciding whether this skill matches a current checkout or should be refreshed.

## Route by Task

| User task | Read |
| --- | --- |
| Install DeePMD-kit, choose pip/conda/docker/source build, diagnose missing backend, validate `dp` availability | `sub-skills/installation-backends/SKILL.md` |
| Inspect `type.raw`, `type_map.raw`, `set.*`, labels, mixed-type systems, LMDB/HDF5/npy layouts, or draft/repair training JSON/YAML | `sub-skills/data-config/SKILL.md` |
| Choose a model family, draft `dp train`, monitor `lcurve.out`, restart/fine-tune, handle pretrained/multi-task, or freeze after training | `sub-skills/training-models/SKILL.md` |
| Use `DeepPot`, run `dp test`, `eval-desc`, `embed`, `model-devi`, `show`, `compress`, `convert-*`, `pretrained`, or `change-bias` | `sub-skills/inference-model-ops/SKILL.md` |
| Write LAMMPS/i-PI inputs, use C/C++/Node/dpdata/ASE APIs, build native components, or maintain this checkout | `sub-skills/integrations-development/SKILL.md` |

## Cross-Cutting References

- `references/cli-overview.md` summarizes verified `dp` backend aliases and subcommands.
- `references/troubleshooting.md` maps common symptoms to the right sub-skill and first checks.
- `references/repo-routing-metadata.json` contains structured import metadata for `repo-skills-router`.

## Common Command Map

- Install/runtime check: `dp --version`, `dp -h`, `dp --pt -h`.
- Training: `dp --tf train input.json`, `dp --pt train input.json`, `dp --pd train input.json`.
- Freeze: `dp freeze -o model.pb`, `dp --pt freeze -o model.pth`, `dp --pd freeze -o model`.
- Test/inference: `dp test -m model.pb -s system -n 30`, `dp eval-desc -m model.pb -s system -o desc`.
- Model ops: `dp model-devi`, `dp compress`, `dp convert-from`, `dp convert-backend`, `dp show`, `dp pretrained download`.
- Integration: generate LAMMPS input with `sub-skills/integrations-development/scripts/write_lammps_deepmd_input.py`.

## Safety and Validation

- Use bounded help/parser/import checks before running long workflows.
- Treat repository examples and tests as evidence; do not rely on original checkout paths in generated user-facing workflows.
- Training examples are small validation fixtures, not production datasets.
- Prefer focused tests such as a single `pytest` target over the full suite when maintaining the checkout.
- For source/C++ builds, use generous timeouts and do not cancel known long build operations.

## Existing Focused Skills

This generated repo skill is a self-contained router for DeePMD-kit package and repository work. The source repository also contains narrower official skills for training, DPA3 fine-tuning, Python inference, and LAMMPS; their concepts were distilled here, but runtime use of this generated skill does not require the original repository skills to remain available.

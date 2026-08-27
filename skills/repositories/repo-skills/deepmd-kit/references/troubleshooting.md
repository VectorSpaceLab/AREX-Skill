# DeePMD-kit Troubleshooting Router

Use this router when the symptom spans multiple DeePMD-kit workflows. Follow the owner link for detailed recovery steps.

| Symptom | First checks | Owner |
| --- | --- | --- |
| `import deepmd` fails | Confirm active Python, package install, Python version `>=3.10`, and backend package availability. | `sub-skills/installation-backends/references/troubleshooting.md` |
| `dp` command not found | Use `python -m deepmd -h`; check console script path and active environment. | `sub-skills/installation-backends/references/troubleshooting.md` |
| `Unknown backend` or wrong backend selected | Use explicit `--tf`, `--pt`, `--jax`, `--pd`, or set valid `DP_BACKEND`. | `sub-skills/installation-backends/SKILL.md` |
| Backend import error (`tensorflow`, `torch`, `jax`, `paddle`) | Install the matching backend and avoid mixing GPU wheels with incompatible drivers. | `sub-skills/installation-backends/references/troubleshooting.md` |
| Training data loader shape/type error | Inspect `type.raw`, `type_map.raw`, `set.*`, `coord`, `box`, and labels. | `sub-skills/data-config/references/troubleshooting.md` |
| Missing `box.npy` or PBC confusion | Check `nopbc`; periodic systems need boxes, non-periodic Python inference can use `cell=None`. | `sub-skills/data-config/references/troubleshooting.md` |
| Training loss is NaN or exploding | Check labels, type maps, learning rate, descriptor cutoff/selection, data scale, and backend precision. | `sub-skills/training-models/references/troubleshooting.md` |
| Fine-tune or pretrained model has type/head mismatch | Inspect model metadata with `dp show`; align `type_map`, `model-branch`, `head`, and config. | `sub-skills/training-models/references/troubleshooting.md` |
| `DeepPot.eval` shape error | Reshape coordinates to `(nframes, natoms*3)`, cell to `(nframes, 9)` or `None`, and atom types to the expected type-map order. | `sub-skills/inference-model-ops/references/troubleshooting.md` |
| Model suffix/backend mismatch | Use `dp show`, explicit backend flags, or conversion/compatibility commands. | `sub-skills/inference-model-ops/references/troubleshooting.md` |
| LAMMPS cannot find `pair_style deepmd` | Confirm plugin or built-in USER-DEEPMD package, `plugin load`, and runtime library paths. | `sub-skills/integrations-development/references/troubleshooting.md` |
| LAMMPS run fails after velocity/thermostat setup | Confirm atom masses, element/type mapping, unit style, and model type map. | `sub-skills/integrations-development/references/troubleshooting.md` |
| C++/native build fails | Verify backend roots, CMake/compiler requirements, C++ ABI, and selected build toggles. | `sub-skills/integrations-development/references/repo-development.md` |

## General Rules

- Use help/import/parser checks before long training or native builds.
- Keep model artifact formats aligned with backend commands: `.pb` for TensorFlow, `.pth` frozen PyTorch, `.pt` PyTorch checkpoint, Paddle JSON plus parameters, and JAX formats for JAX.
- Treat old frozen models as compatibility risks; route to `convert-from` before assuming current runtime support.
- Do not repeatedly instantiate the same model inside a loop; load model objects once and reuse them to avoid framework memory growth.

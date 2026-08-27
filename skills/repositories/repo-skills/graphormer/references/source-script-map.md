# Source Script Map

This table records the repository-owned scripts and examples that were useful as
source evidence and how the generated skill replaces them at runtime.

| Source repo artifact | Bundled skill replacement | Decision | Why |
| --- | --- | --- | --- |
| `install.sh` | `references/installation-and-environment.md` + `scripts/check_graphormer_environment.py` | reference-only | Installs a historical stack and mutates the environment; not safe as a runtime helper. |
| `examples/property_prediction/zinc.sh` | `sub-skills/fairseq-training/scripts/build_graphormer_train_command.py` | adapt | Safe to render as a training command template once repo-relative paths and fixed GPU IDs are removed. |
| `examples/property_prediction/pcqv1.sh` | `sub-skills/fairseq-training/scripts/build_graphormer_train_command.py` | adapt | Same Graphormer training family as ZINC. |
| `examples/property_prediction/pcqv2.sh` | `sub-skills/fairseq-training/scripts/build_graphormer_train_command.py` | adapt | Same Graphormer training family as ZINC. |
| `examples/property_prediction/hiv_pre.sh` | `sub-skills/fairseq-training/scripts/build_graphormer_train_command.py` and `sub-skills/pretrained-and-evaluation/scripts/build_graphormer_eval_or_finetune_command.py` | adapt | Shares the MolHIV FLAG fine-tuning flags and pretrained checkpoint semantics. |
| `examples/oc20/oc20.sh` | `sub-skills/fairseq-training/scripts/build_graphormer_train_command.py` | adapt | Safe to render as a template, but the original wrapper hard-codes a local data path and distributed launch details. |
| `examples/customized_dataset/customized_dataset.py` | `sub-skills/datasets-and-customization/scripts/validate_custom_dataset_contract.py` | adapt | The example is useful, but the skill needs a validator rather than a QM9 download recipe. |
| `graphormer/evaluate/evaluate.py` | `sub-skills/pretrained-and-evaluation/scripts/build_graphormer_eval_or_finetune_command.py` | adapt | The evaluation flow is useful, but the runtime helper should only render and preflight commands. |
| `distributional_graphormer/catalyst-adsorption/scripts/*.sh` | `sub-skills/distributional-graphormer/scripts/build_dig_command.py` | adapt | Retain the command semantics without immediate distributed launch or local path assumptions. |
| `distributional_graphormer/property-guided/scripts/*.sh` | `sub-skills/distributional-graphormer/scripts/build_dig_command.py` | adapt | Retain the command semantics without immediate distributed launch or local path assumptions. |
| `distributional_graphormer/protein/run_inference.py` | `sub-skills/distributional-graphormer/scripts/build_dig_command.py` + `references/protein-workflows.md` | reference/adapt | The CLI contract is important, but the original file is large and model-specific. |
| `distributional_graphormer/protein-ligand/src/evaluation/*.sh` | `sub-skills/distributional-graphormer/scripts/build_dig_command.py` + `references/protein-ligand-workflows.md` | reference/adapt | The workflow is useful, but the original scripts depend on Docker, external data, and long GPU runs. |
| `docs/Tutorisals.rst` GraphMLP example | `sub-skills/model-extension/references/extension-recipes.md` and `scripts/summarize_graphormer_registries.py` | reference/adapt | The tutorial is valuable as a pattern, but the runtime skill should focus on registry inspection and extension recipes. |

Notes:
- A source artifact that is marked `reference-only` or `reference/adapt` is still
  useful evidence, but future agents should use the bundled helper instead of
  trying to execute the original file directly.
- The generated runtime skill must remain self-contained and must not depend on
  opening the original repository checkout.

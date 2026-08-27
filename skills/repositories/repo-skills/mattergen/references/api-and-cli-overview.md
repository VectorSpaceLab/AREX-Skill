# API and CLI overview

Read this reference when choosing a public entry point or inspecting a Python workflow.

## Console entry points

| Command | Owner route | Public purpose |
|---|---|---|
| `mattergen-generate` | [generation](../sub-skills/generation/SKILL.md) | Fire CLI for pretrained/local checkpoint sampling |
| `mattergen-evaluate` | [evaluation](../sub-skills/evaluation/SKILL.md) | Fire CLI for structure loading, relaxation/energy evaluation, metrics, and serialization |
| `csv-to-dataset` | [data preparation](../sub-skills/data-preparation/SKILL.md) | Convert every `.csv` in a folder into MatterGen cache splits |
| `mattergen-train` | [training](../sub-skills/training-finetuning/SKILL.md) | Hydra base/CSP training entry point |
| `mattergen-finetune` | [training](../sub-skills/training-finetuning/SKILL.md) | Hydra adapter fine-tuning entry point |

Run `--help` first. The Fire-based commands accept Python/JSON-like mappings
with shell-sensitive punctuation; Hydra commands accept override grammar and
may need quoting. Help success proves parser importability, not backend or
asset readiness.

## Verified Python objects

- `mattergen.generator.CrystalGenerator` constructs sampling from a
  `MatterGenCheckpointInfo`, conditioning map, batch controls, sampling config,
  guidance factor, target compositions, and trajectory option. Its
  `generate(batch_size=None, num_batches=None, target_compositions_dict=None,
  output_dir='outputs')` returns a list of `pymatgen.core.structure.Structure`.
- `mattergen.common.utils.data_classes.MatterGenCheckpointInfo` accepts
  `model_path`, `load_epoch='last'`, `config_overrides`, `split='val'`, and
  `strict_checkpoint_loading`; `from_hf_hub(model_name,
  repository_name='microsoft/mattergen', config_overrides=None)` resolves a
  named Hub checkpoint.
- `mattergen.evaluation.evaluate.evaluate` accepts structures, either
  relaxation or precomputed energies, an optional reference, matcher, output
  paths, MatterSim potential path, device, and correction scheme, returning a
  metric dictionary.
- `mattergen.common.utils.eval_utils.load_structures(Path)` accepts the
  structure path forms described in the evaluation route.

Exact signatures and workflow caveats belong to the linked sub-skills; do not
reimplement private checkpoint or diffusion internals merely to call these APIs.

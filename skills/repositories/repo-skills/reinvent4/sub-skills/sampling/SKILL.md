---
name: sampling
description: "Configure and troubleshoot REINVENT4 sampling runs for Reinvent,
  LibInvent, LinkInvent, Mol2Mol, and PepInvent generators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Sampling

Use this sub-skill when a user needs to generate molecules with REINVENT4, validate a `sampling` config, adapt a prior or trained agent for generation, or debug seed-file/model/device/output issues for Reinvent, LibInvent, LinkInvent, Mol2Mol, or PepInvent.

## Read First

- `references/workflows.md` for choosing the generator mode, preparing seed files, running `reinvent`, and checking output CSVs.
- `references/configuration.md` for TOML/JSON/YAML keys, templates, CLI flags, model-file handling, and seed-file conventions.
- `references/troubleshooting.md` for model/seed mismatches, CUDA fallback, invalid formats, output collisions, expensive generation, and prior availability.
- `scripts/validate_sampling_config.py` for safe no-run validation before launching generation.

## Fast Path

1. Confirm `run_type = "sampling"` and choose `device = "cpu"` for portable checks or `device = "cuda:0"` only when a CUDA PyTorch device is available.
2. Put `model_file`, `num_smiles`, `output_file`, `unique_molecules`, and `randomize_smiles` under `[parameters]`.
3. Add `smiles_file` for LibInvent, LinkInvent, Mol2Mol, and PepInvent seed-based runs; omit it for normal Reinvent de novo sampling.
4. Validate without generation:
   ```bash
   python sub-skills/sampling/scripts/validate_sampling_config.py sampling.toml --model-mode Linkinvent
   ```
5. Run a small smoke generation before scaling:
   ```bash
   reinvent --device cpu --seed 123 --log-filename sampling.log sampling.toml
   ```

## Scope Boundaries

- This sub-skill owns `run_type = "sampling"`, generator model selection, seed-file conventions, `num_smiles`, uniqueness/randomization, CLI flags, output sanity checks, and static validation.
- For scoring function design, use the `scoring` sub-skill.
- For transfer learning or staged reinforcement learning that produces an agent to sample from, use the `learning` sub-skill, then return here to sample the resulting model.
- For raw SMILES cleanup before creating seed files, use the `data-pipeline` sub-skill.
- For peptide/molecule enumeration workflows, use the `enumeration` sub-skill.

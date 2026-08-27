# RFdiffusion Troubleshooting

## Import Or Install Failures

Symptoms:

- `ModuleNotFoundError: No module named 'rfdiffusion'`
- `ModuleNotFoundError` for `se3_transformer`, `dgl`, `e3nn`, `hydra`, or `omegaconf`
- `pip check` dependency conflicts

Actions:

1. Run `python scripts/check_rfdiffusion_environment.py` from the skill root or with the script path adapted to the installed skill location.
2. Confirm RFdiffusion was installed into the active Python environment.
3. Confirm SE(3)-Transformer, PyTorch, DGL, e3nn, Hydra, OmegaConf, NumPy, and SciPy are available for the workflow.
4. If the user is preparing a new environment, follow the repository install guidance but avoid broad optional installs unless the workflow needs them.

## GPU, CUDA, And CPU Limitations

RFdiffusion can import on CPU, but real inference is typically GPU-oriented and can be slow or impractical on CPU. If a run logs no GPU detected, treat CPU as a diagnostic fallback unless the user explicitly accepts slow runs.

Check:

```bash
python - <<'PY'
import torch
print(torch.__version__)
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')
PY
```

If CUDA is unavailable, match the PyTorch wheel/toolkit to the host driver and avoid claiming a GPU run is ready until `torch.cuda.is_available()` is true.

## Model Weight Failures

Symptoms:

- Missing checkpoint file errors.
- Crashes immediately after sampler selection.
- Unexpected checkpoint/config key mismatches.

Actions:

1. Read `model-weights.md`.
2. Pass `inference.model_directory_path=/path/to/models` when defaults are unclear.
3. Verify explicit `inference.ckpt_override_path` files exist.
4. Use checkpoint overrides only for documented workflows such as active-site scaffolding, complex tasks, or special symmetric motif examples.

## Hydra Quoting Failures

Symptoms:

- Shell errors around brackets or spaces.
- Hydra parser errors for contigs, hotspots, or potentials.
- Chain breaks interpreted incorrectly.

Fix by single-quoting list-like overrides:

```bash
'contigmap.contigs=[A1-150/0 70-100]'
'ppi.hotspot_res=[A59,A83,A91]'
'potentials.guiding_potentials=["type:monomer_contacts,weight:0.05"]'
```

The `/0 ` chain break includes a space before the next block; preserve it inside the quoted string.

## Input PDB And Contig Failures

Symptoms:

- Missing residue or chain errors.
- Length mismatch errors, especially with partial diffusion.
- Motif or hotspot residues not found.

Actions:

1. Check that every chain/residue span in the contig, hotspot list, and mask list exists in the runtime PDB.
2. For partial diffusion, make the contig total residue count match the input structure being noised.
3. For binder tasks, make hotspots refer to target chain PDB numbering in the actual runtime PDB, not source or database numbering after cropping/renumbering.
4. For motif scaffolding, use active-site checkpoint overrides for very small motifs that drift.

## Output Surprises

- `inference.output_prefix` is a prefix; RFdiffusion appends `_0.pdb`, `_0.trb`, and later indices.
- With `inference.cautious=True`, existing output PDBs are skipped instead of overwritten.
- With `inference.write_trajectory=True`, trajectory files can be large and are written under `traj/`.
- Designed residues can appear as glycine placeholders in backbone output; downstream sequence design is a separate step.

## Workflow-Specific Pages

- Binder errors: `../sub-skills/binder-design/references/troubleshooting.md`.
- Contig/motif errors: `../sub-skills/motif-scaffolding/references/troubleshooting.md`.
- Partial diffusion errors: `../sub-skills/partial-diffusion/references/troubleshooting.md`.
- Symmetry errors: `../sub-skills/symmetric-oligomers/references/troubleshooting.md`.
- Potential errors: `../sub-skills/guided-potentials/references/troubleshooting.md`.
- Scaffold-guided errors: `../sub-skills/scaffold-guided-design/references/troubleshooting.md`.
- Macrocycle errors: `../sub-skills/macrocycle-design/references/troubleshooting.md`.

# Motif Scaffolding Troubleshooting

Use this guide when motif scaffolding commands fail, produce unexpected chain layouts, or do not hold the motif geometry.

## Hydra And Shell Quoting

Symptoms:

- Hydra parse errors.
- `no matches found` in shells with globbing.
- Contig arguments split into multiple tokens.

Fixes:

- Wrap list-like overrides in single quotes:

```bash
'contigmap.contigs=[10-40/A163-181/10-40]'
'contigmap.inpaint_seq=[A163-168/A170-171/A179]'
```

- For nested strings in guiding potentials, keep the whole Hydra override single quoted and inner strings double quoted:

```bash
'potentials.guiding_potentials=["type:substrate_contacts,s:1,r_0:8,rep_r_0:5.0,rep_s:2,rep_r_min:1"]'
```

- Do not quote only the bracket body; quote the full `key=value` override.

## Invalid Contigs

Symptoms:

- `Contig string incompatible with --length range`.
- Assertion errors from contig parsing.
- Output chain lengths do not match expectations.

Causes and fixes:

- `contigmap.length` cannot be satisfied by the sampled generated ranges. Broaden the length window or change segment ranges.
- A motif span lacks a chain letter. Use `A10-25`, not `10-25`, for input residues.
- A generated span accidentally has a chain letter. Use numeric spans such as `10-40` for residues RFdiffusion should build.
- Receptor fragments in one receptor block must come from the same chain and increasing residue order.
- Single-residue motifs should be written explicitly as `A1083-1083` for clarity.

## Chain Break Mistakes

Symptoms:

- Target residues appear merged into the designed chain.
- RFdiffusion treats all residues as one chain.
- Target/receptor block contributes to the wrong length accounting.

Fixes:

- Use `/0 ` with a space before the next contig block:

```bash
'contigmap.contigs=[A25-109/0 0-70/B17-29/0-70]'
```

- Keep target/receptor blocks chain-prefixed and ending in `/0`.
- Use `contigmap.length` to constrain the designed chain, not the fixed receptor chain.
- Inspect the `.trb` mappings and output PDB chain IDs after a one-design smoke run.

## Missing PDB Or Residues

Symptoms:

- File-not-found errors for `inference.input_pdb`.
- Key/index errors while processing target or contig residues.
- Motif residues absent from output mappings.

Fixes:

- Confirm `inference.input_pdb` points to a real PDB visible from the run environment.
- Verify chain IDs and residue numbers in the PDB match the contig exactly.
- Check whether the PDB was renumbered, stripped, or has insertion codes.
- Include all chains and ligands required by the contig or substrate potential in the same input PDB.
- Run a minimal `inference.num_designs=1` command before launching a large batch.

## Missing Or Wrong Checkpoint

Symptoms:

- `FileNotFoundError` for `Base_ckpt.pt`, `Complex_base_ckpt.pt`, `InpaintSeq_ckpt.pt`, or `ActiveSite_ckpt.pt`.
- Crash after overriding `inference.ckpt_override_path`.
- Warning that a checkpoint override may be incompatible.

Fixes:

- Set `inference.model_directory_path="$MODEL_DIR"` to a directory containing RFdiffusion model weights.
- Use `inference.ckpt_override_path="$MODEL_DIR/ActiveSite_ckpt.pt"` only for active-site/tiny motif use cases.
- Use `inference.ckpt_override_path="$MODEL_DIR/Complex_base_ckpt.pt"` for complex-finetuned target-aware motif tasks when desired.
- Let RFdiffusion auto-select `InpaintSeq_ckpt.pt` when using `contigmap.inpaint_seq` or `contigmap.inpaint_str` unless there is a strong reason to override.
- Do not use `inference.trb_save_ckpt_path` to select a model; RFdiffusion asserts that model choice belongs in `inference.ckpt_override_path`.

## Install Or Backend Problems

Symptoms:

- `ModuleNotFoundError: rfdiffusion`.
- SE(3)-Transformer import/build errors.
- CUDA or PyTorch compatibility failures.
- Very slow CPU-only execution.

Fixes:

- Activate the environment where RFdiffusion and its SE(3)-Transformer dependency are installed.
- Verify `python -c "import rfdiffusion; import rfdiffusion.contigs"` succeeds.
- Verify PyTorch sees the intended backend with `python -c "import torch; print(torch.cuda.is_available())"`.
- If RFdiffusion logs CPU fallback, expect slow inference and consider moving to a compatible GPU environment.
- Do not encode machine-specific conda prefixes or local checkout paths into reusable commands; use environment variables.

## Motif Drift Or Poor Geometry

Symptoms:

- Tiny catalytic residues move relative to the input motif.
- The scaffold looks plausible but the active-site arrangement is broken.
- Motif alignment fails downstream filtering.

Fixes:

- Use `inference.ckpt_override_path="$MODEL_DIR/ActiveSite_ckpt.pt"` for very small motifs or active sites.
- Confirm every critical residue is included in the contig and not masked with `inpaint_str` unintentionally.
- Avoid masking sequence identity for residues whose sidechain identity is part of the functional motif.
- Generate more designs and filter by motif RMSD/geometry.
- Simplify over-constrained contigs or adjust generated segment ranges if the model cannot satisfy the topology.

## Inpaint Mask Misuse

Symptoms:

- Inpaint masks do not affect intended residues.
- Assertions involving secondary-structure masks.
- Unexpected checkpoint selection.

Fixes:

- Write masks with chain-prefixed residue spans from the input PDB:

```bash
'contigmap.inpaint_seq=[A1/A30-40]'
'contigmap.inpaint_str=[B165-178]'
```

- Ensure masked residues are represented in the contig/input mapping.
- Use `inpaint_seq` for sequence identity masking and `inpaint_str` for coordinate masking.
- Secondary-structure masks must be subsets of `inpaint_str` residues.
- Check the `.trb` `inpaint_seq` entry to confirm the resolved mask.

## Target-Aware Workflow Misuse

Symptoms:

- User asks for binding hotspots but only supplies a motif contig.
- Target chain is present but no interface strategy is defined.
- Complex checkpoint improves context but does not target a binding site.

Fixes:

- Route hotspot-guided PPI design to binder-design guidance using `ppi.hotspot_res`.
- Keep this sub-skill focused on preserving/scaffolding a specified motif in target context.
- If using both motif scaffolding and hotspot-guided binder design, combine guidance carefully and validate route ownership with the sibling sub-skill.

## Active-Site Potential Problems

Symptoms:

- Substrate potential fails because no ligand is found.
- The substrate name does not match any heteroatom record.
- Designs ignore expected substrate contacts.

Fixes:

- Confirm the input PDB includes the ligand/substrate and its residue name matches `potentials.substrate`.
- Use `substrate_contacts` only when the workflow needs ligand-aware active-site guidance.
- Start with one design and inspect logs before running large batches.
- If potential tuning is the main task, consult the auxiliary-potentials guidance if available.

---
name: motif-scaffolding
description: "Design scaffolds around fixed motifs or active sites with
  RFdiffusion contigs, target-chain chain breaks, sequence/structure masking,
  and checkpoint overrides."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Motif Scaffolding

Use this sub-skill when a user needs RFdiffusion to scaffold motif residues from an input PDB, preserve or redesign parts of a motif, include a fixed target chain, or choose a motif-specific checkpoint.

## Route Here

- Scaffold one or more residue spans from an input PDB into a new monomeric scaffold.
- Build around catalytic/active-site residues, especially tiny motifs that drift with the base checkpoint.
- Add a fixed target/receptor chain to a motif-scaffolding contig using `/0 ` chain-break syntax.
- Mask motif sequence with `contigmap.inpaint_seq` or motif structure with `contigmap.inpaint_str`.
- Constrain generated-chain length with `contigmap.length`.
- Choose `ActiveSite_ckpt.pt`, `Complex_base_ckpt.pt`, or automatic inpaint checkpoints.

## Route Elsewhere

- For PPI binder hotspot selection with `ppi.hotspot_res`, route to the binder-design sub-skill.
- For cyclic, dihedral, tetrahedral, or symmetric motif scaffolding, route to the symmetric-oligomers sub-skill.
- For scaffold-guided secondary-structure fold conditioning, route to `../scaffold-guided-design/SKILL.md`.
- For generic unconditional monomer generation, route to `../unconditional-generation/SKILL.md`.

## Inputs To Confirm

- `inference.input_pdb`: a PDB containing every referenced motif, target, and ligand/substrate residue.
- Motif residue identity: chain letters and inclusive residue numbers exactly as they appear in the PDB.
- Generated residue ranges: numeric ranges such as `10-40`; RFdiffusion samples a value each design.
- Chain layout: whether a target chain should remain separate using `/0 ` with a required space after `0`.
- Output prefix: a writable prefix such as `$OUT_DIR/motif_run`.
- Model weights: default model directory, or explicit checkpoint path for active-site/complex use.
- Number of designs and optional deterministic/restart behavior.

## Core Command Shape

Run from an RFdiffusion installation where `rfdiffusion` imports and the installed `run_inference.py` launcher is available:

```bash
run_inference.py \
  inference.output_prefix="$OUT_DIR/motif_scaffold" \
  inference.input_pdb="$INPUT_PDB" \
  inference.model_directory_path="$MODEL_DIR" \
  inference.num_designs=10 \
  'contigmap.contigs=[10-40/A163-181/10-40]'
```

Keep Hydra list-like overrides in single quotes. Do not let the shell interpret brackets, commas, spaces, or embedded quotes.

## Contig Decisions

- Use `A10-25` for residues 10 through 25 on chain `A` from `inference.input_pdb`.
- Use `5-15` for a generated segment whose length is sampled independently each design.
- Use `5-15/A10-25/30-40` to build N-terminal and C-terminal scaffold segments around one motif.
- Use `A25-109/0 0-70/B17-29/0-70` to keep target chain `A25-109` separate from a generated chain that contains motif `B17-29`.
- Use `contigmap.length=70-120` when variable segment ranges must produce a generated chain in a total length window.
- Use multiple motif fragments in one generated chain as `10-100/A1083-1083/10-100/A1051-1051/10-100`.

See `references/contig-patterns.md` for validated patterns and interpretation rules.

## Standard Workflows

- Simple motif scaffolding: input PDB plus contig such as `10-40/A163-181/10-40`.
- Motif sequence redesign: add `contigmap.inpaint_seq` for nonessential motif residues that should have masked amino-acid identity.
- Target-aware motif scaffolding: include the fixed target/receptor as a receptor block before `/0 ` and use a complex checkpoint when needed.
- Active-site/enzyme scaffolding: use several single-residue motif fragments and usually `inference.ckpt_override_path=$MODEL_DIR/ActiveSite_ckpt.pt`.
- Structure masking: use `contigmap.inpaint_str` when coordinates for selected input residues should be hidden while preserving sequence context.

Detailed commands are in `references/workflows.md`.

## Checkpoint Selection

- Default motif scaffolding normally uses `$MODEL_DIR/Base_ckpt.pt` via RFdiffusion's automatic checkpoint choice.
- `contigmap.inpaint_seq`, `contigmap.inpaint_str`, or `contigmap.provide_seq` triggers an inpaint-capable checkpoint automatically unless `inference.ckpt_override_path` is set.
- Fixed target/complex motif tasks can use `inference.ckpt_override_path=$MODEL_DIR/Complex_base_ckpt.pt` when the complex-finetuned model is desired.
- Tiny active-site motifs should use `inference.ckpt_override_path=$MODEL_DIR/ActiveSite_ckpt.pt` to reduce motif drift.
- If overriding, verify checkpoint compatibility with the provided contig and masks; incompatible model/config features can crash at inference.

## Sequence And Structure Masking

- `contigmap.inpaint_seq` masks amino-acid identities for selected input residues, letting RFdiffusion reason over better identities while keeping the motif coordinates in context.
- Use inclusive chain-residue spans: `'contigmap.inpaint_seq=[A163-168/A170-171/A179]'`.
- `contigmap.inpaint_str` masks structure for selected input residues and uses an inpaint-capable checkpoint.
- Do not mask residues that are absent from the contig/input PDB mapping.
- For residues that must remain functionally fixed, leave sequence and structure unmasked.

## Target Chains And Chain Breaks

- The `/0 ` token creates a 200-residue index jump so RFdiffusion treats following residues as a separate chain.
- The space after `/0` is semantically important because contig parsing splits receptor and inpaint blocks by whitespace.
- A target block made only of chain-prefixed residues plus final `/0` is treated as a receptor/fixed chain.
- `contigmap.length` applies to the generated/inpaint chain length, not necessarily fixed receptor length.
- For hotspot-guided binder design with `ppi.hotspot_res`, switch to binder-design guidance rather than this sub-skill alone.

## Validation Checklist

- PDB exists and contains every chain/residue span in `contigmap.contigs`, `contigmap.inpaint_seq`, and `contigmap.inpaint_str`.
- Contig override is single quoted and passed as one Hydra argument.
- Any target chain break is written as `/0 `, not `/0/` or `/0` without the separating space when a new block follows.
- `contigmap.length` is compatible with the generated segment ranges; incompatible ranges can loop and exit with a length error.
- Model weights include the checkpoint named by `inference.ckpt_override_path` or the automatically selected file under `inference.model_directory_path`.
- Outputs include `*.pdb` and `*.trb`; the `.trb` records the sampled contig and residue mappings.
- Motif residues in output should be inspected/aligned against the input motif; tiny active sites may need `ActiveSite_ckpt.pt`.

## Common Fixes

- Hydra parse error: wrap list overrides in single quotes and avoid unquoted brackets.
- Missing checkpoint: set `inference.model_directory_path=$MODEL_DIR` or pass the correct `inference.ckpt_override_path`.
- Missing residues: check PDB numbering and chain IDs; residue insertion codes or renumbered files often cause mismatches.
- Motif drift: use the active-site checkpoint for very small motifs, reduce design difficulty, or tighten motif definition.
- Target merges with scaffold: correct `/0 ` chain-break syntax and confirm the fixed target block is chain-prefixed.

See `references/troubleshooting.md` for diagnosis details.

## Outputs To Explain

- Final `*.pdb` contains backbone design output; designed residues are written as glycine while motif residues can retain identity context.
- `*.trb` stores config, sampled contig, mappings such as motif input/output indices, and inpaint masks.
- `traj/` contains reverse-ordered trajectory PDBs when `inference.write_trajectory=True`.
- Use `.trb` mappings for downstream motif alignment, sequence design, and filtering.

## Minimal Examples

Use these as templates after replacing paths:

```bash
run_inference.py \
  inference.output_prefix="$OUT_DIR/design_motifscaffolding" \
  inference.input_pdb="$INPUT_PDB" \
  inference.model_directory_path="$MODEL_DIR" \
  'contigmap.contigs=[10-40/A163-181/10-40]' \
  inference.num_designs=10
```

```bash
run_inference.py \
  inference.output_prefix="$OUT_DIR/design_motif_with_target" \
  inference.input_pdb="$INPUT_PDB" \
  inference.model_directory_path="$MODEL_DIR" \
  'contigmap.contigs=[A25-109/0 0-70/B17-29/0-70]' \
  contigmap.length=70-120 \
  inference.ckpt_override_path="$MODEL_DIR/Complex_base_ckpt.pt" \
  inference.num_designs=10
```

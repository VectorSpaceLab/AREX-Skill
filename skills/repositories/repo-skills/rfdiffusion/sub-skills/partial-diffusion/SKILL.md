---
name: partial-diffusion
description: "Diversify an existing RFdiffusion backbone or complex with partial
  diffusion, including partial_T selection, contig length matching, provide_seq
  sequence preservation, deterministic smoke checks, and output validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Partial Diffusion

Use this sub-skill when the user wants RFdiffusion to start from an existing `inference.input_pdb` and sample nearby structures by adding and denoising a limited amount of noise. This is the route for fold diversification, complex diversification, and peptide-complex refinement where the generated topology should remain close to an input backbone.

For general de novo generation without an input backbone, route to `../unconditional-generation/` if present. For binder target selection, hotspots, or de novo binder strategy, route to `../binder-design/` if present, then return here only for the partial-diffusion diversification stage.

## What Partial Diffusion Controls

- `diffuser.partial_T` sets how many diffusion steps to noise from the known structure before denoising.
- Larger `partial_T` usually gives more diversity and more drift from the input.
- RFdiffusion defaults to `diffuser.T=50`; historical `partial_T=80` under a 200-step schedule is roughly comparable to `partial_T=20` under `T=50`.
- `inference.input_pdb` is required because partial diffusion needs coordinates to noise.
- `contigmap.contigs` must describe an output with exactly the same total residue count as the input structure used for partial diffusion.
- `contigmap.provide_seq` can preserve sequence identity for selected positions inside diffused regions.

## Minimum Command Pattern

Use the installed RFdiffusion script entrypoint, not a repository-relative script path:

```bash
run_inference.py \
  inference.input_pdb=/path/to/input.pdb \
  inference.output_prefix=outputs/partial/design \
  'contigmap.contigs=[79-79]' \
  diffuser.partial_T=10 \
  inference.num_designs=10
```

Expected outputs are `outputs/partial/design_0.pdb`, `outputs/partial/design_0.trb`, and additional numbered designs. If `inference.write_trajectory=True` remains enabled, trajectory PDBs are written under a sibling `traj/` directory.

## Required Setup Decisions

1. Confirm the input PDB exists and has the chains/residue spans the contig will reference.
2. Count the total residues represented by the partial-diffusion contig.
3. Make that total match the input PDB length after any intended chain/residue selection.
4. Choose `diffuser.partial_T` by desired diversity, commonly starting near `10` for local changes or near `20` for stronger diversification under default `diffuser.T=50`.
5. Decide whether any sequence positions should be preserved with `contigmap.provide_seq`.
6. Set an output prefix in a writable directory.

## Whole-Backbone Diversification

Use this when all residues in a monomer should be noised and denoised while preserving the same length:

```bash
run_inference.py \
  inference.input_pdb=/path/to/79_residue_input.pdb \
  inference.output_prefix=outputs/partial/whole_backbone \
  'contigmap.contigs=[79-79]' \
  diffuser.partial_T=10 \
  inference.num_designs=10
```

This pattern is appropriate when the input PDB is a 79-residue monomer and every residue participates in partial diffusion. For a different input length, replace both numbers in `[79-79]` with the actual length.

## Diversify One Chain While Keeping a Partner Present

Use a chain break `/0` in the contig for complexes. For example, to diversify a 100-residue binder while keeping a 150-residue target chain represented:

```bash
run_inference.py \
  inference.input_pdb=/path/to/binder_target_complex.pdb \
  inference.output_prefix=outputs/partial/binder_context \
  'contigmap.contigs=[100-100/0 B1-150]' \
  diffuser.partial_T=20 \
  inference.num_designs=10
```

The total contig length is `100 + 150 = 250`, so the relevant input complex must also provide 250 residues in the order RFdiffusion will map. If the user is asking how to choose target hotspots or binder length from scratch, route that design strategy to `../binder-design/` first.

## Preserve Sequence With provide_seq

Use `contigmap.provide_seq` when coordinates may move but selected sequence identities should remain fixed. Positions are zero-indexed over the full contig, not per-chain, and ranges are inclusive.

For a 172-residue scaffold plus a 34-residue peptide where the peptide sequence should be preserved:

```bash
run_inference.py \
  inference.input_pdb=/path/to/peptide_complex.pdb \
  inference.output_prefix=outputs/partial/peptide_sequence_preserved \
  'contigmap.contigs=["172-172/0 34-34"]' \
  diffuser.partial_T=10 \
  inference.num_designs=10 \
  'contigmap.provide_seq=[172-205]'
```

For multiple disjoint sequence-preserved ranges:

```bash
run_inference.py \
  inference.input_pdb=/path/to/peptide_complex.pdb \
  inference.output_prefix=outputs/partial/peptide_terminal_sequence_preserved \
  'contigmap.contigs=["172-172/0 34-34"]' \
  diffuser.partial_T=10 \
  inference.num_designs=10 \
  'contigmap.provide_seq=[172-177,200-205]'
```

The `provide_seq` checkpoint/model selection is handled by RFdiffusion inference. Still ensure model weights are installed and discoverable before running.

## Deterministic Smoke Test

Before launching many designs, run one deterministic design and stop near the start of denoising to catch malformed inputs quickly:

```bash
run_inference.py \
  inference.input_pdb=/path/to/input.pdb \
  inference.output_prefix=outputs/smoke/partial \
  'contigmap.contigs=[79-79]' \
  diffuser.partial_T=10 \
  inference.num_designs=1 \
  inference.deterministic=True \
  inference.final_step=8
```

For these smoke checks, `inference.final_step` is commonly set to `partial_T - 2` when `partial_T` is greater than `2`. Do not use this as a scientific production setting without understanding the shortened trajectory; it is a fast validation pattern.

## Output Validation

After a run, check:

- A numbered `.pdb` exists for each requested design that was not skipped by cautious mode.
- A matching `.trb` metadata file exists for each design.
- The output PDB residue count matches the intended contig length.
- Preserved `provide_seq` positions retain the intended sequence identities.
- The `.trb` config records the expected `diffuser.partial_T`, `contigmap.contigs`, `contigmap.provide_seq`, and `inference.input_pdb` values.
- If trajectories are enabled, the `traj/` outputs exist and are useful for inspecting denoising behavior.

## Common Routing Decisions

- User asks “make new proteins of length N” without an input PDB: route to `../unconditional-generation/`.
- User asks “diversify this fold/complex/peptide around an input PDB”: use this sub-skill.
- User asks “which target residues should a binder contact?”: route to `../binder-design/` for hotspot strategy, then use this sub-skill only if they also want partial diffusion around a known complex.
- User asks “why did the length change or fail?”: inspect `contigmap.contigs` first; partial diffusion requires the contig total to match the input length.
- User asks “why was my peptide sequence redesigned?”: inspect zero-indexed `contigmap.provide_seq` ranges and confirm they cover the intended global contig positions.

## More Detail

- Use `references/workflows.md` for complete command templates and decision recipes.
- Use `references/troubleshooting.md` for failures related to quoting, contig mismatches, missing files, model weights, and sequence-preservation surprises.

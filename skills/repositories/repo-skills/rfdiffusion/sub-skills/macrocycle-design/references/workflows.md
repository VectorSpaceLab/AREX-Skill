# Macrocycle Workflows

This reference gives self-contained RFpeptides macrocycle command patterns for RFdiffusion. Replace all paths with paths that exist in the user's runtime environment.

## Shell Safety Rules

RFdiffusion commands use Hydra overrides. In shell commands:

- Quote contig lists: `'contigmap.contigs=[12-18]'`.
- Quote hotspot lists: `'ppi.hotspot_res=[A51,A52,A50]'`.
- Keep `inference.cyc_chains='a'` as a quoted string value.
- Use `--config-name base` when mirroring repository RFpeptides examples.
- Do not embed original checkout-relative example paths in public commands; use the user's installed launcher and PDB paths.

If a shell, scheduler, or wrapper strips hotspot list values, use an escaped-entry variant:

```bash
ppi.hotspot_res=[\'A51\',\'A52\',\'A50\']
```

Use only one hotspot override form in a command.

## Macrocyclic Monomer

Use this when the user wants standalone cyclic peptide backbones with no target protein.

```bash
run_inference.py \
  --config-name base \
  inference.output_prefix=outputs/macrocycle_monomer/design \
  inference.num_designs=10 \
  'contigmap.contigs=[12-18]' \
  inference.cyclic=True \
  diffuser.T=50 \
  inference.cyc_chains='a'
```

Adjust the length range to the requested macrocycle size, for example `'contigmap.contigs=[8-12]'` or `'contigmap.contigs=[20-24]'`. Keep `inference.cyc_chains='a'` for a single generated macrocycle chain.

Recommended pilot variant:

```bash
run_inference.py \
  --config-name base \
  inference.output_prefix=outputs/macrocycle_monomer_pilot/design \
  inference.num_designs=1 \
  'contigmap.contigs=[12-18]' \
  inference.cyclic=True \
  diffuser.T=50 \
  inference.cyc_chains='a' \
  inference.deterministic=True \
  inference.write_trajectory=False \
  inference.cautious=True
```

This checks command parsing and model setup with minimal output volume. It is not a substitute for a production-quality batch.

## Macrocyclic Binder

Use this when the generated cyclic peptide should bind a fixed target protein site.

```bash
run_inference.py \
  --config-name base \
  inference.output_prefix=outputs/macrocycle_binder/design \
  inference.num_designs=10 \
  'contigmap.contigs=[12-18 A3-117/0]' \
  inference.input_pdb=target.pdb \
  inference.cyclic=True \
  diffuser.T=50 \
  inference.cyc_chains='a' \
  'ppi.hotspot_res=[A51,A52,A50,A48,A62,A65]'
```

Interpretation:

- `12-18` creates the generated macrocyclic peptide.
- `A3-117` keeps target chain `A` residues 3 through 117 from `target.pdb`.
- `/0` creates the RFdiffusion chain break after the target segment in this RFpeptides-style contig.
- `inference.cyc_chains='a'` cyclizes the generated peptide chain.
- `ppi.hotspot_res` points to target residues in `target.pdb` numbering.

If the target PDB is cropped or renumbered, update both `A3-117` and hotspots to the exact file. Repository RFpeptides examples note that their GABARAP example target chain A is shifted by `+2` relative to the original PDB ID; users should not copy those residue numbers unless their local PDB has the same numbering.

## Multiple Cyclic Chains

RFdiffusion accepts a string of cyclic chain IDs, for example:

```bash
inference.cyc_chains='abcd'
```

Use this only when the contig actually creates compatible generated chains corresponding to those chain IDs. Do not add target chain letters to `inference.cyc_chains`. If the user's real goal is a cyclic oligomer with symmetry, route to the symmetric-oligomer workflow rather than forcing it through RFpeptides macrocycle flags.

## Choosing Contigs

Common patterns:

- Short monomer macrocycle: `'contigmap.contigs=[8-12]'`.
- RFpeptides-like monomer range: `'contigmap.contigs=[12-18]'`.
- Fixed-size macrocycle: `'contigmap.contigs=[14-14]'`.
- Binder with a target crop: `'contigmap.contigs=[12-18 A20-95/0]'`.
- Binder with a different target chain: `'contigmap.contigs=[12-18 B10-140/0]'` with hotspots like `'ppi.hotspot_res=[B42,B45,B88]'`.

Avoid mixing target and peptide roles. The generated macrocycle segment is the chain to cyclize; target PDB residues are fixed context for binder design.

## Hotspot Selection For Macrocyclic Binders

The macrocycle binder command uses the same RFdiffusion `ppi.hotspot_res` input as classic binder design, with macrocycle-specific checks:

- Hotspots must be on the target chain, not on the generated macrocycle.
- Hotspots must fall inside the target span retained by `contigmap.contigs`.
- A small set of 3-6 interface residues is a reasonable starting point.
- Do not expect every listed hotspot to become a final contact; use output inspection and downstream interface checks.
- If hotspots are omitted, the run is no longer targeted to a specific binding site even though the peptide is cyclic.

For broader hotspot strategy, target cropping, and non-cyclic PPI troubleshooting, use the sibling `binder-design` sub-skill.

## Output Review

After generation:

1. Confirm the expected files exist: `output_prefix_0.pdb`, `output_prefix_0.trb`, and additional indexed outputs.
2. Open the PDB and confirm the macrocycle chain is the generated peptide chain selected by `inference.cyc_chains`.
3. For binder runs, verify target and macrocycle chains are both present and the target residues are not accidentally treated as cyclic chains.
4. Confirm the resolved config in the `.trb` records `inference.cyclic=True`, the intended `cyc_chains`, `diffuser.T=50`, and the contig string.
5. Triage contacts to hotspots visually or with the user's preferred structure analysis tool before committing to large campaigns.

RFdiffusion outputs are backbone candidates. Sequence design, structure prediction, and interface assessment remain downstream steps outside this sub-skill's runtime responsibility.

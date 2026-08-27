# Potential Reference

This reference is distilled from RFdiffusion's potential source and inference config. It is intended for command construction and troubleshooting, not for modifying RFdiffusion internals.

## How RFdiffusion Parses Potentials

`potentials.guiding_potentials` is either `null` or a list of strings. Each string is split on commas, then each entry is split on `:`. The `type` field is kept as a string and all other fields are converted to floats.

Correct shell pattern:

```bash
'potentials.guiding_potentials=["type:monomer_ROG,weight:1,min_dist:5"]'
```

Multiple potentials are possible as multiple strings in the list:

```bash
'potentials.guiding_potentials=["type:monomer_ROG,weight:1,min_dist:5","type:monomer_contacts,weight:0.02"]'
```

Use multiple potentials cautiously. Pilot one potential at a time first so that failures are interpretable.

Global potential config values from the base inference config:

- `potentials.guiding_potentials=null`
- `potentials.guide_scale=10`
- `potentials.guide_decay=constant`
- `potentials.olig_inter_all=null`
- `potentials.olig_intra_all=null`
- `potentials.olig_custom_contact=null`
- `potentials.substrate=null`

The default `guide_scale=10` is not necessarily a good starting point for every use. Repository examples commonly use smaller explicit values such as `2` for monomer RoG or oligomer contacts and `1` for substrate contacts.

## Implemented Potentials

### `monomer_ROG`

Purpose: encourage compact monomer designs by minimizing radius of gyration over C-alpha atoms.

Arguments:

- `weight`, default `1`
- `min_dist`, default `15`

Example:

```bash
'potentials.guiding_potentials=["type:monomer_ROG,weight:1,min_dist:5"]' potentials.guide_scale=2 potentials.guide_decay=quadratic
```

Use when a de novo or motif-scaffolded monomer is too extended. It may be unnecessary for ordinary unconditional generation, so compare against a no-potential baseline.

### `monomer_contacts`

Purpose: increase differentiable intra-chain C-alpha contacts in a monomer.

Arguments:

- `weight`, default `1`
- `r_0`, default `8`
- `d_0`, default `2`
- `eps`, default `1e-6`

Example:

```bash
'potentials.guiding_potentials=["type:monomer_contacts,weight:0.05"]'
```

The source comments note that this contact form can sometimes produce NaN gradients; RFdiffusion has gradient checks elsewhere, but overly aggressive weights are still risky.

### `olig_contacts`

Purpose: add attractive or repulsive contact objectives within and between chains of symmetric oligomer designs.

Arguments:

- `weight_intra`, default `1`
- `weight_inter`, default `1`
- `r_0`, default `8`
- `d_0`, default `2`

Additional global settings:

- `potentials.olig_intra_all=True` marks every diagonal chain-pair entry attractive.
- `potentials.olig_inter_all=True` marks every off-diagonal chain-pair entry attractive.
- `potentials.olig_custom_contact=<string>` supplies selected attractive or repulsive chain pairs.

Example for all intra-chain and all inter-chain contacts:

```bash
'potentials.guiding_potentials=["type:olig_contacts,weight_intra:1,weight_inter:0.1"]' \
  potentials.olig_intra_all=True \
  potentials.olig_inter_all=True \
  potentials.guide_scale=2 \
  potentials.guide_decay=quadratic
```

Custom contact strings use three-character chain-pair tokens. The first and third characters are chain letters from `A` onward; the middle character is `&` for attraction or `!` for repulsion. Tokens are comma-separated.

Examples:

- `A&B`: attractive contacts between chains A and B.
- `A!C`: repulsive contacts between chains A and C.
- `A&B,B&C,A!D`: combined custom matrix.

Symmetry determines chain count:

- `C6` gives 6 chains.
- `D2` gives 4 chains.
- `tetrahedral` uses 12 chains in the source helper.

For symmetric oligomers, start from repository-style weights where intra-chain contact strength is larger than inter-chain contact strength.

### `binder_ROG`

Purpose: compact only the binder segment of a binder-style run.

Arguments:

- `weight`, default `1`
- `min_dist`, default `15`

Example:

```bash
'potentials.guiding_potentials=["type:binder_ROG,weight:0.5,min_dist:15"]'
```

Requires RFdiffusion to infer `binderlen`. This is normally available in binder/PPI-style contig workflows. Do not use it for pure unconditional monomer generation.

### `binder_ncontacts`

Purpose: increase differentiable contacts within the binder segment.

Arguments:

- `weight`, default `1`
- `r_0`, default `8`
- `d_0`, default `4`

Example:

```bash
'potentials.guiding_potentials=["type:binder_ncontacts,weight:0.05,r_0:8,d_0:4"]'
```

Requires `binderlen`. The implementation prints `BINDER CONTACTS:` during inference, so expect extra log output.

### `interface_ncontacts`

Purpose: increase contacts across binder and target segments.

Arguments:

- `weight`, default `1`
- `r_0`, default `8`
- `d_0`, default `6`

Example:

```bash
'potentials.guiding_potentials=["type:interface_ncontacts,weight:0.05,r_0:8,d_0:6"]'
```

Requires `binderlen`. The implementation prints `INTERFACE CONTACTS:` during inference. Use extra care in hotspot-guided PPI: source documentation warns that auxiliary potentials can interact oddly with hotspot residues.

### `dimer_ROG`

Purpose: compact both halves of a dimer-style design.

Arguments:

- `weight`, default `1`
- `min_dist`, default `15`

Example:

```bash
'potentials.guiding_potentials=["type:dimer_ROG,weight:0.5,min_dist:15"]'
```

Requires `binderlen` and assumes two segments based on that length. Prefer sibling symmetric-oligomer guidance for true symmetry setup.

### `substrate_contacts`

Purpose: implicitly model contacts between a scaffolded active site and a substrate residue found in the input motif PDB.

Arguments:

- `weight`, default `1`
- `r_0`, default `8`
- `d_0`, default `2`
- `s`, default `1`
- `eps`, default `1e-6`
- `rep_r_0`, default `5`
- `rep_s`, default `2`
- `rep_r_min`, default `1`

Additional global setting:

- `potentials.substrate=<three-letter residue name>` such as `LLK`.

Example:

```bash
'potentials.guiding_potentials=["type:substrate_contacts,s:1,r_0:8,rep_r_0:5.0,rep_s:2,rep_r_min:1"]' \
  potentials.substrate=LLK \
  potentials.guide_scale=1
```

Use with active-site motif scaffolding and an input PDB that contains the substrate residue. It also relies on the active-site/motif plumbing to provide motif coordinates and diffusion masks, so route contig and checkpoint questions to motif scaffolding first.

## Guide Scale And Decay

`potentials.guide_scale` multiplies the potential guidance vector. Larger values increase the bias and can damage designs if too strong.

`potentials.guide_decay` choices:

- `constant`: same scale throughout denoising.
- `linear`: proportional to current timestep.
- `quadratic`: squared timestep fraction; repository examples use this for monomer RoG and oligomer contacts.
- `cubic`: cubed timestep fraction.

The decay implementation makes guidance strongest early in reverse diffusion and weaker near the end for linear/quadratic/cubic schedules.

## PPI And Hotspot Caveat

RFdiffusion's README explicitly cautions that auxiliary potentials can interact oddly with hotspot residues in PPI. For binder design:

1. Build and validate the binder command with hotspots first.
2. Run a no-potential baseline.
3. Add only one conservative binder or interface potential for a small pilot.
4. Compare interface geometry, target contact location, and design failure modes before scaling.

If the user only asks how to choose hotspots or build a binder contig, route to `../binder-design/SKILL.md` instead of starting with potentials.

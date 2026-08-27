# Guided Potential Troubleshooting

Use this guide when an RFdiffusion command fails after adding `potentials.*` overrides or when outputs become worse after potential tuning.

## Hydra Quoting Failures

Symptoms:

- Hydra reports a parse error near brackets, commas, or quotes.
- The shell strips quotes before RFdiffusion sees the list.
- `potentials.guiding_potentials` is interpreted as a string instead of a list.

Fix:

```bash
'potentials.guiding_potentials=["type:monomer_ROG,weight:1,min_dist:5"]'
```

Rules:

- Quote the whole Hydra override with single quotes in shell commands.
- Put each potential string inside the list with double quotes.
- Keep commas inside the potential string for potential parameters.
- For multiple potentials, separate the quoted strings with commas inside one list.

Avoid these forms:

```bash
potentials.guiding_potentials=[type:monomer_ROG,weight:1]
potentials.guiding_potentials="type:monomer_ROG,weight:1"
'potentials.guiding_potentials=[type:monomer_ROG,weight:1]'
```

## Unknown Potential Name

Symptom:

```text
potential with name: <name> is not one of the implemented potentials
```

Fixes:

- Use one of the implemented names exactly: `monomer_ROG`, `binder_ROG`, `dimer_ROG`, `binder_ncontacts`, `interface_ncontacts`, `monomer_contacts`, `olig_contacts`, or `substrate_contacts`.
- Check capitalization. `monomer_ROG` is valid; `monomer_rog` is not.
- Use `substrate_contacts`, not the singular phrase sometimes seen in prose.

## Non-Numeric Potential Arguments

Symptom:

- A `ValueError` occurs while parsing potential values as floats.
- RFdiffusion fails before starting inference.

Cause:

The potential manager converts every per-potential key except `type` to `float`.

Fix:

- Use `weight:1`, not `weight:strong`.
- Use `rep_r_min:1`, not `rep_r_min:true`.
- Put global string settings outside the potential string, such as `potentials.substrate=LLK`.

## Bad Guide Decay

Symptom:

```text
decay_type must be one of ... Received decay_type=<value>
```

Fix:

Use exactly one of:

- `potentials.guide_decay=constant`
- `potentials.guide_decay=linear`
- `potentials.guide_decay=quadratic`
- `potentials.guide_decay=cubic`

For example-style compactness or oligomer contacts, prefer `quadratic` unless the user is intentionally testing a different schedule.

## Potentials Too Strong

Symptoms:

- Generated structures collapse or become distorted.
- Motifs drift or no longer preserve the intended geometry.
- Binder designs contact the wrong region despite hotspots.
- Success rate drops compared with the baseline.

Fixes:

- Compare against a no-potential baseline.
- Reduce `potentials.guide_scale` first.
- Reduce the per-potential `weight` second.
- Use a decaying guide such as `quadratic` instead of `constant`.
- Change one parameter at a time and run small pilots.

## `olig_contacts` Without Symmetry

Symptoms:

- Initialization errors because `contact_matrix` is missing.
- The command does not know how many chains to build a contact matrix for.

Cause:

The manager creates the oligomer contact matrix from `inference.symmetry`. Without symmetry, `olig_contacts` does not receive the required matrix.

Fix:

- Route symmetry setup to the symmetric-oligomer sub-skill first.
- Use a symmetry config and set `inference.symmetry`, such as `C6`, `D2`, or `tetrahedral`.
- Use `potentials.olig_intra_all=True`, `potentials.olig_inter_all=True`, or a valid `potentials.olig_custom_contact` string.

## Bad Oligomer Custom Contact String

Symptoms:

- Assertion failure while parsing the contact string.
- Custom chain-pair matrix behaves unexpectedly.

Rules:

- Each token must be exactly three characters.
- First and third characters are chain letters: `A`, `B`, `C`, and so on.
- Middle character is `&` for attractive or `!` for repulsive.
- Tokens are comma-separated: `A&B,A!C,B&C`.
- Chain letters must exist for the symmetry-derived chain count.

Examples:

```bash
potentials.olig_custom_contact='A&B,A!C'
```

For C2, only chains A and B exist, so a token involving C is invalid. For D2, chains A-D exist.

## Binder Potential Without Binder Length

Symptoms:

- Initialization fails with missing `binderlen`.
- A binder-specific potential does not behave as intended.

Affected potentials:

- `binder_ROG`
- `binder_ncontacts`
- `interface_ncontacts`
- `dimer_ROG`

Fix:

- Use these only in binder/PPI or dimer-style workflows where RFdiffusion can infer a binder segment length.
- For plain de novo monomers, use `monomer_ROG` or `monomer_contacts` instead.
- Route target/binder contig construction to `../binder-design/SKILL.md`.

## Hotspot Interaction Problems

Symptoms:

- Binder ignores hotspots after adding a potential.
- Interface is contact-rich but at the wrong target site.
- Designs get worse despite better compactness/contact metrics.

Cause:

RFdiffusion repository guidance warns that auxiliary potentials can interact oddly with hotspot residues in PPI workflows.

Fix:

1. Run the same binder command without potentials.
2. Keep the hotspot list small and target-relevant.
3. Add one conservative potential at a time.
4. Use small batches and inspect whether contacts still localize around hotspots.
5. Prefer route-level binder design fixes over increasing potential strength.

## Substrate Contact Failures

Symptoms:

- The substrate contact potential cannot find substrate atoms.
- Alignment assertions fail.
- The active-site run starts but substrate guidance is nonsensical.

Checklist:

- `potentials.substrate=<resname>` is set outside the potential string.
- The input PDB contains that residue name exactly, including capitalization.
- The motif residues in the contig are present in the input PDB.
- The active-site/motif residues are sufficient to define a frame.
- The selected checkpoint is suitable for small active-site motifs when required.
- The input PDB has usable atom coordinates for the substrate residue.

A correct substrate potential override looks like:

```bash
'potentials.guiding_potentials=["type:substrate_contacts,s:1,r_0:8,rep_r_0:5.0,rep_s:2,rep_r_min:1"]' potentials.substrate=LLK potentials.guide_scale=1
```

## NaN Or Gradient Warnings

Symptoms:

- Logs mention NaN gradients.
- Outputs fail after adding contact-style potentials.

Likely causes:

- Contact potentials are too strong.
- Structures are driven into extremely close contacts.
- Multiple potentials over-constrain the run.

Fixes:

- Lower `weight` and `guide_scale`.
- Use a decaying schedule.
- Pilot only one potential.
- Compare with `monomer_ROG` or `binder_ROG` if contact potentials are unstable.

## Validator Helper

The bundled validator can catch many command-construction mistakes before inference:

```bash
python sub-skills/guided-potentials/scripts/validate_potential_override.py \
  --guiding-potentials '["type:substrate_contacts,s:1,r_0:8,rep_r_0:5.0,rep_s:2,rep_r_min:1"]' \
  --substrate LLK \
  --guide-decay quadratic
```

It does not validate structural biology correctness, model weights, GPU availability, or whether an input PDB actually contains a substrate residue. Use it as a syntax and source-rule check only.

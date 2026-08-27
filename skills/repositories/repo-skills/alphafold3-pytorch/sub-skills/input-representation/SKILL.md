---
name: input-representation
description: "Build, validate, batch, serialize, and export AlphaFold 3 molecule
  and atom inputs without running model inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Input representation

Use this sub-skill when a task starts from protein, RNA, DNA, ligand, or metal
entities and needs a valid AlphaFold 3 input graph, atom-level features,
collation, serialization, or structure-output conversion.

## Route first

1. Read [the API contract](references/input-api.md) for entity fields and the
   conversion chain.
2. Read [the feature and shape contract](references/feature-and-shape-contracts.md)
   before supplying tensors, custom embeddings, masks, or windows.
3. Use [the workflows](references/workflows.md) for direct construction,
   heterogeneous batches, round trips, and coordinate export.
4. Use [troubleshooting](references/troubleshooting.md) when validation fails.
5. Run `scripts/inspect_input.py --help` before using the bundled, no-inference
   validator. It accepts a small JSON specification, emits deterministic
   summaries, and can validate a temporary serialization round trip.

The normal conversion is:

`Alphafold3Input` → molecule-length input → `AtomInput` →
`BatchedAtomInput` → model-facing keyword arguments.

Prefer `Alphafold3Input` for sequence/SMILES/ion descriptions and `AtomInput`
when atom-level features already exist. Keep MSA, template, PDB/mmCIF loading,
cropping, and dataset preparation in [data-pipeline](../data-pipeline/SKILL.md).
Keep forward, loss, sampling, checkpoint, and confidence behavior in
[model-inference](../model-inference/SKILL.md). Keep trainer and dataloader
configuration in [training-configuration](../training-configuration/SKILL.md).

## Operating guardrails

- Validate entity alphabets, molecule counts, atom indices, feature dimensions,
  and padding before a model call.
- Double-stranded sequences are represented by the supplied strand followed by
  its reverse complement; do not add the complement a second time.
- A direct `Alphafold3Input` must contain at least one supported entity. Use
  explicit `AtomInput` data for precomputed or unusual atom-level cases.
- The inspection helper never downloads data, trains, starts a server, or runs
  a model. It is a preflight tool, not a structure-quality check.
- Treat output coordinates as a separate contract: model sampling is normally
  `[batch, atoms, 3]`, while standalone `alphafold3_input_to_biomolecule`
  expects token-major `[tokens, 47, 3]` coordinates. Do not interchange them.

---
name: input-data-formats
description: "Author, validate, and debug Chai FASTA input records for proteins,
  ligands, DNA, RNA, modified residues, entity names, and chain naming."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Input Data Formats

Use this sub-skill when an agent needs to create or repair Chai input FASTA records before folding. It covers entity headers, sequences, ligand SMILES, modified residues, entity names, and the chain-name consequences of `fasta_names_as_cif_chains` / `entity_name_as_subchain`.

## Route First

- Need to run `chai-lab fold` or `chai_lab.chai1.run_inference` after the FASTA is valid? Use `../cli-inference/SKILL.md`.
- Need `.aligned.pqt`, A3M conversion, MSA server, or template hit files? Use `../msa-templates/SKILL.md`.
- Need contact/pocket/covalent restraint CSVs or glycan bond details? Use `../restraints-glycans/SKILL.md`.
- Need only basic `glycan|name` FASTA routing? This sub-skill covers the header; glycan string semantics belong to `../restraints-glycans/SKILL.md`.

## Fast Authoring Rules

- Write one FASTA record per Chai entity: `>protein|name`, `>protein|name=receptor`, `>ligand|name=atp`, `>dna|name=primer`, `>rna|name=guide`, or `>glycan|name=n_linked`.
- Always provide an entity name; Chai rejects headers without a label and inference requires names to be unique.
- Use explicit entity types instead of relying on sequence heuristics; short `A/C/G/T` records are ambiguous across DNA, RNA, and protein.
- Encode modified polymer residues as bracketed multi-character residue names, such as `AAA(SEP)AAA` or `(MSE)G`, not as unbracketed three-letter text.
- Encode ligands as SMILES strings; use bracketed ions such as `[Mg+2]` or `[Zn+2]`, because bare ion text can pass header parsing but fail ligand tokenization.
- Preserve entity order intentionally: automatic chain IDs are assigned from the accepted chain order, while `fasta_names_as_cif_chains=True` uses entity names as parsing/output chain IDs.

## Validate Before Folding

Run the bundled helper before expensive inference:

```bash
python scripts/validate_chai_fasta.py input.fasta
python scripts/validate_chai_fasta.py --tokenize --entity-names-as-subchains input.fasta
```

The first command checks Chai header parsing, required names, duplicate names, type heuristics, and polymer modified-residue syntax. The optional tokenization check catches malformed SMILES and chain-name issues that only appear when Chai builds chains.

## References

- `references/fasta-and-entities.md` — format grammar, entity tables, naming rules, and chain-name implications.
- `references/api-reference.md` — validation and parsing APIs useful for scripts and diagnostics.
- `references/troubleshooting.md` — common parser, sequence, ligand, duplicate-name, and chain-name failures.

---
name: inputs-and-formats
description: "Prepare and validate ColabFold FASTA, CSV, A3M, AlphaFold3
  molecule, and PDB/mmCIF inputs before MSA search or prediction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ColabFold inputs and formats

Use this sub-skill when the task is about making ColabFold input files valid, explaining how `get_queries` will read them, serializing A3M content, or extracting sequence/template-ready content from PDB/mmCIF files.

## Route by task

- **FASTA, CSV, TSV, or directory inputs**: use [data-formats.md](references/data-formats.md) to choose file layout, multimer syntax, sorting, and naming behavior.
- **AlphaFold3 non-protein components**: use [data-formats.md](references/data-formats.md#af3-non-protein-molecule-syntax) for `dna|`, `rna|`, `ccd|`, and `smiles|` entries, including SMILES semicolon escaping.
- **Parser/API behavior**: use [api-reference.md](references/api-reference.md) for `parse_fasta`, `classify_molecules`, `get_queries`, `msa_to_str`, and `pdb_to_string` signatures and return shapes.
- **Input validation**: run [`scripts/validate_colabfold_input.py`](scripts/validate_colabfold_input.py) before recommending expensive search or prediction.
- **Format failures**: use [troubleshooting.md](references/troubleshooting.md) for optional dependency, backend, data/config, CLI/API, and workflow failures owned by input preparation.

## Safe validation commands

```bash
python sub-skills/inputs-and-formats/scripts/validate_colabfold_input.py input.fasta
python sub-skills/inputs-and-formats/scripts/validate_colabfold_input.py input.csv --sort none
python sub-skills/inputs-and-formats/scripts/validate_colabfold_input.py msas/ --sort msa_depth --json
```

The validator only reads local input files, imports lightweight ColabFold parsing helpers when available, and performs no network, database, GPU, prediction, relaxation, or destructive actions.

## Boundaries

- For generating/searching MSAs, route to [`../msa-search/SKILL.md`](../msa-search/SKILL.md).
- For `colabfold_batch` model execution, templates during prediction, and output ranking, route to [`../batch-prediction/SKILL.md`](../batch-prediction/SKILL.md).
- For Amber relaxation, PDB/mmCIF output inspection after prediction, confidence plots, and citations, route to [`../relaxation-and-outputs/SKILL.md`](../relaxation-and-outputs/SKILL.md).

Do not send future agents back to the source repository for input syntax; this sub-skill distills the needed parser and format behavior into bundled references and scripts.

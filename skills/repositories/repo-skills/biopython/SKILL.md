---
name: biopython
description: "Route Biopython computational biology workflows across sequence
  objects, file formats, alignments, structures, web databases, BioSQL, motifs,
  restriction enzymes, and specialized modules."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Biopython repo skill

Use this skill when a task asks for Biopython, `Bio.*`, `BioSQL`, or general computational-biology workflows that Biopython owns: sequences, biological file formats, alignments, BLAST/search output parsing, phylogenetic trees, macromolecular structures, public biological databases, motifs, restriction enzymes, and specialized bioinformatics modules.

## First checks

- Public install: `python -m pip install biopython`; conda users can install from conda-forge.
- Source/developer install: `python -m pip install -e .` from a Biopython checkout when editing the package.
- Required runtime dependency: NumPy. Optional features may need ReportLab, matplotlib, networkx, rdflib, database drivers, or external bioinformatics executables.
- Minimal import check:

```python
import Bio
from Bio.Seq import Seq
from Bio import SeqIO
print(Bio.__version__, Seq("ATGGCC").translate())
```

- Run [scripts/biopython_quick_smoke.py](scripts/biopython_quick_smoke.py) when you need a safe offline package smoke check before deeper work.
- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a checkout. If the commit, package version, or evidence paths differ substantially, refresh the skill.
- Read [references/troubleshooting.md](references/troubleshooting.md) for install/import/build issues, optional dependency failures, online-service constraints, and source-tree warning recovery.
- Read [references/capability-map.md](references/capability-map.md) when a request spans multiple Biopython modules or you need optional dependency ownership.

## Route by task

| User task | Read next | Notes |
|---|---|---|
| Create/manipulate `Seq`, `MutableSeq`, `SeqRecord`, annotations, features, locations, codon tables, reverse complements, translations, GC/protein utilities | [sequence-objects-and-features](sub-skills/sequence-objects-and-features/SKILL.md) | In-memory object semantics; route file parsing/writing onward to file I/O. |
| Parse, read, write, index, or convert FASTA/FASTQ/GenBank/EMBL/SwissProt/UniProt XML/alignment files | [file-io-and-format-conversion](sub-skills/file-io-and-format-conversion/SKILL.md) | Covers `SeqIO`, `AlignIO`, low-level FASTA/FASTQ iterators, BGZF, `index`, `index_db`, and format names. |
| Pairwise/multiple alignments, substitution matrices, BLAST/SearchIO parsing, local or online BLAST result handling, phylogenetic tree I/O/traversal | [alignment-search-and-phylogeny](sub-skills/alignment-search-and-phylogeny/SKILL.md) | For online BLAST policy, also read the web/database sub-skill. |
| PDB/mmCIF/BinaryCIF/PQR/PDBML structure parsing, SMCRA traversal, atom/residue selection, disordered atoms, contacts, geometry, superposition | [structural-bioinformatics](sub-skills/structural-bioinformatics/SKILL.md) | External tools such as DSSP/NACCESS/MSMS are optional and not part of the base install. |
| Entrez, KEGG, UniProt, Swiss-Prot, ExPASy, GenBank, Medline, GEO, public-database parsers, qblast network etiquette, BioSQL | [web-databases-and-biosql](sub-skills/web-databases-and-biosql/SKILL.md) | Default to offline parsing examples; live services require user email/API policy and network handling. |
| Motifs, PWM/PSSM, JASPAR, restriction enzymes, clustering, phenotype arrays, GenePop/popgen, GenomeDiagram/graphics, SeqUtils/ProtParam, long-tail modules | [specialized-analyses-and-graphics](sub-skills/specialized-analyses-and-graphics/SKILL.md) | Optional graphics/database integrations are documented but not required for base use. |

## Boundary rules

- Do not use Biopython as a replacement for HTSlib-backed BAM/CRAM/VCF command wrappers; use dedicated HTS tools when the request needs samtools/bcftools/tabix semantics.
- Do not claim online-service verification unless you actually ran the network call with user-approved email/API key/rate policy.
- Do not require the original Biopython repository checkout for runtime guidance; this skill bundles the operating references and smoke scripts future agents need.
- If a workflow needs an optional package, external executable, database server, or credentials, stop at the sub-skill troubleshooting section and ask for/verify that dependency before running live work.

# Biopython Capability Map

## Purpose

Read this when a request spans several Biopython modules or when you must decide which optional dependency or sub-skill owns a workflow.

## Core route map

| Capability family | Primary APIs | Skill owner | Typical outputs | Optional dependencies |
|---|---|---|---|---|
| In-memory sequence logic | `Bio.Seq.Seq`, `MutableSeq`, module functions such as `translate`, `reverse_complement`, `transcribe` | `sequence-objects-and-features` | strings/sequences, translated proteins, reverse complements | none beyond base install |
| Annotated records and features | `SeqRecord`, `SeqFeature`, `SimpleLocation`, `CompoundLocation`, position classes | `sequence-objects-and-features` | annotated records, feature-derived subsequences, coordinate validation | none |
| Sequence file I/O | `Bio.SeqIO.parse/read/write/index/index_db/convert`, low-level FASTA/FASTQ iterators | `file-io-and-format-conversion` | `SeqRecord` iterators, dictionaries, indexed databases, converted files | none for common formats; some formats need format-specific input validity |
| Alignment file I/O | `Bio.AlignIO`, `Bio.Align.parse/read/write` | `file-io-and-format-conversion` plus `alignment-search-and-phylogeny` | alignments, converted alignment files | external aligners only when launching them, not for parsing files |
| Pairwise and multiple alignment analysis | `Bio.Align.PairwiseAligner`, `Bio.Align.Alignment`, substitution matrices, legacy `Bio.pairwise2` | `alignment-search-and-phylogeny` | scores, alignment objects, substitution matrices | none for core algorithms |
| Search results and BLAST | `Bio.SearchIO`, `Bio.Blast.parse/read/write/qblast` | `alignment-search-and-phylogeny`; network policy in `web-databases-and-biosql` | `QueryResult`, `Hit`, `HSP`, BLAST records, filtered search hits | BLAST+ executable only for local runs; network for qblast |
| Phylogenetics | `Bio.Phylo.parse/read/write/convert`, tree/clade traversal and drawing helpers | `alignment-search-and-phylogeny` | Newick/Nexus/PhyloXML/NeXML/CDAO trees, traversed or modified trees | matplotlib, networkx, pygraphviz/pydot, rdflib for selected drawing/graph/RDF paths |
| Structures | `Bio.PDB.PDBParser`, `MMCIFParser`, `PDBIO`, `MMCIFIO`, `NeighborSearch`, `Superimposer`, vectors | `structural-bioinformatics` | structure hierarchy objects, selected atoms/residues, geometry/contact results, written structure files | DSSP/NACCESS/PSEA/MSMS and network downloads are optional |
| Web/database records | `Bio.Entrez`, `Bio.Medline`, `Bio.GenBank`, `Bio.SwissProt`, `Bio.ExPASy`, `Bio.KEGG`, `Bio.UniProt` | `web-databases-and-biosql` | parsed XML/text records, downloaded handles, biological database records | live network, NCBI email/tool/api key policy |
| BioSQL | `BioSQL.BioSeqDatabase.open_database` and loaders/adaptors | `web-databases-and-biosql` | database connections, loaded sequences, retrieved records | sqlite3 is stdlib; MySQL/PostgreSQL require drivers and servers |
| Motifs and restriction enzymes | `Bio.motifs`, `Bio.Restriction.Analysis`, `RestrictionBatch` | `specialized-analyses-and-graphics` | motif objects, PWM/PSSM scans, cut maps | JASPAR DB access may need network/DB; base motif/restriction workflows do not |
| Numeric/specialized analyses | `Bio.Cluster`, `Bio.phenotype`, `Bio.PopGen`, `Bio.SeqUtils`, `Bio.Graphics`, `Bio.CAPS`, `Bio.SCOP`, long-tail modules | `specialized-analyses-and-graphics` | cluster assignments, phenotype summaries, GenePop records, protein properties, diagrams | ReportLab for graphics; module-specific external data/tools for some paths |

## Cross-route patterns

- Start with `SeqRecord` concepts before writing or reading records; file formats often preserve only a subset of annotations.
- For a task that starts with online retrieval and ends with sequence parsing, read `web-databases-and-biosql` for handles/policy, then `file-io-and-format-conversion` for `SeqIO` parsing and indexing.
- For BLAST workflows, separate three concerns: launching online/local BLAST, parsing results, and interpreting hits. Network policy belongs to `web-databases-and-biosql`; parser/object-model guidance belongs to `alignment-search-and-phylogeny`.
- For structure-to-sequence tasks, parse and traverse with `structural-bioinformatics`, then route extracted sequences to `sequence-objects-and-features` or `file-io-and-format-conversion` if records need to be written.
- Optional dependency errors are expected in broad Biopython installs. Treat them as feature-specific prerequisites, not as proof that the base package is broken.

## Verification shortcuts

- Use `scripts/biopython_quick_smoke.py` for cross-package import and tiny API coverage.
- Use each sub-skill `scripts/*_smoke.py` when the request is focused and you need a more targeted offline check.
- Avoid online, database-server, graphics-rendering, and external-executable checks unless the user approves the dependency, inputs, and expected side effects.

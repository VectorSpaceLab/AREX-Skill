# Biopython Troubleshooting

## Purpose

Read this for cross-cutting Biopython install, import, optional dependency, network, and workflow-selection failures. For module-specific symptoms, continue to the nearest sub-skill troubleshooting file.

## Install and import failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'Bio'` | Biopython is not installed in the active Python environment | Run `python -m pip install biopython`, then run `python -c "import Bio; print(Bio.__version__)"`. Verify that `python` is the interpreter used by the final task. |
| `ModuleNotFoundError: No module named 'Bio.Alphabet'` or old tutorial code fails | The old alphabet API was removed/deprecated | Remove alphabet arguments and use molecule annotations or format-specific metadata where needed. Route sequence-object code to `sequence-objects-and-features`. |
| Warning about importing Biopython from inside the source tree | The current working directory or Python path points at a Biopython checkout rather than an installed package | Run scripts from outside the checkout, install the package, or ensure editable build extensions are compiled. This warning is expected only during package development. |
| C extension import errors such as missing `_aligncore`, `_pairwisealigner`, `kdtrees`, or `_cluster` | Source install did not build compiled extensions, compiler/build headers missing, or stale editable install | Reinstall with a supported Python and compiler: `python -m pip install --force-reinstall --no-cache-dir biopython` for wheels, or rebuild the editable checkout. Then run the root smoke script. |
| `pip check` reports NumPy conflicts | Environment has incompatible packages or mixed package managers | Prefer a clean environment; install Biopython and NumPy together through one manager. Avoid mixing system Python, conda base, and virtualenv packages. |

## Optional dependency failures

| Symptom | Owning workflow | Recovery |
|---|---|---|
| `ImportError: No module named reportlab` or graphics output fails | GenomeDiagram/graphics | Install ReportLab only if the task needs graphics output. Otherwise route non-graphics analyses to specialized modules that work in the base install. |
| matplotlib, networkx, pygraphviz/pydot, or rdflib import errors | `Bio.Phylo` drawing/graph/RDF paths | Use tree parsing/traversal without those extras, or install the specific optional package required by the requested output format. |
| Missing MySQL/PostgreSQL driver or database connection errors | BioSQL | Use sqlite for local smoke tests when possible. For MySQL/PostgreSQL, install the matching driver and verify the database server, credentials, schema, and network access. |
| External executable not found: BLAST+, ClustalW, MUSCLE, EMBOSS, PAML, DSSP, NACCESS, PSEA, MSMS | Alignment, phylogeny, or structure workflows that launch third-party tools | Do not install broad tools blindly. Confirm the requested workflow, install the one executable it needs, and run its `--help` or version command before launching real data. |

## Online service and credentials failures

- Entrez/NCBI tasks should set `Entrez.email` and, when appropriate, `Entrez.tool` and `Entrez.api_key` before live calls.
- Treat HTTP 429, 5xx, timeout, XML truncation, and service-specific error records as retriable or policy failures, not parser bugs until reproduced offline.
- Save live responses to files or strings before deep parsing when a long workflow depends on a remote service.
- Prefer offline parser smoke checks when the user did not authorize network access.
- For qblast/online BLAST, coordinate with `alignment-search-and-phylogeny` for result parsing and with `web-databases-and-biosql` for network etiquette.

## Parser and file-format failures

- `SeqIO.read` and `AlignIO.read` expect exactly one record/alignment. Use `parse` for multi-record inputs.
- Unsupported format errors usually mean the format name is wrong for the API or the format is readable but not writable/indexable. Read the file I/O format reference.
- FASTQ workflows require qualities. Converting FASTA to FASTQ without supplying quality scores is invalid.
- Rich GenBank/EMBL annotations may not survive round trips through simple formats such as FASTA.
- BGZF is random-access friendly; ordinary gzip is usually not suitable for `index`/`index_db` random access.

## When to stop and ask

Stop before running live work when the task requires:

- Online services without a user-approved email/API key/rate policy.
- Database server credentials or schema changes.
- External executables not already installed.
- Large downloads, full test suites, benchmarks, or long training/alignment jobs.
- Mutating a user-owned environment to repair compiled extensions or optional dependencies.

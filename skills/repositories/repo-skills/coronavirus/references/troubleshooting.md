# Cross-cutting troubleshooting

| Failure | Diagnose and respond |
|---|---|
| Skill helper cannot import a dependency | Run the bundled OpenMM environment probe and inspect the supported environment independently. Keep private executable and installation paths out of notes. Install only the required CPU OpenMM baseline; OpenFF/SystemGenerator/ParmEd are optional for ligand work. |
| A source script is referenced but unavailable | Use the bundled explicit-argument replacement and the nearest sub-skill reference. Never require the original checkout, historical relative paths, or generated source outputs. |
| Input identity is uncertain | Stop before editing or simulating. Record source structure ID, lineage, chain map, and transformation evidence; route coordinate issues to structure-curation and note-quality issues to project-context. |
| PDB parses but data is not simulation-ready | Validate atom/position counts, residues, duplicate names, termini, hydrogens, caps, waters, ions, and ligand chemistry. Parsing is not a scientific or force-field validation. |
| OpenMM preparation fails | Separate dependency/import failure, force-field template failure, topology/position mismatch, periodic-box/solvent failure, XML mismatch, and numerical instability. Use the system-preparation troubleshooting table and preserve the failing command/parameters. |
| Output files are overwritten or mixed | Use a new artifact directory and treat PDB, System, State, and Integrator XML as one bundle. Helpers refuse existing outputs unless `--overwrite` is explicit. |
| CUDA is listed but unusable | Record the exact platform error. The extraction environment reported `CUDA_ERROR_UNSUPPORTED_PTX_VERSION`; use CPU for required checks and do not convert enumeration into a CUDA capability claim. |
| A short run is presented as a recovered scientific result | Report it as a bounded mechanics smoke test. It does not establish equilibration quality, production sampling, binding, efficacy, or paper-level reproduction. |
| Target/publication note makes an unsupported claim | Mark statements as source evidence, project hypothesis, observation, or unresolved. Cite supplied material and write `not verified` rather than guessing DOI, efficacy, or clinical meaning. |
| External tool is unavailable | State the blocked protonation, capping, extraction, or chemistry step. Do not silently substitute an unverified operation or claim the output is equivalent. |

## General safety rules

Do not download files, invoke a Folding@home client, run long historical iterations, copy large structures/archives/PDFs/trajectories, or expose private environment paths from the runtime skill. Keep command lines, versions, input/output checksums when useful, warnings, and intentional omissions in the review artifact or project note rather than in a generated trajectory directory.

# Biotite Troubleshooting

Use this root guide for cross-cutting install, import, optional dependency, and routing failures. For workflow-specific problems, use the nearest sub-skill troubleshooting reference.

## Import And Install Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: biotite` | Biotite is not installed in the active Python environment | Install with `python -m pip install biotite` or the environment manager used by the project, then run `scripts/check_biotite_environment.py`. |
| Import works in one shell but not another | Different Python environment or notebook kernel | Run `python -c "import sys; print(sys.executable)"` in the failing context and install Biotite there. |
| Source install is very slow or times out | Biotite builds Cython/Rust extension wheels from source | Prefer published wheels for package use; for source development, ensure Python 3.12+, Cython, NumPy build headers, setuptools-rust, a Rust toolchain, and a C compiler are available. |
| `pip check` reports broken dependencies | Incompatible NumPy, SciPy/biotraj, requests, packaging, or optional dependency versions | Create a fresh environment or align packages with Biotite's declared runtime requirements before debugging API behavior. |
| Attribute/API differs from examples | Version mismatch between installed Biotite and the task evidence | Check `biotite.__version__`; if working against a newer checkout or unreleased source, refresh this skill or inspect the current source before relying on old signatures. |

## Routing Failures

| Task shape | Best route |
| --- | --- |
| Constructing sequences, alphabets, annotations, alignments, profiles, or trees | [sequence-analysis](../sub-skills/sequence-analysis/SKILL.md) |
| Working with in-memory atoms, bonds, filters, geometry, contacts, trajectories, or structural alphabets | [structure-analysis](../sub-skills/structure-analysis/SKILL.md) |
| Reading/writing FASTA, FASTQ, GenBank, GFF, PDB, PDBx, BinaryCIF, MOL/SDF, GRO, PDBQT, or trajectory files | [file-io-formats](../sub-skills/file-io-formats/SKILL.md) |
| Querying/fetching biological databases or using BLAST/MSA/DSSP/SRA/Vina/Tantan/ViennaRNA wrappers | [database-application](../sub-skills/database-application/SKILL.md) |
| Using PyMOL, RDKit, OpenMM, Matplotlib, sequence graphics, or structure graphics | [interfaces-visualization](../sub-skills/interfaces-visualization/SKILL.md) |

If a workflow spans multiple rows, route in pipeline order: fetch/query, parse, analyze, then visualize/export.

## Optional Dependency And Side-effect Policy

- Database clients may contact remote services and can fail due to network, service availability, throttling, invalid IDs, or credentials/API-key policy. Do not run them unless the user allows network access.
- Application wrappers require external executables. Use `sub-skills/database-application/scripts/check_optional_applications.py` before running BLAST, DSSP, MSA tools, SRA tools, Vina, Tantan, or ViennaRNA.
- Interface/visualization workflows require optional packages such as RDKit, OpenMM, PyMOL, Matplotlib, IPython, ffmpeg, or ImageMagick. Use `sub-skills/interfaces-visualization/scripts/check_optional_interfaces.py` before assuming availability.
- GUI rendering, molecular simulations, large downloads, and external analyses should be explicit user-approved actions, not implicit diagnostics.

## Data And API Misuse Patterns

- Biotite structure annotations and coordinates are NumPy arrays; set `AtomArray.coord` to a float ndarray with shape `(n, 3)`, not a nested Python list.
- PDBx has `CIFFile` and `BinaryCIFFile`; do not look for a public `PDBxFile` class.
- Sequence constructors validate alphabets. Normalize case, convert RNA `U` to `T` for `NucleotideSequence`, and choose ambiguous nucleotide handling deliberately.
- Trajectory files often store coordinates without atom annotations. Load or construct a matching topology/template before converting a trajectory into an `AtomArrayStack`.
- RDKit/OpenMM/PyMOL conversions frequently require finite coordinates, bonds, and standard annotations. Prepare the structure first in `structure-analysis`.

## When To Refresh This Skill

Read [repo-provenance.md](repo-provenance.md) before using this skill for a local checkout. Refresh if the current commit, dirty state, package metadata, public module layout, optional dependency matrix, or major docs/tests differ from the recorded snapshot.

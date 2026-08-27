# PaddleHelix Capability Map

Use this map to choose the nearest sub-skill and bundled helper before opening detailed references.

| User intent or signal | Primary owner | Read/run first | Evidence distilled | Verification candidate |
| --- | --- | --- | --- | --- |
| `pahelix` import, package metadata, optional dependency diagnosis | Root + `core-api-data` | `scripts/check_paddlehelix_environment.py`; `sub-skills/core-api-data/scripts/check_core_api.py` | `setup.py`, `pahelix/tests/import_test.py`, environment handoff | Help/import checks; optional modules skipped with diagnostics |
| `InMemoryDataset`, NPZ cache, data slicing | `core-api-data` | `sub-skills/core-api-data/references/data-formats.md` | `pahelix/datasets/inmemory_dataset.py`, `pahelix/utils/data_utils.py`, utility tests | Tiny cache fixture through bundled checker |
| Random/index/scaffold molecular splits | `core-api-data` | `sub-skills/core-api-data/references/api-reference.md` | `pahelix/utils/splitters.py`, splitter tests | Dependency-light splitter checks; RDKit scaffold case skipped or diagnosed |
| Protein token IDs without training | `core-api-data` or `protein-sequence-function` | `sub-skills/protein-sequence-function/scripts/validate_protein_inputs.py` | `pahelix/utils/protein_tools.py`, protein tutorial | Mixed FASTA/plain synthetic case |
| Compound property prediction or compound pretraining | `compound-drug-discovery` | `sub-skills/compound-drug-discovery/references/workflows.md` | Compound tutorials, GEM/GEM-2/PretrainGNN READMEs/configs | Heavy native commands skipped; preflight assertions via validator |
| DTI data/layout/command planning | `compound-drug-discovery` | `sub-skills/compound-drug-discovery/scripts/validate_compound_inputs.py` | GraphDTA, MolTrans, SIGN, SMAN, GIANT, BatchDTA app evidence | Synthetic malformed DTI layout case |
| Molecular generation | `compound-drug-discovery` | `sub-skills/compound-drug-discovery/references/workflows.md` | JT-VAE, SD-VAE, Seq-VAE app evidence | Tiny SMILES/config preflight; model-required runs skipped |
| HelixDock docking | `compound-drug-discovery` | `sub-skills/compound-drug-discovery/references/helixdock.md` | HelixDock README/config/reproduce scripts | Native reproduce scripts reference-only due downloads/GPU/OpenBabel |
| TAPE protein train/eval/predict | `protein-sequence-function` | `sub-skills/protein-sequence-function/references/workflows.md` | `apps/pretrained_protein/tape/`, protein tutorial | Config/path/sequence preflight; training skipped |
| Protein function prediction | `protein-sequence-function` | `sub-skills/protein-sequence-function/scripts/validate_protein_inputs.py --workflow function-test` | DeepFRI, ProteinSIGN, PTHL evidence | Missing model/label synthetic failure |
| HelixFold3 or HelixFold-S1 JSON | `structure-prediction` | `sub-skills/structure-prediction/scripts/validate_helixfold3_input.py` | HelixFold3/S1 README, demo JSON, run scripts | Demo JSON and synthetic multimodal JSON validation |
| HelixFold family command planning | `structure-prediction` | `sub-skills/structure-prediction/references/helixfold-family.md` | HelixFold, HelixFold-Single, HelixFold3, HelixFold-S1 docs/scripts | Command anatomy only; downloads/GPU runs skipped |
| LinearFold/LinearPartition usage | `linear-rna` | `sub-skills/linear-rna/scripts/check_linear_rna.py` | LinearRNA README/tutorial/bindings/build notes | Constraint validation; API toy calls only if extension imports |

## Integration Notes

- Primary workflow routes are intentionally broad because PaddleHelix is a multi-application bio-computing repository.
- `competition/` and `research/` are long-tail evidence; they are not primary runtime routes unless a user explicitly asks for those experiments.
- Shell launchers, downloaders, notebooks, and training scripts were distilled into bundled references or validators rather than copied as executable runtime dependencies because they are data-, model-, network-, hardware-, or checkout-dependent.

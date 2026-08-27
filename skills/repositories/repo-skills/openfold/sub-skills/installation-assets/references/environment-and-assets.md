# Environment and Runtime Assets

This reference distills OpenFold installation and asset planning for future agents. It is self-contained: do not rely on original source checkout scripts or docs at runtime unless the user deliberately chooses equivalent commands in their own environment.

## Supported Baseline

- OpenFold package metadata is `openfold` version `2.2.0`.
- The documented production target is Linux, Python 3.10, PyTorch 2, and CUDA 12-class GPU workflows.
- The package is POSIX/Linux-oriented; macOS is not a supported production target for CUDA/cuEquivariance workflows.
- Full inference and training need both Python package dependencies and external assets: parameters, sequence/template databases, bioinformatics binaries, and GPU/runtime libraries.
- Basic imports such as `openfold`, `openfold.config`, parsers, and protein utilities can pass while model or CLI imports still fail if the compiled/stub `attn_core_inplace_cuda` extension is unavailable.

## Installation Workflow

1. Create an isolated Python 3.10 environment. Conda or mamba is preferred because OpenFold mixes CUDA, PyTorch, OpenMM/PDBFixer, bioinformatics binaries, and Python packages.
2. Install dependency families before installing OpenFold itself:
   - Core Python/science: `setuptools`, `pip`, `numpy`, `pandas`, `scipy`, `PyYAML`, `requests`, `tqdm`, `typing-extensions`, `ml-collections`, `dm-tree`, `biopython`, `modelcif`.
   - Package build/runtime: `torch`, `torch.utils.cpp_extension`, a compatible C/C++ compiler, and when building CUDA kernels, CUDA toolkit plus `nvcc`.
   - Relaxation: `openmm` and `pdbfixer`.
   - Training/logging: `pytorch-lightning`, `wandb`, `deepspeed`, and `dllogger` when those workflows are used.
   - Download/runtime tools: `aria2`, `awscli`, `git`, and optionally Git LFS for alternate checkpoint sources.
   - Alignment/template binaries: HMMER (`jackhmmer`, `hmmsearch`, `hmmbuild`), HHSuite (`hhblits`, `hhsearch`), and Kalign/Kalign2.
   - Optional acceleration: `flash-attn`, TensorRT Python bindings, CUDA Python runtime module, Polygraphy, and cuEquivariance Torch packages.
3. Install OpenFold only after `torch` imports in the target environment. For a local/editable install, prefer `pip install -e . --no-build-isolation` because setup imports `torch` directly.
4. If compiling CUDA kernels, confirm `nvcc`, CUDA toolkit libraries, and PyTorch CUDA version are compatible. If CUDA toolkit is not available, setup can build a CPU C++ stub under the same `attn_core_inplace_cuda` module name; this is useful for inspection but not a full GPU production validation.
5. Put the active environment's `lib` directory before system libraries in `LIBRARY_PATH` and `LD_LIBRARY_PATH` when extension or OpenMM/Torch shared-library resolution is ambiguous.
6. Validate with `python scripts/check_openfold_environment.py --json` before attempting inference or training. Add `--check-cli --run-pretrained /path/to/run_pretrained_openfold.py` only when the user intentionally wants local script help checks.

## Package Build Behavior

OpenFold's setup process imports `torch`, loads `torch.utils.cpp_extension`, and builds an extension named `attn_core_inplace_cuda`:

- CUDA path: builds a CUDA extension from OpenFold softmax CUDA/C++ sources.
- CPU fallback path: builds a C++ stub when CUDA is not detected.
- Compute capability flags depend on detected CUDA major version and, when available, NVIDIA device capability.
- The `cuequivariance` extra is CUDA/Linux-oriented and excluded on Darwin/macOS.

Practical implication: a build failure with `ModuleNotFoundError: No module named 'torch'` usually means the isolated build environment cannot see the target environment's PyTorch. Install PyTorch first and reinstall OpenFold without build isolation.

## Dependency Families by Workflow

| Workflow | Required dependency families | Optional or conditional dependencies |
| --- | --- | --- |
| Import/config inspection | Python 3.10, PyTorch, NumPy/SciPy stack, OpenFold package, `attn_core_inplace_cuda` stub or extension for model imports | External databases and GPU are not needed for import-only checks |
| Monomer inference with new alignments | Core imports, PyTorch/CUDA, parameter files, PDB mmCIF templates, UniRef90, MGnify, BFD or Small BFD, UniClust30, PDB70, HMMER, HHSuite, Kalign | OpenMM/PDBFixer for relaxation; DeepSpeed, FlashAttention, TensorRT, cuEquivariance for acceleration |
| Monomer inference with precomputed alignments | Core imports, PyTorch/CUDA, parameter files, template mmCIF directory, valid per-query alignment directories | OpenMM/PDBFixer only if relaxation is enabled; full sequence databases may be unnecessary |
| Multimer inference | Monomer-style core plus AlphaFold-Multimer v2.3 parameters, PDB SeqRes, UniProt, UniRef30, MGnify, BFD, UniRef90, PDB mmCIF, HMMSearch/HMMBuild | OpenFold monomer checkpoints are not a substitute for multimer weights |
| SoloSeq inference | Core imports, PyTorch/CUDA, SoloSeq checkpoint, ESM embeddings or ESM generation runtime | UniRef90, PDB70, PDB mmCIF, HHSearch, JackHMMER, and Kalign only when template evidence is generated |
| Training/fine-tuning | Core imports, PyTorch/CUDA GPUs, Lightning, DeepSpeed/dllogger as selected, training mmCIFs, alignment data or alignment DBs, caches | MPI via `mpi4py`, site scheduler wrappers, OpenMM/PDBFixer depending on preprocessing/validation |
| TensorRT acceleration | PyTorch/CUDA, TensorRT Python bindings, `cuda.cudart`, Polygraphy, writable engine directory | Engine profiles must match expected sequence lengths and options |
| cuEquivariance acceleration | Linux CUDA runtime, compatible `cuequivariance_torch`/ops packages, compatible Triton | Not available on macOS; route API/kernel details to `../model-apis/` |

## Runtime Asset Matrix

| Asset | Used by | Expected paths or shapes | Planning notes |
| --- | --- | --- | --- |
| AlphaFold monomer parameters | Monomer inference with DeepMind weights | `params_model_*.npz`, `params_model_*_ptm.npz` | Match `--config_preset` or pass `--jax_param_path`. DeepMind parameters are CC BY 4.0. |
| OpenFold monomer checkpoints | Monomer inference with OpenFold-trained weights | `initial_training.pt`, `finetuning_*.pt`, `finetuning_ptm_*.pt`, no-template variants | Pass `--openfold_checkpoint_path`; choose checkpoint family to match template/pTM intent. |
| AlphaFold-Multimer parameters | Multimer inference | Multimer v2.3 parameter `.npz` files | Required for `model_*_multimer_v3`; OpenFold monomer checkpoints do not replace them. |
| SoloSeq parameters | Single-sequence inference | `openfold_soloseq_params/seq_model_esm1b_ptm.pt` | Pair with `--config_preset seq_model_esm1b_ptm` and ESM embeddings or generation runtime. |
| PDB mmCIF templates | Monomer, multimer, SoloSeq with templates, training caches | `pdb_mmcif/mmcif_files/` plus obsolete/date metadata where relevant | Required positional template directory for many commands; synchronize with PDB SeqRes for multimer. |
| PDB70 | Monomer/SoloSeq template search | `pdb70/pdb70` database prefix | Used with HHSearch; can be skipped for valid precomputed template outputs. |
| PDB SeqRes | Multimer template search | `pdb_seqres/pdb_seqres.txt` | Keep date-compatible with PDB mmCIF. |
| UniRef90 | Monomer MSA and optional SoloSeq template-assisted embedding generation | `uniref90/uniref90.fasta` | Used by JackHMMER. |
| MGnify | Monomer/multimer MSA | `mgnify/mgy_clusters_*.fa` | Multimer docs use a newer MGnify release than older monomer examples. |
| BFD or Small BFD | Monomer/multimer MSA | Full BFD database prefix or `small_bfd/...fasta` | Full BFD is storage-heavy; Small BFD trades size for quality. |
| UniClust30 | Monomer HHblits workflow | `uniclust30/<release>/<prefix>` | Older monomer plans use UniClust30. |
| UniRef30 | Multimer HHblits workflow | `uniref30/UniRef30_*` | Multimer uses UniRef30 naming. |
| UniProt | Multimer MSA | `uniprot/uniprot.fasta` | Required for AlphaFold-Multimer-style database searches. |
| SoloSeq embeddings | SoloSeq inference | Per-FASTA-label embedding directories | ESM-1b sequence length is limited to 1022 residues; longer sequences are truncated. |
| OpenProteinSet training data | Training/fine-tuning | mmCIFs, alignment directories or alignment DB shards, data caches, duplicate-chain files | Route layout and preprocessing to `../data-preparation/`; route execution to `../training/`. |

## Parameter Choices

- `model_1` and `model_2`: template-enabled monomer, no pTM; AlphaFold parameter names should match the preset.
- `model_1_ptm` and `model_2_ptm`: template-enabled monomer with pTM.
- `model_3`, `model_4`, and `model_5`: no-template monomer, no pTM.
- `model_3_ptm`, `model_4_ptm`, and `model_5_ptm`: no-template monomer with pTM.
- `model_1_multimer_v3` and related multimer presets: multimer mode using AlphaFold-Multimer parameters.
- `seq_model_esm1b_ptm`: SoloSeq mode using the SoloSeq checkpoint and ESM embeddings/generation.

OpenFold checkpoint categories include `initial_training.pt`, chronological `finetuning_*.pt`, no-template `finetuning_no_templ_*.pt`, no-template pTM `finetuning_no_templ_ptm_*.pt`, and pTM `finetuning_ptm_*.pt`.

## Dry-Run Asset Planning

Use the bundled planner before running any network/storage-heavy asset workflow:

```bash
python scripts/plan_asset_downloads.py --workflow monomer
python scripts/plan_asset_downloads.py --workflow multimer --base-data-dir data --params-dir openfold/resources
python scripts/plan_asset_downloads.py --workflow soloseq --json
python scripts/plan_asset_downloads.py --workflow training --small-bfd
```

The planner lists retrieval notes, expected path shapes, prerequisites, and follow-up routing. It intentionally does not run `bash`, `aws`, `aria2`, `git`, `wget`, or any network client, and it does not require original OpenFold download scripts.

## Docker and Runtime Notes

OpenFold's source project provides a CUDA-devel Ubuntu Docker build path with Miniforge, the documented environment, copied package sources, and setup installation. A future Docker runtime still needs:

- NVIDIA driver compatibility between host and container CUDA runtime.
- NVIDIA container runtime or equivalent GPU passthrough.
- External parameters and databases mounted into the container.
- Sufficient shared memory, disk, and temporary storage for alignment and model workloads.
- Explicit library path checks when using conda-provided CUDA/OpenMM/Torch libraries.

Treat Docker as a packaging option, not a way to skip asset planning or GPU compatibility checks.

## Fast Validation Checklist

Before routing to inference or training:

- `openfold`, `openfold.config`, parser modules, protein utilities, model modules, and relaxation modules import as required by the intended workflow.
- `attn_core_inplace_cuda` imports, or the user intentionally accepts CPU-stub/import-only limitations.
- `torch.cuda.is_available()` and `torch.version.cuda` match expectations for GPU work.
- Optional CLI help checks pass for user-supplied scripts when validating a local checkout.
- `jackhmmer`, `hmmsearch`, `hmmbuild`, `hhblits`, `hhsearch`, and `kalign` are available when generating alignments/templates.
- Parameter files match the requested preset and workflow.
- Database paths match monomer, multimer, SoloSeq, or training requirements.
- Optional acceleration flags are enabled only when their imports and runtime libraries validate.

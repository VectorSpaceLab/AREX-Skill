# Installation and Asset Troubleshooting

Use this reference to diagnose OpenFold setup, import, backend, binary, Docker, and asset failures before escalating to workflow-specific sub-skills.

## Quick Triage

1. Run `python scripts/check_openfold_environment.py --json` in the target environment. This checks imports, optional backends, extension availability, CUDA state, and external binaries without running model jobs.
2. Add CLI help probes only when the user provides explicit script paths, for example `--check-cli --run-pretrained /path/to/run_pretrained_openfold.py`.
3. If the problem is command construction for inference, route to `../inference/` after missing dependencies/assets here are resolved.
4. If the problem is alignment directory, mmCIF cache, chain cache, or training data layout, route to `../data-preparation/`.
5. If the problem is training execution, Lightning, distributed launch, or DeepSpeed config selection, route to `../training/`.
6. If the problem is model configs, TensorRT engine profiles, cuEquivariance kernels, or weight import internals, route to `../model-apis/`.

## Build and Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'torch'` during `pip install` | OpenFold setup imports PyTorch at build time, but isolated build environment does not include `torch`. | Install compatible PyTorch first, then reinstall OpenFold from the local source with build isolation disabled, such as `pip install -e . --no-build-isolation`. |
| `CUDA_HOME`, `nvcc`, or CUDA toolkit not found during build | PyTorch may have CUDA runtime support, but the toolkit/compiler needed for extension compilation is not visible. | Install or activate a CUDA toolkit matching the PyTorch CUDA family, expose `nvcc`, or accept CPU-stub/import-only behavior for non-GPU inspection. |
| `ModuleNotFoundError: No module named 'attn_core_inplace_cuda'` | The OpenFold extension was not built, was built for another Python/PyTorch/CUDA ABI, or cannot be found on import path. | Reinstall OpenFold in the active environment after validating PyTorch/CUDA/toolkit compatibility; rebuild rather than reusing artifacts from another environment. |
| `attn_core_inplace_cuda` fails with `undefined symbol` or shared library errors | Extension and runtime libraries are ABI-incompatible or dynamic linker paths point at another environment. | Put the active environment `lib` directory first in `LD_LIBRARY_PATH` and `LIBRARY_PATH`, then rebuild OpenFold inside that environment. |
| Basic `openfold` imports pass but model/CLI imports fail | Parser/config modules do not exercise the compiled extension; model paths import `attn_core_inplace_cuda` through attention/structure modules. | Treat this as partial environment readiness. Fix the extension before claiming full CLI/model validation. |
| `openfold.np.relax` or relaxation imports fail | `openmm` or `pdbfixer` is missing. | Install OpenMM/PDBFixer for relaxation, or skip relaxation in inference plans when scientifically acceptable. |
| DeepSpeed prints CPU accelerator warnings | DeepSpeed is installed but no GPU accelerator is detected. | For import-only checks this can be acceptable; for inference/training, verify GPU visibility, driver/container runtime, CUDA runtime, and `torch.cuda.is_available()`. |

## Optional Dependency Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'tensorrt'` | TensorRT acceleration code path was requested without TensorRT Python bindings. | Disable TensorRT flags or install TensorRT bindings compatible with the environment's CUDA/Python/PyTorch stack. |
| `ModuleNotFoundError: No module named 'cuda.cudart'` | CUDA Python runtime module is unavailable, often affecting TensorRT helpers. | Install the compatible CUDA Python package or run without TensorRT. |
| `ModuleNotFoundError: No module named 'polygraphy'` | TensorRT helper dependency is missing. | Install Polygraphy only for TensorRT engine workflows; otherwise disable TensorRT mode. |
| `ModuleNotFoundError: No module named 'deepspeed'` | DeepSpeed optional dependency is missing. | Install DeepSpeed for DeepSpeed inference/training flags, or disable DeepSpeed options. |
| `deepspeed.ops.deepspeed4science` missing | DeepSpeed is present but the DS4Sci kernels required by OpenFold acceleration are unavailable. | Use a DeepSpeed build that includes the needed ops or disable OpenFold DeepSpeed Evoformer attention. |
| `ModuleNotFoundError: No module named 'dllogger'` | Training/logging dependency is missing. | Install DLLogger for training paths that require it, or avoid those logging paths. |
| `cuequivariance_torch` or `cuequivariance_ops_torch` missing | cuEquivariance optional packages are not installed or unsupported on the platform. | Install CUDA-version-specific cuEquivariance packages on Linux CUDA systems, or disable cuEquivariance flags. |
| `flash_attn` build/import failure | FlashAttention wheel, compiler, PyTorch, Python, or CUDA versions do not match. | Use a wheel built for the exact stack, rebuild with matching compiler, or disable FlashAttention settings. |

## CUDA, Driver, and Library Mismatch

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `torch.cuda.is_available()` is false on a GPU machine | CPU-only PyTorch, missing driver, no GPU visibility, or container runtime mismatch. | Check driver, `nvidia-smi`, container GPU passthrough, `CUDA_VISIBLE_DEVICES`, and the PyTorch CUDA build. |
| Extension builds but crashes on GPU | Extension compiled for an incompatible CUDA/PyTorch ABI or unsupported compute capability. | Rebuild OpenFold in the same environment after checking CUDA toolkit, PyTorch CUDA version, and GPU architecture. |
| OpenMM imports but relaxation fails | OpenMM platform plugin or CUDA libraries are unavailable/incompatible. | Inspect OpenMM available platforms; use CPU relaxation only if runtime is acceptable. |
| TensorRT engine build fails | TensorRT/CUDA/PyTorch/profile mismatch or engine directory is not writable. | Validate TensorRT imports, choose a writable engine directory, and match max sequence length/profile settings to expected inputs. Route deep tuning to `../model-apis/`. |
| cuEquivariance flags fail on macOS | cuEquivariance is CUDA/Linux-oriented. | Disable cuEquivariance on macOS; use supported Linux CUDA runtime for these kernels. |

## External Binary Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `jackhmmer: command not found` | HMMER is not installed or not on `PATH`. | Install HMMER and ensure `jackhmmer`, `hmmsearch`, and `hmmbuild` are discoverable; pass explicit binary path flags when needed. |
| `hhblits` or `hhsearch` missing | HHSuite is not installed or not on `PATH`. | Install HHSuite; monomer templates use HHSearch/PDB70 and some MSA workflows use HHblits. |
| `kalign` missing | Kalign/Kalign2 binary is absent or named differently. | Install Kalign and pass `--kalign_binary_path` when it is outside `PATH`. |
| Binary exists but fails with shared library errors | Binary came from another environment or cannot find active environment libraries. | Reinstall the binary family in the active environment or adjust runtime library paths. |
| `aria2c` or `aws` missing during asset acquisition | Download helper prerequisites are unavailable. | Use the dry-run planner first, then install only the retrieval tool needed for the chosen parameter/database source. |

## Parameter and Database Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Inference cannot find AlphaFold parameters | Default resource directory is empty or selected `--jax_param_path` is wrong. | Plan `monomer` or `multimer` assets, download parameters into a stable resource directory, and pass the exact `.npz` path when not using defaults. |
| OpenFold checkpoint not found | `--openfold_checkpoint_path` points to a missing `.pt` file or incompatible checkpoint layout. | Plan OpenFold parameters and choose a checkpoint matching template/no-template and pTM intent. |
| Multimer weights missing | Multimer preset selected without AlphaFold-Multimer v2.3 parameters. | Plan/download AlphaFold parameters for multimer; OpenFold monomer checkpoints are not substitutes. |
| `pdb_seqres_database_path` missing in multimer workflow | Monomer asset plan was reused for multimer. | Plan `multimer` assets; include PDB SeqRes, UniProt, UniRef30, MGnify, BFD/Small BFD, UniRef90, and PDB mmCIF. |
| PDB SeqRes/template mismatch errors | PDB SeqRes and PDB mmCIF came from incompatible dates. | Redownload or synchronize PDB SeqRes and PDB mmCIF from the same release date. |
| Monomer template search fails against PDB70 | PDB70 path is missing/wrong or HHSearch is unavailable. | Verify the PDB70 database prefix and `hhsearch`; for precomputed alignments, ensure each query has `hhsearch_output.hhr`. |
| Alignment generation fails due missing UniRef/MGnify/BFD/UniClust/UniRef30 assets | Required database paths are absent or point to the wrong file/prefix shape. | Use `plan_asset_downloads.py --workflow monomer` or `--workflow multimer` and compare expected paths with command flags. |
| SoloSeq checkpoint or embeddings missing | SoloSeq preset selected without `seq_model_esm1b_ptm.pt` or ESM embeddings/generation setup. | Plan `soloseq` assets; provide `--openfold_checkpoint_path` and either precomputed embeddings or dependencies/databases for generation. |
| ESM SoloSeq sequence truncation surprises | Input sequence exceeds the ESM-1b 1022-residue limit. | Split the sequence or choose an MSA-based workflow; call out the truncation risk in the inference plan. |
| Training data not found | Inference database paths were confused with OpenProteinSet training layout. | Plan `training` assets, then route mmCIF/alignment DB/cache layout to `../data-preparation/`. |

## Docker Runtime Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Container cannot see GPUs | NVIDIA container runtime or host driver setup is missing. | Verify GPU passthrough with a minimal CUDA/PyTorch command before running OpenFold. |
| Container build succeeds but inference cannot find databases | Parameters/databases were not downloaded or mounted into the runtime container. | Use the dry-run asset planner; mount chosen data/resource directories explicitly. |
| OpenMM/Torch library errors inside container | Conda/CUDA libraries are not first on runtime linker path. | Ensure the active environment library path is exported in the container runtime environment. |
| Out-of-space or shared-memory errors | Database downloads, alignment generation, or model jobs exceed container storage/shm defaults. | Plan disk and shared memory before download/model runs; avoid hidden downloads in validation steps. |

## CPU-Only Limitations

CPU-only or extension-stub environments can be useful for metadata, parser, config, and limited import inspection. They are not adequate evidence for production inference/training readiness. Before claiming production readiness, validate GPU visibility, CUDA/PyTorch compatibility, extension import, required optional acceleration imports if enabled, and actual parameter/database availability.

## Download Workflow Safety

OpenFold parameter and data acquisition is network- and storage-heavy. Always produce a plan with `scripts/plan_asset_downloads.py` first, then ask the user before running equivalent download commands in their environment. Never run downloads as a hidden validation step.

## Common Route Decisions

- `run_pretrained_openfold.py --help` fails with `attn_core_inplace_cuda`: fix/rebuild the extension here, then route command planning to `../inference/`.
- User asks which databases are needed for monomer versus multimer: use `scripts/plan_asset_downloads.py`; route to `../inference/` only after assets are selected.
- User has precomputed alignments but no BFD/MGnify/UniRef databases: route to `../data-preparation/` to validate alignment layout; full database downloads may be unnecessary.
- User wants full training data from OpenProteinSet: plan install/runtime prerequisites here, then route data layout to `../data-preparation/` and execution to `../training/`.

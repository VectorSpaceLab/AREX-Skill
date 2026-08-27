# BindCraft installation and runtime prerequisites

Read this before choosing an environment or launching a campaign. The source
installer is evidence for dependency order, but it mutates Conda, downloads
external code and weights, and should not be treated as a safe one-click
helper.

## Required runtime

- Linux x86_64 and Python 3.10 are the repository's documented baseline.
- An NVIDIA GPU with a compatible driver and a CUDA-enabled JAX/JAXLIB build is
  required by the main pipeline. The program calls `jax.devices()` at startup
  and exits if no GPU device is present.
- Install the scientific stack used by the repository: NumPy below 2, pandas,
  Matplotlib, Biopython, SciPy, PDBFixer, seaborn, tqdm, Jupyter/FFmpeg and the
  JAX/Flax/Haiku/Optax support packages. Match versions to the selected CUDA
  runtime rather than copying an arbitrary wheel.
- Install ColabDesign and ProteinMPNN support through the documented BindCraft
  environment. Install PyRosetta from an authorized Rosetta distribution; its
  license terms differ for commercial use.
- Download and unpack the AlphaFold2 parameters separately. The repository
  documentation estimates roughly 5.3 GB. Set `af_params_dir` to the unpacked
  directory and verify the files before a run.
- Provide the DSSP executable used by Biopython secondary-structure analysis
  and the DAlphaBall executable used by PyRosetta buried-unsatisfied-hydrogen
  bond/SASA analysis. Check execute permissions and ABI compatibility.

## Safe preparation order

1. Choose an isolated environment and the Python/CUDA/JAX combination before
   installing optional packages. Do not modify a shared/base environment.
2. Install the backend foundation first, then scientific dependencies,
   ColabDesign, and PyRosetta. Run `pip check` and import probes after each
   major phase.
3. Acquire AF2 parameters and place them in a storage location with enough free
   space. Do not put the archive or cache into the generated skill.
4. Make copies of the repository's JSON presets and replace every target,
   weight, DSSP, DAlphaBall, and output path with paths valid on the launch host.
5. Run the root environment helper with explicit asset paths:

   ```bash
   python skills/disco/bindcraft/scripts/check_bindcraft_env.py \
     --check-assets --af-params-dir ./params \
     --dssp-path ./functions/dssp \
     --dalphaball-path ./functions/DAlphaBall.gcc
   ```

   This command diagnoses; it does not repair permissions or download files.

## CUDA and resource checks

The README recommends at least 32 GB GPU memory for larger target+binder
complexes. A 40 GB card is not a guarantee: target size, binder length,
recycles, model count, and MPNN batch size all affect memory. Trim targets to the
smallest structurally justified region and reduce one resource dimension at a
time when debugging out-of-memory errors. Keep an eye on the fact that host
GPU utilization may be shared; request an isolated device through the scheduler.

## Colab and SLURM

Colab is a convenience path with network, notebook, and large-weight side
effects. Use the same target/settings contracts, but do not assume notebook
paths or package state transfer to a local host. For SLURM, adapt the resource
request in `design-pipeline/references/launching.md`; never copy a hard-coded
Conda activation path from another cluster.

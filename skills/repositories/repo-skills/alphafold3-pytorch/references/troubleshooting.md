# Cross-cutting troubleshooting

## Import and install

- **`ModuleNotFoundError` during `import alphafold3_pytorch`:** install the
  public `alphafold3-pytorch` distribution in the active environment and run
  `python -m pip check`. The package imports a broad scientific stack; do not
  diagnose a missing optional component as a model bug.
- **Torch/CUDA mismatch or `torch.cuda.is_available() == False`:** run the
  bundled environment probe, inspect the installed PyTorch build tag and driver,
  and use CPU only for workflows whose claims have a full CPU substitute. Do
  not claim CUDA verification from a CPU import.
- **RDKit/Gemmi/CCD data error:** distinguish a missing Python dependency from
  missing structure data. PDB/atomized-residue workflows need the data layout
  described by `data-pipeline`; import success does not create CCD files.
- **Optional Nim/PLM/NLM/Kalign failure:** route to the owning reference and
  use the documented Python/query-only fallback where available. Do not install
  compiler, model, or alignment assets during a bounded smoke test.

## Input and feature validation

- **Empty-input assertion:** provide at least one supported entity; check
  protein/RNA/DNA alphabets, ligand SMILES, and metal identifiers before
  conversion.
- **Shape or index assertion:** read the input and model feature contracts
  together. Atom-level indices are structure-global and generally must be
  ascending; atom/token/pair masks and padded dimensions must agree.
- **Unexpected loss or coordinate return:** inspect whether coordinate labels
  or `atom_pos` were supplied, whether `return_loss` was forced, and whether
  `num_sample_steps` was set. The model route distinguishes training from
  sampling explicitly.
- **Serialization failure:** `file_to_atom_input` expects a file produced by
  the package's `atom_input_to_file` path and uses weights-only loading. Do not
  load arbitrary pickle state as an input artifact.

## Data/configuration

- **Malformed mmCIF, missing MSA/template, or bad crop weights:** run the
  data-layout validator before constructing `PDBInput` or a dataset. Check file
  extension, optional fallback policy, cutoff date, and weights summing to one.
- **Dataset/sample mismatch:** verify whether the layout is curated PDB,
  arbitrary mmCIF, or distillation data. Cluster-cache flags and residue-index
  assumptions differ; do not reuse filtered-PDB shortcuts for arbitrary data.
- **YAML validation error:** run the training config validator, identify the
  config kind and dotpath, then fix required model/trainer/conductor fields
  before creating `Trainer`. Do not use Trainer construction as a dry run.
- **Checkpoint overwrite or wrong dataset source:** set an explicit disposable
  output/checkpoint namespace and choose one dataset construction path. Keep
  overwrite disabled until prior artifacts are intentionally disposable.

## CLI/app

- **Checkpoint assertion:** both entry points require an existing checkpoint;
  a syntactically valid path does not prove state compatibility. Route state
  keys/constructor errors to `model-inference`.
- **Boolean/repeated Click options:** pass explicit boolean values for
  `--use-cuda` and repeat `--protein`, `--rna`, or `--dna` once per entity.
  Build and inspect a command before executing it.
- **CUDA flag appears ignored:** the CLI only moves the loaded model when the
  flag is true and CUDA is available; otherwise it keeps the loaded device.
  Probe the backend separately.
- **App `--precision` appears ineffective:** in the current app, the device and
  dtype conversion block is commented out. Do not promise quantization or lower
  memory from this option.
- **Unexpected cache deletion:** the app recursively removes an existing cache
  directory on startup and removes per-session directories on unload. Use a
  disposable cache path; it is not a safe shared-storage service.

## Resource and quality limits

Production model defaults, full diffusion, PDB-scale data, and training can
exceed CPU/GPU memory and time budgets. Reduce dimensions, sequence/atom count,
recycling/sample steps, and optional outputs only for contract diagnostics; a
tiny synthetic success does not establish structural accuracy. Stop rather than
silently downloading weights, external data, or launching a service when those
side effects were not explicitly requested.

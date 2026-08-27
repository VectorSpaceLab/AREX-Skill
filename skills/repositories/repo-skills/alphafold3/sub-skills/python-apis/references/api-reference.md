# AlphaFold 3 Python API Reference

This reference covers Python internals that are useful for coding agents. AlphaFold 3 exposes a runnable CLI, but many Python modules are implementation APIs rather than stable public APIs. Prefer installed-package signature inspection before writing long-lived code.

## Verified Package Facts

- Distribution version inspected: `alphafold3==3.0.3`.
- Imports verified for `alphafold3`, `alphafold3.common.folding_input`, `alphafold3.data.pipeline`, `alphafold3.model.model_config`, and `alphafold3.structure`.
- AlphaFold 3 input JSON constants: `JSON_DIALECT = "alphafold3"`, `JSON_VERSION = 4`, `JSON_VERSIONS = (1, 2, 3, 4)`.
- Generated CCD pickle resources may be required after install; `alphafold3.build_data.build_data()` generates them from a `libcifpp` `components.cif` source when package resources are writable.
- `run_alphafold.py --help` can render flags yet still exit nonzero under some `absl.flags`/program-entry conditions; do not treat help exit code alone as package failure.

## Safe Inspection Script

Run the bundled script to inspect an environment without model inference:

```bash
python scripts/inspect_alphafold3_api.py
python scripts/inspect_alphafold3_api.py --check-ccd-load
```

The default mode imports key modules, prints version and selected signatures, and checks whether packaged CCD pickle resources are present. `--check-ccd-load` attempts `chemical_components.Ccd()` and may fail if generated resources are missing.

## Input Parsing and Serialization

Import from `alphafold3.common.folding_input`:

```python
from alphafold3.common import folding_input

fold_input = folding_input.Input.from_json(json_text, json_path=None)
print(fold_input.sanitised_name())
round_tripped_json = fold_input.to_json()
```

Verified signatures:

```text
folding_input.Input.from_json(json_str: str, json_path: pathlib.Path | None = None) -> Self
folding_input.Input.to_json(self) -> str
folding_input.Input.sanitised_name(self) -> str
```

Important behavior:

- `Input.from_json` validates dialect, version, sequence IDs, sequence types, RNG seeds, bonded atom pairs, and `userCCD`/`userCCDPath` mutual exclusion.
- `json_path` is used to resolve relative file references such as `userCCDPath` and external MSA/template paths; pass the original JSON file path when parsing JSON loaded from disk.
- Chain IDs must be uppercase letters and unique after expansion.
- `Input.to_json` emits AlphaFold 3 JSON with the current `JSON_VERSION`; use this for normalized serialization.
- `Input.sanitised_name()` replaces spaces with underscores and keeps only letters, digits, `_`, `-`, and `.` for filenames.

Minimal parse-only validation pattern:

```python
from pathlib import Path
from alphafold3.common import folding_input

json_path = Path("job.json")
fold_input = folding_input.Input.from_json(json_path.read_text(), json_path=json_path)
print(fold_input.name, fold_input.sanitised_name(), len(fold_input.chains))
```

For full JSON field semantics and examples, route to `../input-preparation/`.

## Data Pipeline APIs

Import from `alphafold3.data.pipeline`:

```python
from alphafold3.data import pipeline
```

Verified signatures:

```text
pipeline.DataPipelineConfig(*, jackhmmer_binary_path: str, nhmmer_binary_path: str, hmmalign_binary_path: str, hmmsearch_binary_path: str, hmmbuild_binary_path: str, small_bfd_database_path: str, small_bfd_z_value: int | None = None, mgnify_database_path: str, mgnify_z_value: int | None = None, uniprot_cluster_annot_database_path: str, uniprot_cluster_annot_z_value: int | None = None, uniref90_database_path: str, uniref90_z_value: int | None = None, ntrna_database_path: str, ntrna_z_value: float | None = None, rfam_database_path: str, rfam_z_value: float | None = None, rna_central_database_path: str, rna_central_z_value: float | None = None, seqres_database_path: str, pdb_database_path: str, jackhmmer_n_cpu: int = 8, jackhmmer_max_parallel_shards: int | None = None, nhmmer_n_cpu: int = 8, nhmmer_max_parallel_shards: int | None = None, max_template_date: datetime.date) -> None
pipeline.DataPipeline(data_pipeline_config: alphafold3.data.pipeline.DataPipelineConfig)
pipeline.DataPipeline.process(self, fold_input: alphafold3.common.folding_input.Input) -> alphafold3.common.folding_input.Input
```

`DataPipeline.process()` runs external MSA/template tools and writes no model outputs by itself. It returns a new `Input` with MSAs/templates filled for protein/RNA chains and leaves ligands/DNA unchanged. It requires valid binary paths, database paths, and a `max_template_date`.

Pipeline-only construction sketch:

```python
import datetime
from alphafold3.common import folding_input
from alphafold3.data import pipeline

fold_input = folding_input.Input.from_json(json_text, json_path=json_path)
config = pipeline.DataPipelineConfig(
    jackhmmer_binary_path="jackhmmer",
    nhmmer_binary_path="nhmmer",
    hmmalign_binary_path="hmmalign",
    hmmsearch_binary_path="hmmsearch",
    hmmbuild_binary_path="hmmbuild",
    small_bfd_database_path="/data/small_bfd",
    mgnify_database_path="/data/mgnify",
    uniprot_cluster_annot_database_path="/data/uniprot_cluster_annot",
    uniref90_database_path="/data/uniref90",
    ntrna_database_path="/data/nt_rna",
    rfam_database_path="/data/rfam",
    rna_central_database_path="/data/rnacentral",
    seqres_database_path="/data/pdb_seqres",
    pdb_database_path="/data/pdb_mmcif",
    max_template_date=datetime.date(2021, 9, 30),
)
processed = pipeline.DataPipeline(config).process(fold_input)
```

This sketch is for wiring only; replace database and binary values with real available resources. If an input already contains complete MSA/template fields, AlphaFold 3 skips corresponding searches.

## `process_fold_input` Helper

`process_fold_input` lives in the top-level `run_alphafold.py` script module, not in `alphafold3.*`. It is useful when a project imports the repo's runner code, but it is not a stable library entry point.

Verified signature:

```text
run_alphafold.process_fold_input(fold_input: alphafold3.common.folding_input.Input, data_pipeline_config: alphafold3.data.pipeline.DataPipelineConfig | None, *, model_runner: run_alphafold.ModelRunner | None, output_dir: os.PathLike[str] | str, buckets: collections.abc.Sequence[int] | None = None, ref_max_modified_date: datetime.date | None = None, conformer_max_iterations: int | None = None, resolve_msa_overlaps: bool = True, fix_standalone_glycans: bool = False, force_output_dir: bool = False, compress_large_output_files: bool = False) -> alphafold3.common.folding_input.Input | collections.abc.Sequence[run_alphafold.ResultsForSeed]
```

Safe pipeline-only usage:

```python
from run_alphafold import process_fold_input

processed_input = process_fold_input(
    fold_input=fold_input,
    data_pipeline_config=data_pipeline_config,
    model_runner=None,
    output_dir="out",
    force_output_dir=True,
)
```

Safety notes:

- Passing `model_runner=None` skips inference and returns the processed `Input`.
- Passing `data_pipeline_config=None` skips the data pipeline.
- Passing both `data_pipeline_config=None` and `model_runner=None` is usually only useful for writing normalized input JSON.
- Passing a real `ModelRunner` can load parameters, JIT-compile, allocate accelerator memory, and run expensive inference.
- `output_dir` may be timestamp-adjusted when non-empty unless `force_output_dir=True`.

For command-line equivalents, route to `../running-predictions/`.

## Model Configuration and Runner Hooks

`make_model_config` and `ModelRunner` are defined in `run_alphafold.py`.

Verified signatures:

```text
run_alphafold.make_model_config(*, flash_attention_implementation: Literal['mosaic', 'triton', 'cudnn', 'xla', 'xla_chunked'] = 'triton', num_diffusion_samples: int = 5, num_recycles: int = 10, return_embeddings: bool = False, return_distogram: bool = False) -> alphafold3.model.model.Model.Config
run_alphafold.ModelRunner(config: alphafold3.model.model.Model.Config, device: jaxlib._jax.Device, model_dir: pathlib.Path)
run_alphafold.ModelRunner.run_inference(self, featurised_example: dict[str, numpy.ndarray | jax.Array], rng_key: jax.Array) -> collections.abc.Mapping[str, typing.Any]
run_alphafold.ModelRunner.extract_inference_results(self, batch: dict[str, numpy.ndarray | jax.Array], result: collections.abc.Mapping[str, typing.Any], target_name: str) -> list[alphafold3.model.model.InferenceResult]
run_alphafold.ModelRunner.extract_embeddings(self, result: collections.abc.Mapping[str, typing.Any], num_tokens: int) -> dict[str, numpy.ndarray] | None
```

Model config construction is cheap:

```python
from run_alphafold import make_model_config

config = make_model_config(
    flash_attention_implementation="triton",
    num_diffusion_samples=5,
    num_recycles=10,
    return_embeddings=False,
    return_distogram=False,
)
```

`ModelRunner` construction itself stores config, device, and model directory. Accessing `model_params`, invoking `_model`, or calling `run_inference()` loads weights and starts accelerator work. Use these hooks only in explicit inference workflows with an approved model directory and compatible JAX device.

`extract_embeddings(result, num_tokens)` is post-processing only: it slices `single_embeddings` to `[:num_tokens]` and `pair_embeddings` to `[:num_tokens, :num_tokens]`, casts to `float16`, and returns `None` if no embedding arrays are present.

## Model Config Module

`alphafold3.model.model_config.GlobalConfig` is a dataclass-style internal configuration object.

Verified signature:

```text
model_config.GlobalConfig(*, bfloat16: Literal['all', 'none', 'intermediate'] = 'all', final_init: Literal['zeros', 'linear'] = 'zeros', pair_attention_chunk_size: collections.abc.Sequence[tuple[int | None, int | None]] = ((1536, 128), (None, 32)), pair_transition_shard_spec: collections.abc.Sequence[tuple[int | None, int | None]] = ((2048, None), (None, 1024)), flash_attention_implementation: Literal['mosaic', 'triton', 'cudnn', 'xla', 'xla_chunked'] = 'triton') -> None
```

Prefer `make_model_config()` for runner-compatible configs unless modifying model internals.

## Structure, mmCIF, and CCD Utilities

Useful imports:

```python
from alphafold3.constants import chemical_components
from alphafold3.structure import mmcif
from alphafold3 import structure
```

Common safe utilities:

- `chemical_components.Ccd(ccd_pickle_path=None, user_ccd=None)` loads the packaged CCD pickle and optionally overlays a user CCD string.
- `mmcif.from_string(mmcif_string)` parses one mmCIF block into a `Mmcif` mapping-like object.
- `mmcif.parse_multi_data_cif(cif_string)` parses multiple `data_...` CIF records into a dict.
- `mmcif.int_id_to_str_id(num)` and `mmcif.str_id_to_int_id(str_id)` convert AlphaFold/mmCIF chain IDs.
- `mmcif.get_bond_atom_indices(mmcif_obj, model_id="1")` extracts `_struct_conn` bond atom indices and raises `BondParsingError` on malformed bond references.
- `mmcif.get_or_infer_type_symbol(mmcif_obj, ccd=None)` reads or infers atom element symbols, loading CCD if needed.
- `structure.from_mmcif(...)` parses structures with options for MSE, arginine, unknown DNA, water/other inclusion, bonds, and model selection.
- `structure.from_sequences_and_bonds(...)` constructs a `Structure` from sequences, chain types, sequence formats, chain IDs, bonds, and a `Ccd` object.
- `Structure.to_mmcif()` and `Structure.to_mmcif_dict()` serialize structure objects.

`Structure` objects expose arrays and iterators such as `num_atoms()`, `num_residues(count_unresolved=...)`, `num_chains()`, `iter_atoms()`, `iter_residues()`, `iter_chains()`, `iter_bonds()`, `filter(...)`, `group_by_chain`, `chain_single_letter_sequence(...)`, `chain_res_name_sequence(...)`, `generate_bioassembly(...)`, `rename_chain_ids(...)`, and `to_mmcif()`.

Caveat: several structure operations require compiled C++ extension modules and packaged CCD resources. If a simple import succeeds but parsing fails, check resource and extension troubleshooting before changing code.

## Generated Resource Maintenance

`alphafold3.build_data.build_data()` builds intermediate package resources:

- Searches `LIBCIFPP_DATA_DIR/components.cif` first.
- Otherwise scans installed site-packages for `share/libcifpp/components.cif`.
- Writes `constants/converters/ccd.pickle` and `constants/converters/chemical_component_sets.pickle` under the installed package resources.

Use it only when:

- AlphaFold 3 is installed in an environment where package resources are writable.
- `libcifpp` data is installed or `LIBCIFPP_DATA_DIR` points at a directory containing `components.cif`.
- The user explicitly wants to repair generated package data.

Safe recovery sketch:

```python
from importlib import resources
from alphafold3 import build_data
import alphafold3.constants.converters as converters

root = resources.files(converters)
missing = [name for name in ("ccd.pickle", "chemical_component_sets.pickle") if not root.joinpath(name).is_file()]
if missing:
    build_data.build_data()
```

Do not run this recovery in read-only installations, production environments, or user-managed shared package installs without approval.

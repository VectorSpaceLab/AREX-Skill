# HelixFold3 Operational Reference

HelixFold3 is the PaddleHelix biomolecular structure-prediction workflow for proteins, nucleic acids, ligands, ions, and modified polymer residues. It is the closest route for requests about AlphaFold3-like JSON inputs, multimodal entities, mmCIF outputs, or `bf16`/`fp32` planning.

## Licensing and Use Caveats

- The repository documentation describes the HelixFold3 server free tier as restricted to non-commercial use, with paid access for commercial use.
- The HelixFold3 code and model parameters are documented as available under the HelixFold3 license for non-commercial use by individuals or non-commercial organizations only.
- Before helping a user run HelixFold3, ask them to confirm that their intended use and model-parameter source are permitted by the applicable license. Do not present model checkpoints or server outputs as unrestricted commercial assets.

## Environment Assumptions

The documented reproduction environment is specialized:

- Python 3.10.
- CUDA 12.0, CuDNN 8.4.0, NCCL 2.14.3.
- PaddlePaddle GPU 3.1.0 from a CUDA-compatible Paddle wheel index.
- Python packages including `absl-py`, `dm-tree`, `biopython`, `immutabledict`, `ml-collections`, `pandas`, `scipy`, `jsonschema`, and `posebusters`.
- MSA tools from a separate environment or install prefix: `jackhmmer`, `hhblits`, `hhsearch`, `kalign`, `hmmsearch`, `hmmbuild`, and `nhmmer`.
- `aria2c` is used by download helpers, but downloads are large and must be explicit user-approved actions.

## Input JSON Schema

A HelixFold3 input JSON contains a top-level `entities` list. Each entity is an object with a `type` and `count`; polymer entities also have `sequence`, and ligand/ion entities use `ccd` or `smiles` as appropriate.

Supported entity types in the examples and docs:

| Entity type | Required payload | Notes |
| --- | --- | --- |
| `protein` | `sequence`, `count` | Amino-acid sequence. Counts greater than 1 represent multiple copies of the same entity. |
| `dna` | `sequence`, `count` | DNA sequence, optionally with residue replacement modifications. |
| `rna` | `sequence`, `count` | RNA sequence, optionally with residue replacement modifications. |
| `ligand` | `ccd` or `smiles`, plus `count` | CCD examples include `QF8`, `PRF`, and `MN`; SMILES examples are supported. If both are present, native preprocessing prefers `ccd`, so treat that as ambiguous user input. |
| `ion` | `ccd`, `count` | Treat ions like CCD-based small components. |

`count` must be a positive integer. For rough resource planning, count expanded polymer tokens: `len(sequence) * count` for proteins, DNA, and RNA. Ligands and ions add atoms/tokens that can materially increase memory but cannot be estimated safely from the JSON alone.

### Modification Objects

Polymer entities may include a `modification` list. The documented HelixFold3 modification form is:

```json
{"type": "residue_replace", "ccd": "5CM", "index": 2}
```

Rules to enforce before planning inference:

- `index` is 1-based and must be within the polymer sequence length.
- `ccd` names the Chemical Component Dictionary code for the replacement residue.
- `type` is currently documented as `residue_replace` for HelixFold3. Other values should be treated as unsupported unless the user has newer local documentation.

## Command Anatomy

The source launcher is reference-only because it encodes local Python, environment, data, and checkpoint paths. Distill it into this command shape instead of asking future agents to open or run the original script:

```bash
CUDA_VISIBLE_DEVICES=0 python inference.py \
  --jackhmmer_binary_path <msa-bin>/jackhmmer \
  --hhblits_binary_path <msa-bin>/hhblits \
  --hhsearch_binary_path <msa-bin>/hhsearch \
  --kalign_binary_path <msa-bin>/kalign \
  --hmmsearch_binary_path <msa-bin>/hmmsearch \
  --hmmbuild_binary_path <msa-bin>/hmmbuild \
  --nhmmer_binary_path <msa-bin>/nhmmer \
  --preset reduced_dbs \
  --reduced_bfd_database_path <data>/small_bfd/bfd-first_non_consensus_sequences.fasta \
  --uniprot_database_path <data>/uniprot/uniprot.fasta \
  --pdb_seqres_database_path <data>/pdb_seqres/pdb_seqres.txt \
  --uniref90_database_path <data>/uniref90/uniref90.fasta \
  --mgnify_database_path <data>/mgnify/mgy_clusters_2018_12.fa \
  --template_mmcif_dir <data>/pdb_mmcif/mmcif_files \
  --obsolete_pdbs_path <data>/pdb_mmcif/obsolete.dat \
  --ccd_preprocessed_path <data>/ccd_preprocessed_etkdg.pkl.gz \
  --rfam_database_path <data>/Rfam-14.9_rep_seq.fasta \
  --max_template_date 2021-09-30 \
  --input_json input.json \
  --output_dir output \
  --model_name allatom_demo \
  --init_model <checkpoint>.pdparams \
  --infer_times 1 \
  --diff_batch_size 1 \
  --precision fp32
```

Important flags:

- `--input_json`: biomolecular entity JSON. Validate it first with `scripts/validate_helixfold3_input.py`.
- `--output_dir`: parent output directory. HelixFold3 creates a child folder with the input JSON basename.
- `--model_name`: configuration key from the HelixFold3 model config; documented demo value is `allatom_demo`.
- `--init_model`: checkpoint `.pdparams` path.
- `--infer_times`: number of inference repetitions.
- `--diff_batch_size`: number of diffusion samples per inference repetition when explicitly overridden.
- `--precision`: `fp32` or `bf16`. `bf16` is suitable only on supported GPUs; `bf16` with AMP level `O2` is not supported by the Python entrypoint.
- `--preset`: documented values are `reduced_dbs`, `full_dbs`, and `casp14` in the parser, but the README says full databases are not yet supported for HelixFold3 at the time of the documented update. Prefer `reduced_dbs` unless the user supplies newer evidence.

## Database and Checkpoint Requirements

HelixFold3 requires all of the following before inference can run:

- MSA/search executables: `jackhmmer`, `hhblits`, `hhsearch`, `kalign`, `hmmsearch`, `hmmbuild`, `nhmmer`.
- Reduced BFD path when using `reduced_dbs`.
- UniProt, PDB seqres, UniRef90, MGnify, template mmCIF directory, obsolete PDB map, CCD preprocessed file, and Rfam database.
- Model checkpoint `.pdparams` under the user’s chosen checkpoint directory.
- Compatible PaddlePaddle GPU runtime and visible GPU.

The documented reduced database download is about 190 GB compressed and about 530 GB after extraction. Do not start downloads without explicit approval.

## Output Layout

For an input JSON named `demo_data.json` and parent output directory `output`, HelixFold3 writes under `output/demo_data/`:

```text
output/demo_data/
  demo_data-pred-1-1/
    all_results.json
    predicted_structure.cif
  demo_data-pred-1-2/
  demo_data-rank1/
    all_results.json
    predicted_structure.cif
  demo_data-rank2/
  msas/
```

The exact number of `pred` and `rank` folders depends on `infer_times` and diffusion batch size. `all_results.json` contains prediction metrics such as pLDDT/PAE-style confidence, chain metrics, clash indicators, and ranking confidence. `predicted_structure.cif` is the predicted structure in mmCIF format. `msas/` contains the MSA/template search files.

## Resource Planning

Documented resource guidance:

- A single GPU should have at least about 32 GB of available memory.
- A100-40G with `bf16` supports about 1200 input tokens in the documented setup.
- V100-32G with `fp32` supports about 1000 input tokens in the documented setup.
- Nucleic acids and ligand-heavy inputs can consume more memory per token/atom than ordinary protein-only examples.
- Lowering model `subbatch_size` or reducing recycles can reduce memory use at the cost of runtime or accuracy, but this requires editing/configuring model config values rather than a pure JSON change.

When planning for a V100 or unknown GPU, choose `--precision fp32`, conservative `--infer_times 1`, conservative `--diff_batch_size 1`, and warn if the validator reports token counts near or above 1000. For A100/H100-class hardware, `bf16` may be reasonable after the user confirms support.

## Evidence Labels

This reference distills evidence from `apps/protein_folding/helixfold3/README.md`, `apps/protein_folding/helixfold3/data/demo_*.json`, `apps/protein_folding/helixfold3/run_infer.sh`, `apps/protein_folding/helixfold3/requirements.txt`, and `apps/protein_folding/helixfold3/inference.py`.

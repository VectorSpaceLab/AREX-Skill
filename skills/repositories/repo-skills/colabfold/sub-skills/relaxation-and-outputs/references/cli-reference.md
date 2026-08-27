# Relaxation, plotting, metrics, and citation reference

This reference covers post-prediction operations only. It assumes a ColabFold result directory already exists, or that you have one or more PDB files to relax.

## Standalone Amber relaxation CLI

`colabfold_relax` relaxes existing PDB structures without re-running MSA search or prediction.

```bash
colabfold_relax input.pdb relaxed.pdb
colabfold_relax input_pdb_directory relaxed_pdb_directory
colabfold_relax input_pdb_directory relaxed_pdb_directory \
  --max-iterations 2000 \
  --tolerance 2.39 \
  --stiffness 10.0 \
  --max-outer-iterations 3
```

Arguments:

- `input`: a single `.pdb` file or a directory containing `.pdb` files.
- `results`: a single output `.pdb` path or a directory for relaxed outputs.
- `--max-iterations`: relaxation iteration cap; `0` means unlimited AlphaFold-style relaxation, but bounded values avoid unexpectedly long runs.
- `--tolerance`: convergence tolerance, default `2.39`.
- `--stiffness`: restraint stiffness, default `10.0`.
- `--max-outer-iterations`: outer iteration cap, default `3`.
- `--use-gpu`: request GPU-backed OpenMM relaxation.

Operational guidance:

- Prefer CPU relaxation when OpenMM GPU/CUDA availability is unknown, especially in portable scripts or CI.
- Use `--use-gpu` only after confirming OpenMM sees the intended CUDA platform; GPU relax can be faster but is more sensitive to driver/CUDA/OpenMM build mismatches.
- Relaxing the top-ranked model is usually enough for downstream inspection; relaxing every seed/model can be much slower.
- Standalone relaxation only reads PDB files. It does not read score JSON, PAE JSON, A3M, FASTA, or mmCIF inputs.

## Python relaxation API

The source-backed function is:

```python
from colabfold.relax import relax_me

relaxed_pdb_text = relax_me(
    pdb_filename="model.pdb",
    use_gpu=False,
    max_iterations=2000,
    tolerance=2.39,
    stiffness=10.0,
    max_outer_iterations=3,
)
```

Supported inputs:

- `pdb_filename`: path to a PDB file.
- `pdb_lines`: PDB text already loaded in memory.
- `pdb_obj`: AlphaFold `protein.Protein` object.

Important dependency assumptions:

- `relax_me(...)` imports AlphaFold relaxation code and OpenMM-backed Amber relaxation at call time.
- A base ColabFold installation may expose the CLI but still fail at runtime if AlphaFold/OpenMM/PDBFixer-style optional dependencies are absent.
- Treat import errors from `alphafold.common.protein`, `alphafold.relax.relax`, or OpenMM components as environment issues, not malformed PDB evidence by default.

## Relaxation during `colabfold_batch`

Full prediction workflows are owned by `../batch-prediction/SKILL.md`, but output post-processing often requires recognizing these relaxation-related options:

```bash
colabfold_batch input.fasta results --amber --num-relax 1
colabfold_batch input.fasta results --num-relax 1 --relax-max-iterations 2000
colabfold_batch input.fasta results --num-relax 1 --use-gpu-relax
```

Relevant behavior:

- `--amber` enables OpenMM/Amber relaxation; if `--amber` is set and `--num-relax` is `0`, ColabFold relaxes all model/seed outputs.
- `--num-relax N` relaxes the top `N` ranked predictions after ranking.
- `--use-gpu-relax` asks relaxation, not prediction, to use GPU.
- Relaxed files are emitted after ranking and are named with `relaxed_rank_...`; unrelaxed files remain available as `unrelaxed_rank_...`.

## Plotting and display APIs

Use these APIs when an environment already has the optional plotting/display stack installed. They are reference APIs, not required for basic validation.

### PAE image from result dictionaries

```python
from pathlib import Path
from colabfold.plot import plot_predicted_alignment_error

plot_predicted_alignment_error(
    jobname="job",
    num_models=len(outs),
    outs=outs,
    result_dir=Path("results"),
    show=False,
)
```

Data assumptions:

- `outs` maps model names to dictionaries containing a `"pae"` matrix.
- The function writes `<jobname>_PAE.png` in `result_dir`.
- Matplotlib is imported inside the function; missing matplotlib is a plotting dependency failure.

### MSA coverage plot

```python
from colabfold.plot import plot_msa_v2

plt = plot_msa_v2(feature_dict, sort_lines=True, dpi=100)
plt.savefig("coverage.png", bbox_inches="tight")
plt.close()
```

Data assumptions:

- `feature_dict["msa"]` is an integer-coded MSA array.
- `feature_dict["num_alignments"]` may be scalar-like or an array containing the count.
- `feature_dict["asym_id"]`, when present, is used to draw chain boundaries for complexes.

### 3D PDB display helper

```python
from colabfold.pdb import show_pdb

view = show_pdb(
    use_amber=True,
    jobname="job",
    homooligomer=1,
    model_num=1,
    color="lDDT",
)
```

Data assumptions:

- `use_amber=True` opens `<jobname>_relaxed_model_<N>.pdb`.
- `use_amber=False` opens `<jobname>_unrelaxed_model_<N>.pdb`.
- `color="lDDT"` colors by the PDB B-factor column, which ColabFold populates with pLDDT.
- `color="chain"` assumes chain labels `A` through `H` and a homooligomer count.
- `py3Dmol` is required. This helper is notebook/display oriented and may not render in headless terminals.

## Extra pTM and interface metrics

When prediction is run with extra pTM calculation enabled, score JSON can include additional interface metrics. The source-backed APIs include:

```python
from colabfold.alphafold import extra_ptm

metrics = extra_ptm.get_chain_and_interface_metrics(
    result,
    asym_id,
    use_probs_extra=False,
    use_jnp=True,
)
```

Common keys:

- `pairwise_actifptm`: pairwise active/interface pTM values by chain pair.
- `pairwise_iptm`: pairwise interface TM values by chain pair.
- `per_chain_ptm`: per-chain pTM values.
- `actifptm`: full-complex active/interface pTM summary.

Plotting:

```python
extra_ptm.plot_chain_pairwise_analysis(scores, fig_path="job_ext_metrics.png")
```

Data assumptions:

- The result dictionary must contain `distogram` logits and `predicted_aligned_error` data.
- `asym_id` defines chain boundaries.
- These metrics are meaningful for complexes; for single-chain results they may be absent or disabled.

## Citation writing API

ColabFold can write a BibTeX file with method/database citations:

```python
from pathlib import Path
from colabfold.citations import write_bibtex

write_bibtex(
    model="alphafold2_ptm",
    use_msa=True,
    use_env=True,
    use_templates=False,
    use_amber=True,
    result_dir=Path("results"),
)
```

Citation selection:

- Always includes ColabFold.
- Adds AlphaFold2 for `alphafold2` or `alphafold2_ptm`.
- Adds AlphaFold-Multimer for model names starting with `alphafold2_multimer`.
- Adds DeepFold for `deepfold_v1`.
- Adds MMseqs2 and UniRef/Uniclust-related citations when `use_msa=True`.
- Adds MGnify when `use_env=True`.
- Adds Foldseek/PDB/HH-suite citations when `use_templates=True`.
- Adds OpenMM when `use_amber=True`.

## Safe validation command

Use the bundled inspector before deciding whether missing plots or metrics require re-running prediction:

```bash
python scripts/inspect_colabfold_outputs.py results_dir --json
```

The inspector only reads file names and lightweight JSON/BibTeX contents. It does not import ColabFold, OpenMM, JAX, matplotlib, or py3Dmol.

# Model and Output Reference

## Model Type Selection

`colabfold_batch` normalizes legacy model names, then applies `set_model_type(is_complex, model_type)`:

- `auto` + monomer selects `alphafold2_ptm`.
- `auto` + complex selects `alphafold2_multimer_v3`.
- Legacy names such as `AlphaFold2-ptm` and `AlphaFold2-multimer-v3` map to lowercase underscore names.
- Supported model types are `alphafold2`, `alphafold2_ptm`, `alphafold2_multimer_v1`, `alphafold2_multimer_v2`, `alphafold2_multimer_v3`, and `deepfold_v1`.

Choose explicit model types when reproducibility matters; use `auto` when the input format already conveys monomer versus complex intent.

## Parameter Files

Prediction loads parameter files from `DATA_DIR/params/`:

- `alphafold2`: `params_model_<N>.npz`
- `alphafold2_ptm`: `params_model_<N>_ptm.npz`
- `alphafold2_multimer_v1`: `params_model_<N>_multimer.npz`
- `alphafold2_multimer_v2`: `params_model_<N>_multimer_v2.npz`
- `alphafold2_multimer_v3`: `params_model_<N>_multimer_v3.npz`
- `deepfold_v1`: `deepfold_model_<N>.npz`

The CLI calls `download_alphafold_params(model_type, data_dir)` when `num_models > 0`. This can trigger a large network download. `--msa-only` sets `num_models=0` and avoids this download.

## Programmatic API Facts

Source-backed functions relevant to planning and debugging:

```python
from colabfold.batch import run, set_model_type, generate_af3_input
from colabfold.download import download_alphafold_params
from colabfold.alphafold.models import load_models_and_params, get_model_haiku_params, model_to_config_name

set_model_type(is_complex: bool, model_type: str) -> str
download_alphafold_params(model_type, data_dir=...)
```

`run(...)` is the orchestration API used by the CLI. It accepts query tuples, output directory, MSA/template settings, model controls, ranking/output settings, and backend flags. Prefer the CLI for user-facing workflows unless a caller already owns parsed queries and dependency setup.

## Default MSA Depth Settings

When not overridden:

- `alphafold2_multimer_v1` and `alphafold2_multimer_v2`: `max_seq=252`, `max_extra_seq=1152`.
- `alphafold2_multimer_v3`: `max_seq=508`, `max_extra_seq=2048`.
- Monomer/pTM/DeepFold routes: `max_seq=512`, `max_extra_seq=5120`.
- `--msa-mode single_sequence` clamps depth to the query count/template requirement.

Use `--max-msa max_seq:max_extra_seq`, `--max-seq`, or `--max-extra-seq` to reduce memory or intentionally sample shallower MSAs.

## Ranking Metrics

- Monomer logs typically include `pLDDT` and `pTM` when using pTM-capable models.
- Multimer logs include `pLDDT`, `pTM`, and `ipTM` where available.
- `--rank auto` selects an appropriate ranking metric; explicit values are `plddt`, `ptm`, `iptm`, or `multimer`.
- `--calc-extra-ptm` adds pairwise ipTM, actifpTM, and chain-wise pTM calculations for complex analysis.

## Expected Output Files

Common per-query outputs:

- `<jobname>.a3m`: serialized MSA used for prediction or generated during MSA-only mode.
- `<jobname>_coverage.png`: MSA coverage plot unless `--skip-output plots` is used.
- `<jobname>_unrelaxed_rank_001_<model>_seed_000.pdb`: unrelaxed structure for a ranked model.
- `<jobname>_scores_rank_001_<model>_seed_000.json`: score data, including pLDDT and PAE-like arrays when available.
- `<jobname>_predicted_aligned_error_v1.json`: AlphaFold-DB-style PAE JSON unless `--skip-output pae_json` is used.
- `<jobname>_pae.png` and `<jobname>_plddt.png`: confidence plots unless `--skip-output plots` is used.
- `<jobname>_template_domain_names.json`: written when templates are enabled.
- `<jobname>.done.txt`: completion marker for non-zipped prediction jobs.
- `<jobname>.result.zip`: zipped result bundle when `--zip` is set.

Shared output files:

- `config.json`: run configuration, including model type, MSA mode, recycles, ranking, seeds, template settings, and ColabFold version.
- `cite.bibtex`: citations selected from model/MSA/template/relaxation use.
- `log.txt`: runtime log with query order, model timing, ranking, and errors.

## Test-Backed Output Expectations

Mocked prediction tests verify that:

- Batch monomer jobs write unrelaxed PDB files and `config.json`.
- Zipped jobs include PDB, scores JSON, coverage/PAE/pLDDT plots, A3M, `cite.bibtex`, and `config.json` without directory prefixes.
- Complex multimer jobs log `rank_001 ... pLDDT=... pTM=... ipTM=...` and use multimer ranking.
- `single_sequence` mode can run without MMseqs2 MSA generation but still predicts with AlphaFold parameters.

Use these as expectations for output interpretation, not as a request to run the original tests.

## Interpreting Confidence Quickly

- High pLDDT indicates confident local structure; low pLDDT regions may be disordered or unsupported by MSA/template evidence.
- PAE plots/JSON indicate domain placement uncertainty; high off-diagonal PAE can mean relative domain/chain orientation is uncertain.
- For complexes, `ipTM` and extra pairwise metrics are more relevant to interface confidence than global pLDDT alone.
- The PDB B-factor column stores pLDDT-like confidence values; do not treat it as crystallographic B-factor data.

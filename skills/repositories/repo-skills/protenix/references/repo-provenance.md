# Repo Provenance

## Source Snapshot

- Repository: Protenix
- Remote URL: `https://github.com/bytedance/Protenix`
- Commit: `c3bfc365b3e1341a11935eddfe7bfdc308092147`
- Branch: `main`
- Exact tag: none detected
- Working tree state at generation: dirty because repo-local `skills/` content was untracked/being generated
- Package distribution: `protenix`
- Package version verified during generation: `2.0.0`

## Environment Inspection Summary

A private inspection environment was verified before skill generation. Public skill content records only reproducible package facts, not local environment paths. Verification covered distribution metadata, core imports, CLI help, and representative modules for CLI, configs, input parsing, MSA utilities, and model code.

Verified import families included:

- `protenix`
- `runner.batch_inference`
- `configs.configs_inference`
- `protenix.data.inference.json_parser`
- `protenix.data.msa.msa_utils`
- `protenix.model.protenix`

## Evidence Paths

The generated skill distilled these relative repository paths:

- `README.md`
- `setup.py`
- `requirements.txt`
- `protenix/version.py`
- `runner/batch_inference.py`
- `runner/inference.py`
- `runner/train.py`
- `runner/msa_search.py`
- `runner/template_search.py`
- `runner/rna_msa_search.py`
- `runner/dumper.py`
- `configs/`
- `protenix/config/`
- `protenix/data/inference/`
- `protenix/data/msa/`
- `protenix/data/template/`
- `protenix/data/constraint/`
- `protenix/data/pipeline/`
- `protenix/data/core/`
- `protenix/model/`
- `protenix/model/modules/`
- `protenix/model/tri_attention/`
- `protenix/model/triangular/`
- `protenix/model/layer_norm/`
- `protenix/tfg/`
- `protenix/metrics/`
- `docs/training_inference_instructions.md`
- `docs/infer_json_format.md`
- `docs/msa_template_pipeline.md`
- `docs/colabfold_compatible_msa.md`
- `docs/prepare_training_data.md`
- `docs/supported_models.md`
- `docs/kernels.md`
- `docs/docker_installation.md`
- `docs/model_0.5.0_benchmark.md`
- `docs/model_1.0.0_benchmark.md`
- `examples/`
- `inference_demo.sh`
- `train_demo.sh`
- `finetune_demo.sh`
- `scripts/prepare_training_data.py`
- `scripts/gen_ccd_cache.py`
- `scripts/colabfold_msa.py`
- `scripts/msa/`
- `scripts/database/`
- `tests/test_installation.py`
- `tests/test_json_template_parser.py`
- `tests/test_fetch_remote_cif.py`
- `tests/test_msa_encoding.py`
- `tests/test_dataset_vectorization.py`
- `tests/test_triton_compatibility.py`
- `tests/test_sample_confidence.py`
- `tests/test_attention_lddt_loss.py`
- `tests/test_fused_dropout_add.py`

## Refresh Triggers

Refresh this skill when Protenix changes any of the following:

- CLI command names, aliases, flags, or boolean parsing behavior.
- Supported model names, default parameters, feature support, or checkpoint/cache behavior.
- Input JSON schema, entity fields, ligand/ion handling, covalent bond format, constraints, or conversion APIs.
- MSA/template/RNA MSA commands, database layouts, external tool requirements, or A3M/header rules.
- Training data root layout, preprocessing command arguments, index CSV schema, training launch patterns, or config override syntax.
- Kernel/backend defaults, optional dependency stack, TFG APIs, confidence metrics, or runtime environment switches.
- Package metadata such as Python version requirements, dependencies, entry points, or distribution version.

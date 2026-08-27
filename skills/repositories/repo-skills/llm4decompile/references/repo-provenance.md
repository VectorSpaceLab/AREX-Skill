# Repository Provenance

- **Repository**: LLM4Decompile
- **Canonical skill id**: `llm4decompile`
- **Source commit**: `85b364bf093eb2ee4f3687cfe38a203fca89f23e`
- **Branch**: `main`
- **Exact tag at HEAD**: none found
- **Working tree state**: clean at extraction time
- **Repository type**: source checkout, not an installable Python package
- **Package metadata found**: none (`pyproject.toml`, `setup.py`, and `setup.cfg` are absent)
- **Public remote URL**: omitted-private-or-unknown

## Evidence Paths Used

These relative paths were the main evidence sources for the generated skill:

- `README.md`
- `requirements.txt`
- `requirements-docker.txt`
- `train/README.md`
- `train/finetune.py`
- `train/compile.py`
- `train/colossalai_llm4decompile/README.md`
- `train/colossalai_llm4decompile/prepare_pretrain_dataset.py`
- `train/llama_factory_llm4decompile/README.md`
- `train/llama_factory_llm4decompile/data/dataset_info.json`
- `train/llama_factory_llm4decompile/train/norm2code-example.yaml`
- `train/llama_factory_llm4decompile/train/pseudo2norm-example.yaml`
- `evaluation/README.md`
- `evaluation/run_evaluation_llm4decompile.py`
- `evaluation/run_evaluation_llm4decompile_singleGPU.py`
- `evaluation/run_evaluation_llm4decompile_vllm.py`
- `evaluation/server/text_generation.py`
- `decompile-bench/readme.md`
- `decompile-bench/run_exe_rate.py`
- `decompile-bench/metrics/cal_edit_sim.py`
- `decompile-bench/metrics/cal_execute_rate.py`
- `ghidra/README.md`
- `ghidra/decompile.py`
- `ghidra/demo.py`
- `sk2decompile/README.md`
- `sk2decompile/Preprocess/format.py`
- `sk2decompile/Preprocess/normalize_src_basedonpseudo.py`
- `sk2decompile/evaluation/normalize_pseudo.py`
- `sk2decompile/evaluation/inf_type.py`
- `sk2decompile/evaluation/sk2decompile_inf.py`
- `sk2decompile/evaluation/evaluate_exe.py`
- `sk2decompile/evaluation/evaluate_r2i.py`
- `sk2decompile/evaluation/gpt_judge.py`
- `sk2decompile/evaluation/bringupbench/README.md`
- `sk2decompile/evaluation/bringupbench/scripts/build-func-maps.py`
- `sk2decompile/evaluation/bringupbench/scripts/eval_infer_out.py`
- `sk2decompile/verl/SK2DECOMPILE/README.md`
- `sk2decompile/verl/SK2DECOMPILE/reward_functions/exe_type.py`
- `sk2decompile/verl/SK2DECOMPILE/reward_functions/sim_exe.py`
- `sk2decompile/verl/SK2DECOMPILE/reward_functions/embedding_gte.py`
- `sk2decompile/verl/SK2DECOMPILE/reward_functions/embedding_qwen3.py`

## Staleness Signals to Watch

- A future checkout with a different commit hash should be treated as a stale baseline until the skill is refreshed.
- A future addition of package metadata would change install and import guidance.
- Any change in the README model tables, dataset schemas, or workflow scripts should trigger a refresh of the corresponding sub-skill.

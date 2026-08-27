---
name: baichuan-7b
description: "Operate Baichuan-7B model loading, architecture inspection,
  C-Eval/MMLU evaluation preflights, and DeepSpeed pretraining setup from
  self-contained repo guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Baichuan-7B Repo Skill

Use this skill when a task involves the Baichuan-7B repository, its custom Transformers model code, official Hugging Face loading pattern, C-Eval/MMLU benchmark scripts, or DeepSpeed pretraining demo. The skill is self-contained for operating decisions; do not reopen the original README or source scripts unless the user's active task is explicitly to edit a checkout.

## Route by task

| User intent | Read | Why |
|---|---|---|
| Load Baichuan-7B, inspect `BaiChuanConfig`, debug generation/cache behavior, or run a tiny architecture smoke | [architecture-and-loading](sub-skills/architecture-and-loading/SKILL.md) | Owns model classes, config defaults, `trust_remote_code` loading, and safe local-source checks. |
| Prepare C-Eval or MMLU evaluation, validate benchmark layout, render commands, or interpret output files | [evaluation-workflows](sub-skills/evaluation-workflows/SKILL.md) | Owns Chinese/English benchmark preflights, dataset layout, output artifacts, and benchmark-specific failures. |
| Prepare pretraining data, validate `tokenizer.model`, DeepSpeed JSON/hostfile, render launch commands, or explain checkpoints | [pretraining-and-deepspeed](sub-skills/pretraining-and-deepspeed/SKILL.md) | Owns corpus sharding, tokenizer placement, DeepSpeed setup, and safe training dry-runs. |
| Check class signatures, dependency surfaces, or source-derived architecture facts shared across workflows | [API reference](references/api-reference.md) | Summarizes verified public classes, signatures, model dimensions, and script surfaces. |
| Diagnose install/import/backend/model-weight problems before choosing a sub-skill | [troubleshooting](references/troubleshooting.md) | Covers cross-cutting dependency pins, CUDA/xFormers, model assets, datasets, and training resource boundaries. |
| Decide whether this skill is stale for a checkout | [repo provenance](references/repo-provenance.md) | Records the commit, dirty state, dependency pins, and evidence paths used to create this skill. |

## Operating assumptions

- Baichuan-7B is a decoder-only 7B causal language model for Chinese and English with a 4096-token training context, 64k vocabulary, RMSNorm, SwiGLU MLP, rotary embeddings, and LLaMA-like design choices.
- The repository has no `setup.py` or `pyproject.toml` package metadata in this snapshot. Local source checks therefore use a Baichuan checkout path or a compatible model directory rather than a pip distribution import.
- The official README loading path uses `AutoTokenizer.from_pretrained(..., trust_remote_code=True)` and `AutoModelForCausalLM.from_pretrained(..., device_map="auto", trust_remote_code=True)`.
- Full 7B generation, benchmark scoring, and DeepSpeed training require model weights/tokenizer files, CUDA-capable runtime, and task-specific data. The bundled helpers are safe preflight/smoke tools and do not download weights, fetch datasets, or launch training by default.
- Code is Apache-2.0 licensed. Model weights have a separate Baichuan model license; check the model source before commercial or redistribution decisions.

## Setup checklist for a later runtime

1. Choose the workflow route above before installing optional packages.
2. Install the repo-documented stack when feasible: `deepspeed==0.9.2`, `numpy==1.23.5`, `sentencepiece==0.1.97`, `torch==2.0.0`, `transformers==4.29.1`, and `xformers==0.0.20`. If newer CUDA/Torch wheels are required, treat compatibility as a runtime decision and run the safe checks again.
3. For architecture-only checks, run the tiny smoke from the architecture sub-skill; it needs no official weights or datasets.
4. For real inference or evaluation, ensure the model identifier or local model directory contains compatible weights, config, tokenizer assets, and trusted remote-code files.
5. For benchmark runs, validate C-Eval or MMLU prerequisites with the evaluation preflight helper before loading the model.
6. For pretraining, validate corpus shards, `tokenizer.model`, DeepSpeed config, hostfile, and checkpoint path before rendering or launching any command.

## Safe first checks

Architecture-only smoke against an active Baichuan-style checkout:

```bash
python sub-skills/architecture-and-loading/scripts/local_model_smoke.py --repo-root /path/to/Baichuan-7B
```

Benchmark preflight without executing inference:

```bash
python sub-skills/evaluation-workflows/scripts/check_evaluation_inputs.py ceval --model /path/to/model --shot 5 --split val
```

Training preflight without launching DeepSpeed:

```bash
python sub-skills/pretraining-and-deepspeed/scripts/validate_training_inputs.py \
  --data-dir /path/to/data_dir \
  --tokenizer-path /path/to/tokenizer.model \
  --deepspeed-config /path/to/deepspeed.json \
  --hostfile /path/to/hostfile
```

## Stop conditions

Stop and ask for explicit user resources before:

- downloading official weights, benchmark datasets, or external benchmark checkouts;
- running full C-Eval/MMLU inference;
- launching DeepSpeed or distributed training;
- changing pinned package versions in a user-owned environment;
- accepting unverified CUDA/DeepSpeed behavior as a completed benchmark or training result.

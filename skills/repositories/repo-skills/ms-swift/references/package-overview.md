# ms-swift Package Overview

## What ms-swift Provides

ms-swift is the ModelScope SWIFT framework for end-to-end large-model workflows:

- Pre-training, supervised fine-tuning, LoRA/QLoRA/full tuning, multimodal tuning, embedding/reranker/sequence-classification training, and checkpoint handoff.
- Inference through `transformers`, vLLM, SGLang, or LMDeploy backends; `swift app` UI-style interaction; and OpenAI-compatible deployment through `swift deploy`.
- Dataset preprocessing, standard message formats, media fields, agent/tool fields, model/template registration, and external plugin loading.
- Export workflows such as LoRA merge, cached dataset export, hub push, and AWQ/GPTQ/GPTQ v2/FP8/BNB quantization.
- EvalScope-backed evaluation through Native, OpenCompass, and VLMEvalKit backends.
- Advanced RLHF/GRPO/GKD/PPO/DPO/KTO/RM/CPO/SimPO/ORPO, sampling, rollout, Ray scheduling, and Megatron-SWIFT distributed training.

## Public Package Facts

- Distribution name: `ms-swift`.
- Import root: `swift`.
- Base console script: `swift`.
- Megatron console script: `megatron`.
- Observed source version for this skill baseline: `4.4.0.dev0`.
- Python support is declared as `>=3.8`; current docs recommend modern Python versions for ML dependencies.

## Main CLI Routes

`swift` routes to these command families:

| Route | Purpose | Primary sub-skill |
| --- | --- | --- |
| `pt` | Continued pre-training or generative-template training | `training` |
| `sft` | Supervised fine-tuning and core training | `training` |
| `infer` | Interactive, batch, dataset, and Python-assisted inference | `inference-deployment` |
| `app` | Local application-style inference UI | `inference-deployment` |
| `deploy` | OpenAI-compatible serving | `inference-deployment` |
| `rollout` | Rollout server/runtime for advanced RL workflows | `advanced-rl-distributed` |
| `rlhf` | GRPO/GKD/PPO/DPO/KTO/RM/CPO/SimPO/ORPO and preference optimization | `advanced-rl-distributed` |
| `sample` | Sampling, distillation, PRM/ORM filtering, and RFT data generation | `advanced-rl-distributed` |
| `export` | Merge, quantize, cached dataset export, and hub push | `export-evaluation` |
| `merge-lora` | LoRA merge helper route | `export-evaluation` |
| `eval` | EvalScope-backed evaluation | `export-evaluation` |
| `web-ui` | Browser UI entrypoint | `training` or `inference-deployment` depending on selected tab |

`megatron` routes to Megatron-SWIFT workflows. Use `advanced-rl-distributed` before planning those commands because optional packages and parallelism constraints are usually required.

## Optional Dependency Families

Base `ms-swift` covers many CLI/API surfaces but not every backend:

- Evaluation: install evaluation support before `swift eval` when EvalScope is missing.
- Ray: install Ray only for selected Ray workflows.
- Megatron-SWIFT: install Megatron/Mcore packages only for selected Megatron workflows.
- Serving acceleration: install vLLM, SGLang, or LMDeploy only for selected inference/deployment/eval backends.
- Quantization: install method-specific packages such as AWQ, GPTQ, GPTQ v2, or BNB dependencies only for the chosen export method.
- Hardware accelerators: match CUDA/NPU/ROCm/MPS/vendor packages to the host and selected workflow; do not install broad accelerator stacks just for source inspection.

## Config and Data Conventions

- Most CLI commands accept YAML or JSON config files as the first argument.
- Config files can contain an `ENV` mapping; ms-swift sets those environment variables only when they are not already present.
- Lists are passed as repeated command values, for example `--dataset data1.jsonl data2.jsonl`.
- Dict-like arguments use JSON strings, for example `--model_kwargs '{"fps_max_frames": 12}'`.
- Dataset values support hub IDs, local files, local directories, subsets, and sample suffixes such as `dataset_id:subset#1000`.

## Cross-Skill Handoffs

- Training to inference: LoRA checkpoints become `--adapters`; full checkpoints become `--model`.
- Training to export: merge/export decisions depend on full-vs-LoRA-vs-QLoRA and the intended serving backend.
- Data customization to training/RLHF: schema, columns, media fields, and plugin registration should be validated before long-running commands.
- Inference to evaluation: accelerated backends can be shared, but EvalScope still requires evaluation extras and backend-specific dataset support.
- RLHF to deployment: GRPO rollout servers are advanced-RL concerns, while final user-facing inference servers are inference/deployment concerns.

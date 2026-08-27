---
name: "training-and-evaluation"
description: "Guide DeepAnalyze training, evaluation, and case-study
  contribution workflows with safe dry-run command planning."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# DeepAnalyze Training and Evaluation Router

Use this sub-skill when the user asks to develop, fine-tune, RL-train, benchmark, or contribute case studies for DeepAnalyze.

## Route by request

- **Train or customize DeepAnalyze**: open [`references/training-recipes.md`](references/training-recipes.md). Use [`scripts/render_training_command.py`](scripts/render_training_command.py) to render the official single-ability SFT, multi-ability cold-start SFT, or multi-ability RL command plan. Do not launch heavy training from placeholders.
- **Evaluate on a playground benchmark**: open [`references/benchmark-playgrounds.md`](references/benchmark-playgrounds.md). Use [`scripts/benchmark_command_builder.py`](scripts/benchmark_command_builder.py) to plan DABStep-Research, DS-1000, DSBench, or TableQA commands with explicit inputs, outputs, resume behavior, and model endpoint needs.
- **Add a public case study or contribution**: open [`references/contribution-and-case-studies.md`](references/contribution-and-case-studies.md).
- **A command fails or a prerequisite is missing**: open [`references/troubleshooting.md`](references/troubleshooting.md) before retrying.

## Boundaries

This sub-skill covers only DeepAnalyze's official training and evaluation pathways:

- model and DataScience-Instruct-500K preparation;
- special-token preprocessing when starting from the DeepSeek-R1-0528-Qwen3-8B base;
- DeepAnalyze's ms-swift editable SFT recipes;
- DeepAnalyze's SkyRL/Ray/Hydra RL recipe and `DeepAnalyzeEnv` behavior;
- DABStep-Research, DS-1000, DSBench, and TableQA benchmark playgrounds;
- contribution and case-study layout.

Route elsewhere instead of expanding this sub-skill:

- vLLM launch, model download trade-offs, quantization, and tokenizer-tag implementation details -> `model-serving`;
- programmatic DeepAnalyze API/file usage -> `api-and-clients`;
- CLI, WebUI, or Jupyter frontends -> `interactive-frontends`;
- generic ms-swift or SkyRL internals not used by DeepAnalyze's official commands -> no route in this generated skill; inspect those projects directly only if the user explicitly asks.

## Safety defaults

- Treat all training and benchmark execution as expensive and environment-dependent.
- Never run a command containing `PATH_TO_...`, `path_to_...`, `YOUR_API_KEY`, or other placeholders.
- Prefer command rendering and file checks before launch.
- Keep SFT, RL, serving, and benchmark environments separate unless the user has already proven a combined environment works.
- Ask for concrete model paths, data paths, GPU count, benchmark data location, evaluator endpoint/key, and output directory when they are not provided.

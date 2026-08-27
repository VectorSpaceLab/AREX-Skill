# LMOps cross-cutting troubleshooting

Read this before executing any LMOps paper-code workflow. LMOps contains many independent projects with different dependency stacks, data sources, model sizes, and hardware assumptions.

## Install/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| A source script imports `transformers`, `fairseq`, `deepspeed`, `vllm`, `ray`, `trlx`, `diffusers`, `DPR`, or `verl` and fails immediately. | The selected subproject has its own environment requirements; LMOps is not one root package. | Use the owning sub-skill to identify the exact project environment. Do not install every requirement file globally. |
| A repo helper works on Python 3.7/3.10 in the README but fails on a newer Python. | Older projects pin old Torch/Fairseq/Transformers or CUDA-era dependencies. | Create a project-specific environment matching the project README; avoid reusing the static inspection environment. |
| Editable install from the repository root fails. | There is no root `pyproject.toml` or root package metadata. | Treat each project independently; use bundled planning helpers before installing anything. |
| A generated helper reports only a plan and not execution. | Bundled scripts are intentionally safe and do not start heavy source workflows. | After the plan is reviewed, run source project commands only in a user-provided execution checkout and environment. |

## Credentials and external services

| Surface | Needed for | Guidance |
| --- | --- | --- |
| Hugging Face token/cache | Gated models, datasets, model downloads, Promptist/CoRAG/AdaptLLM/MiniLLM resources. | Verify access in the execution environment; never write tokens into generated plans or logs. |
| OpenAI-compatible API key | ProTeGi provider calls, UPRISE OpenAI inference, LLM-as-a-Coach/GAD scoring or coach workflows. | Keep keys in environment variables or a secret manager. Use bundled planners without keys first. |
| W&B API key/project | OEL, OPCD, LLM-as-a-Coach, GAD and some Learning Law/training logs. | Decide logging policy before launch; do not hard-code keys. |
| Google Drive or external downloads | Promptist data, UPRISE retriever/prompt pool, other paper assets. | Treat downloads as side effects requiring user approval and storage budget. |

## Data and path mistakes

- Many paper workflows expect large staged datasets. A missing file may mean the data-preparation stage was skipped, not that the training script is broken.
- Prefer bundled validators/planners first:
  - `../sub-skills/example-retrieval/scripts/validate_task_metric_plan.py` for UPRISE/SE2 task and metric plans.
  - `../sub-skills/adaptation-and-training/scripts/raw_to_reading_comprehension.py` for tiny corpus-conversion fixtures.
  - `../sub-skills/adaptation-and-training/scripts/pds_pipeline_planner.py` for PDS stage path completeness.
  - `../sub-skills/distillation-and-post-training/scripts/check_tuna_ranking_data.py` for Tuna ranking JSON.
  - `../sub-skills/rl-experiential-learning/scripts/check_experience_inputs.py` for experience lists, prompt files, and data-root shapes.
  - `../sub-skills/rag-and-acceleration/scripts/corag_service_plan.py` for CoRAG service ordering.
- If a command uses placeholders like `<MODEL_OR_ID>`, `<DATA_ROOT>`, `<EXPERIENCE_LIST>`, or `<OUTPUT_DIR>`, stop and replace every placeholder before execution.

## Hardware and runtime scale

| Project family | Common heavy requirement |
| --- | --- |
| SE2 | README-reported full COPA pipeline can take about one hour on 8 V100-32GB GPUs. |
| MiniLLM | Experiments used large multi-GPU DeepSpeed runs; some LLaMA scripts use tensor parallelism. |
| CoRAG | Example inference was tested with 8 A100-40GB GPUs plus E5 and vLLM servers. |
| OEL/OPCD/GAD/LLM-as-a-Coach | Docker/Ray/vLLM/VeRL environments, A100/H100/H200 or B200-specific setup paths, W&B/HF/OpenAI credentials. |
| Promptist RL training | Multi-GPU Accelerate/TRL/Stable Diffusion/CLIP/aesthetic reward setup. |

A visible GPU is not enough. Match Python, Torch/CUDA wheel, driver, optional CUDA extensions, model size, tensor parallel size, GPU memory, and node count before launch.

## Source-checkout staleness

Read `repo-provenance.md` when a user asks whether this skill matches a checkout. Refresh the skill if any of these changed:

- commit or branch differs materially,
- major project directories, READMEs, scripts, or configs changed,
- public command flags or data schemas changed,
- a formerly optional backend becomes required by user scope.

## When to stop

Stop and ask for explicit user approval before:

- installing broad requirement sets or GPU stacks,
- running downloads, Docker, Ray, vLLM, or long training/evaluation,
- using API keys or uploading logs,
- overwriting output/checkpoint directories,
- accepting a CPU-only result as proof of an actually required CUDA/Ray/vLLM workflow.

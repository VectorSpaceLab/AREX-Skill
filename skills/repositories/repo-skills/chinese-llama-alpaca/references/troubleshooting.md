# Cross-Cutting Troubleshooting

Use this reference when the exact workflow is unclear or when several sub-skills might be involved.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Missing `torch`, `transformers`, `peft`, or `sentencepiece` | Base requirements not installed. | Install the pinned public requirements before using any workflow. |
| Missing `datasets`, `pandas`, `fastapi`, `gradio`, `langchain`, or `deepspeed` | Optional workflow dependency not installed. | Install only the optional package set needed for the chosen sub-skill. |
| CUDA not visible in the safe environment probe | CPU-only environment or no GPU passthrough. | Confirm whether CPU-only usage is acceptable. Do not claim GPU verification without a CUDA-backed import/smoke. |
| User asks for original full LLaMA weights | The repo does not redistribute them. | Explain the release boundary and ask for user-provided licensed base weights. |
| User wants inference but only has LoRA adapters | LoRA adapters are not a full model. | Route to model reconstruction first. |
| User wants training before validating data | Training inputs may be malformed. | Validate data with the training helper first. |
| User wants benchmark claims but no dataset/model is present | Benchmark execution is not possible. | Distinguish example tables from actual C-Eval runs and ask for the required assets. |
| Runtime scripts mention the original checkout | The generated skill is incomplete or stale. | Use only bundled runtime files inside the generated skill tree. |
| Output directory, cache, or asset path leaks local environment details | A public instruction was written too concretely. | Rewrite the guidance to use user-provided or generic reproducible paths only. |
| A long-running job starts unexpectedly | The user approval gate was skipped. | Stop and confirm model/data/GPU/time budget before proceeding. |

## Workflow Selection Heuristics

- **Need a merged model or tokenizer issue?** Start with model reconstruction.
- **Need generation, UI, API, or LangChain?** Start with inference/deployment.
- **Need new adapter training or data checks?** Start with training/fine-tuning.
- **Need C-Eval or example score interpretation?** Start with evaluation/benchmarks.

## Safe Recovery Pattern

1. Run `python scripts/check_environment.py` to confirm the base toolchain.
2. Validate the relevant asset or data shape with the sub-skill helper.
3. Confirm the user wants the chosen backend or service exposure.
4. Run the bundled `--help` or validator check first.
5. Escalate to a full run only if the user confirms the model/data/budget.

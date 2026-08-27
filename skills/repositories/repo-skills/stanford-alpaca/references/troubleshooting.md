# Cross-Cutting Troubleshooting

Read this for failures that span more than one Stanford Alpaca workflow. For workflow-specific failures, continue with the nearest sub-skill troubleshooting reference.

## Dependency or import failure

**Symptoms:** `ModuleNotFoundError` for `torch`, `transformers`, `fire`, `rouge_score`, `sentencepiece`, `tokenizers`, or `openai`; import succeeds for one helper but a training or weight-diff helper fails.

**Recovery:**

1. Run the root `scripts/check_stanford_alpaca_env.py` probe first; it does not load a model or call a network service.
2. Install the dependency family needed by the route, rather than adding every optional integration:
   - data validation: standard Python only for the validator;
   - offline instruction helpers: `fire`, `numpy`, `rouge-score` only if using the source-aligned parser/dedup workflow;
   - SFT and weight-diff helpers: `torch`, `transformers`, `sentencepiece`, and a compatible tokenizer build;
   - DeepSpeed only for the explicit offload recipe.
3. This historical code uses `openai.Completion.create`, `openai.error`, and `openai.openai_object`. If a modern client reports that these are absent, use a pre-1.0 OpenAI client such as `openai==0.27.8`, or migrate the live caller deliberately; do not silently assume the API is source-compatible.
4. If an older PyTorch build warns that it was compiled against NumPy 1.x, use `numpy<2` or a matching newer PyTorch build. Re-run the probe after changing either package.

## CUDA appears unavailable

**Symptoms:** PyTorch imports but `torch.cuda.is_available()` is false, `torchrun` falls back to CPU, bf16/FSDP flags fail, or a CUDA device string raises an error.

**Recovery:**

- Distinguish host hardware from the PyTorch build inside the active environment. A CPU PyTorch wheel cannot validate CUDA merely because the host has GPUs.
- Use the data validator, command builders, prompt renderer, and dry-run weight-diff builder on CPU. They are not evidence that full SFT or checkpoint recovery will run on GPU.
- For full SFT, install a driver-compatible CUDA PyTorch build and verify a small device operation before launching. Then follow [fine-tuning troubleshooting](../sub-skills/fine-tuning/references/troubleshooting.md).
- For recovery, ensure the complete raw and diff checkpoints fit in the selected device or in host memory; then follow [weight-diff troubleshooting](../sub-skills/weight-diff-recovery/references/troubleshooting.md).

## A path, dataset, or checkpoint is missing

**Symptoms:** file-not-found errors, a JSON parse failure, invalid `data_path`, no Hugging Face checkpoint files, or raw/diff/tuned paths accidentally point to the same directory.

**Recovery:**

- Validate training data with [dataset-and-prompts](../sub-skills/dataset-and-prompts/SKILL.md) before training.
- Use the fine-tuning command builder to print a command before launching it; it does not verify or download a model.
- Use the weight-diff command builder with `--strict` when all checkpoint directories should already exist. It rejects path-role collisions before any tensor load.
- Do not create output directories inside an input checkpoint directory. Keep raw, diff, and tuned/recovered paths distinct.

## Live instruction generation cannot start or keeps retrying

**Symptoms:** no `OPENAI_API_KEY`, authentication failure, a rate-limit retry loop, connection errors, no accepted records, or expensive multiprocessing behavior.

**Recovery:**

- Start with the offline renderer and parser in [instruction-generation](../sub-skills/instruction-generation/SKILL.md); they require no credentials.
- Supply credentials only through the process environment and ensure the client/API family matches the historical completion call surface.
- Reduce requested instruction count, request batch size, or worker count before spending more API budget. Inspect saved completion text and parser output before retrying a large run.
- A live API call is external, credentialed, and non-deterministic; do not treat a successful dry run or parser check as a live API test.

## License or intended-use ambiguity

**Symptoms:** a plan proposes commercial use, redistribution, hosted deployment, or a derivative model/data release and the permissive code license seems to conflict with data/model wording.

**Recovery:**

- Read [intended use and licenses](../sub-skills/dataset-and-prompts/references/intended-use-and-licenses.md).
- Treat dedicated data and weight-diff license files and explicit non-commercial/research-use notices as higher-priority evidence for those artifacts than a broad statement about code. The bundled reference records a conflict in the model-card text.
- Stop for policy or legal review before proceeding with commercial or redistribution decisions; this skill is not legal advice.

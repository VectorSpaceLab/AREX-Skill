---
name: example-retrieval
description: "Operate LMOps example retrieval, many-shot prompting, and ICL
  analysis workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# example-retrieval

Use this sub-skill when the user asks about in-context example selection, prompt-pool retrieval, many-shot prompting, or ICL analysis in these LMOps workflow families:

- **UPRISE**: universal prompt retrieval, task/metric extension, prompt-pool encoding, HF/OpenAI inference, retriever training, and random/BM25/SBERT ablations.
- **SE2**: sequential example selection with score -> train -> infer stages, scored-data/checkpoint shortcuts, and beam-search retrieval.
- **LLM Retriever**: LLM-feedback reward scoring, reward-model training, KD bi-encoder training, dense/random/BM25 search, and released-checkpoint evaluation.
- **CED-ICL**: cross-entropy-difference in-context demonstration selection with the T-Few-style runner stack.
- **Structured Prompting** and **Understand ICL**: many-shot structured prompting, Fairseq/HF variants, recording runs, and analysis outputs.

Do **not** use this sub-skill for ProTeGi or Promptist prompt rewriting/optimization. Route those to `../prompt-optimization/SKILL.md`. Do **not** use this sub-skill for CoRAG or LLMA retrieval-augmented generation/decoding acceleration. Route those to `../rag-and-acceleration/SKILL.md`.

## Operating route

1. Classify the request:
   - UPRISE or SE2 command generation, prompt-pool setup, task/metric extension, scoring, retriever training, inference, or ablations: use `references/uprise-and-se2-workflows.md`.
   - LLM Retriever data, reward scoring, KD bi-encoder training, search/evaluation, or CED-ICL: use `references/llm-retriever-and-ced.md`.
   - Structured Prompting or Understand ICL recording/analysis: use `references/structured-prompting-and-icl-analysis.md`.
   - Task/metric, prompt-pool, JSON/JSONL, scored-data, or config-shape questions: use `references/configuration-and-data-formats.md`.
   - Credentials, paths, hardware, old dependency stacks, or confusing output directories: use `references/troubleshooting.md` first.
2. Before any expensive source workflow is attempted, run the bundled planner `scripts/build_retrieval_commands.py` to print the intended command templates and stage order. The planner never downloads data, launches training, starts distributed jobs, or imports repository code.
3. For UPRISE/SE2 task additions, create a tiny task/metric plan and run `scripts/validate_task_metric_plan.py` before editing source task maps or metrics. The validator uses built-in distilled facts and does not import repository code.
4. Keep credentials explicit and external. Do not write OpenAI, Hugging Face, or W&B tokens into generated commands, logs, JSON plans, or prompt-pool files.
5. Treat paper-scale GPU work as documented but unverified by this skill. UPRISE/SE2 scorer/trainer runs, LLM Retriever reward/KD training, CED-ICL PEFT runs, and Fairseq/HF many-shot runs can require multiple GPUs, old dependency stacks, model downloads, and substantial time.

## Bundled reference map

- `references/uprise-and-se2-workflows.md`: UPRISE and SE2 stage order, get-command flags, task/metric extension, prompt-pool encoding, HF/OpenAI inference, ablations, shortcuts, and hardware notes.
- `references/llm-retriever-and-ced.md`: LLM Retriever data/download/formatting, reward scoring, KD bi-encoder training, search/evaluation, DeepSpeed config role, iterative training, and CED-ICL T-Few-style flow.
- `references/structured-prompting-and-icl-analysis.md`: Structured Prompting Fairseq/HF variants plus Understand ICL record/analyze stages and outputs.
- `references/configuration-and-data-formats.md`: task/metric maps, cluster strings, prompt-pool/scored JSON shapes, LLM Retriever JSONL files, and plan examples.
- `references/troubleshooting.md`: HF/OpenAI credentials, task/metric mismatch, checkpoint/prompt-pool path issues, GPU requirements, old torch/fairseq/DPR dependencies, and output-directory confusion.

## Bundled scripts

- `scripts/build_retrieval_commands.py`: safe planner for UPRISE, SE2, and LLM Retriever command templates. It prints and optionally checks paths only; it does not run the printed commands.
- `scripts/validate_task_metric_plan.py`: validates tiny JSON task/metric plans, with optional YAML support when PyYAML is available. It catches common task/metric/class-count/cluster mismatches without importing repository code.

## Verification status

Creation-time verification for this sub-skill is static and CPU-only. The bundled scripts are self-contained and safe by default. End-to-end retriever training, LLM inference, OpenAI calls, Hugging Face downloads, T-Few/CED runs, Fairseq/HF many-shot evaluation, and Understand ICL analysis over real models are documented but not claimed as executed by this skill.

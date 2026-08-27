---
name: evaluation-reproduction
description: "Use PixelRAG evaluation scripts and paper reproduction harnesses
  safely, including reader/search serve preflights and graders."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PixelRAG Evaluation and Reproduction

Use this sub-skill when the task asks to reproduce PixelRAG paper results, run `eval/` benchmark cells, debug `reproduce.sh`, configure reader/search serves, compare retrieval modes, or understand grader/output metadata.

## Start Here

1. Decide whether the user wants a **quick pipeline smoke** or a **paper-matching run**.
   - Quick smoke can use a public search API or a tiny self-hosted index.
   - Paper Table 1 reproduction requires specific search indexes, reader model, large tile/index data, and grader credentials.
2. Validate services before running a benchmark. Use [pixelrag_eval_preflight.py](scripts/pixelrag_eval_preflight.py) or reproduce the shell preflight manually.
3. Confirm credentials:
   - OpenAI key/base URL for LLM judge on NQ/NQ-Tables and some VQA grading paths.
   - Optional MiniMax key for MiniMax reader experiments.
4. Record the run metadata stamped by the harness: dataset/split/n, reader, retrieval URL/status, top-k, instruction, and grader.

## Read or Run

- Read [paper-reproduction.md](references/paper-reproduction.md) for `reproduce.sh`, ports, roles, expected resources, and public-API caveats.
- Read [eval-api-reference.md](references/eval-api-reference.md) for `run_bench.py`, retrieval flags, model config, output files, and graders.
- Read [troubleshooting.md](references/troubleshooting.md) for empty retrieval, wrong index, judge failures, query-image path issues, and slow on-demand rendering.
- Run [pixelrag_eval_preflight.py](scripts/pixelrag_eval_preflight.py) before an expensive eval.

## Common Routes

| Request | Action |
| --- | --- |
| "Reproduce Table 1 NQ base" | Check reader `Qwen/Qwen3.5-4B`, base pixel serve vector count, OpenAI judge, then run the `nq/base` cell. |
| "Try a public API smoke" | Use direct `run_bench.py --local-api-url` mode; warn that public base endpoint may not match normed paper index. |
| "Why is score near zero?" | Check preflight, retrieval timeout, grader key/base URL, reader model, and whether closed-book fallback occurred. |
| "Run MiniMax reader" | Use model config rules and set MiniMax endpoint/key/context length explicitly. |
| "Need full training checkpoint eval" | Route to `../training-and-data/SKILL.md` for training outputs, then return here for eval harness. |

## Boundaries

- Do not download hundreds of GB of indexes or tiles unless the user explicitly approves.
- Do not launch vLLM, search serves, or long benchmark jobs silently.
- Do not treat strict exact-match NQ/NQ-Tables scores as paper numbers; the paper used an LLM judge for those cells.
- Keep benchmark outputs and reports outside the runtime skill tree.

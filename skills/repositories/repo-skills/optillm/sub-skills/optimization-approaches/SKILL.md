---
name: optimization-approaches
description: "Choose, compose, tune, and verify OptiLLM inference-time
  optimization approaches such as MoA, BoN, MCTS, CePO, MARS, Z3, reflection,
  and reranking methods."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Optimization Approaches

Use this sub-skill when the task is to select, combine, tune, or troubleshoot OptiLLM's core inference-time optimization techniques.

## Read first for these tasks

- Choose an approach slug for math, coding, long reasoning, logical reasoning, answer selection, or proof tasks.
- Compose approaches with `&` pipelines or `|` parallel alternatives.
- Tune MCTS, BoN, `n`, RStar, CePO, or MARS parameters.
- Understand cost/latency tradeoffs from multi-call approaches.
- Plan benchmark/evaluation runs safely without launching expensive scripts by default.
- Diagnose approach failures with empty, truncated, or provider-incompatible responses.

Route server startup and OpenAI-compatible request plumbing to [../proxy-server/SKILL.md](../proxy-server/SKILL.md). Route plugins to [../plugins-and-tools/SKILL.md](../plugins-and-tools/SKILL.md). Route local-only decoding methods to [../local-inference-decoding/SKILL.md](../local-inference-decoding/SKILL.md).

## Approach selection shortcut

- **Fast low-risk reasoning:** `re2`, `cot_reflection`, `leap`, or `plansearch`.
- **Candidate generation/selection:** `bon`, `moa`, `self_consistency`, `pvg`.
- **Search and solver-style tasks:** `mcts`, `rstar`, `z3`.
- **Math/code competition style:** `cepo` or `mars` when latency and token budget allow.
- **Direct pass-through:** `none` by itself only.

Use provider-compatible choices. Some endpoints do not support multiple completions, which limits `bon`/parallel sampling workflows.

## Composition patterns

```text
moa-gpt-4o-mini                  # one approach
cot_reflection&moa-gpt-4o-mini   # pipeline, left to right
bon|moa|mcts-gpt-4o-mini         # parallel alternatives, returns multiple responses
```

Approach selection can also come from request body `optillm_approach` or prompt tags when the server is in auto mode.

## Important references and script

- [references/approach-catalog.md](references/approach-catalog.md) catalogs verified slugs, signatures, defaults, and task fit.
- [references/cepo-and-mars.md](references/cepo-and-mars.md) covers the advanced CePO and MARS methods, configuration, and evaluation caveats.
- [references/evaluation-and-benchmarks.md](references/evaluation-and-benchmarks.md) explains benchmark scripts as reference-only workflows and how to plan safe runs.
- [references/troubleshooting.md](references/troubleshooting.md) covers provider limitations, bad responses, token/cost issues, and dependency failures.
- Run `python scripts/approach_matrix.py --help` to list approaches or parse a model string without provider calls.

## Minimal offline validation

```bash
python scripts/approach_matrix.py --parse 'bon|moa|mcts-gpt-4o-mini'
```

Expected parse shape is operation `OR`, approaches `bon,moa,mcts`, model `gpt-4o-mini`.

## Tuning checklist

1. Confirm provider supports the request shape (`n`, system messages, max token fields, streaming).
2. Start with the cheapest approach that addresses the failure mode.
3. Add multi-call approaches only when accuracy matters more than latency/cost.
4. Bound `max_tokens`, MCTS simulations/depth, BoN candidates, MARS agents/iterations, and CePO planning counts.
5. For proof tasks, preserve full reasoning visibility and be careful with answer extraction or `<think>` stripping.
6. For code tasks, verify whether answer extraction should preserve code fences.
7. Run safe mock-client tests before real provider benchmarks when editing the repo.

## Native evidence anchors

The source repository validates approach imports, mock-client calls, response guards for bad provider outputs, and request-scoped MCTS parameters in safe tests. Benchmark scripts exist for MATH-500, AIME, Arena Hard, FRAMES, SimpleQA, IMO, and OptiLLMBench, but they require datasets, provider calls, and longer runtimes; treat them as explicit evaluation workflows, not default smoke tests.

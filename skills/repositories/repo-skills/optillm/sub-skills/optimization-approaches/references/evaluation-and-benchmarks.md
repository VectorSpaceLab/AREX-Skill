# Evaluation and Benchmark Planning

OptiLLM includes benchmark and dataset scripts, but they are not default smoke tests. Use this reference when a task explicitly asks to evaluate approaches.

## Benchmark families represented by source scripts

- AIME / IMO / IMO Bench: competition math and proof tasks.
- MATH-500: math reasoning.
- Arena Hard Auto: open-ended instruction-following evaluation.
- FRAMES and SimpleQA: factual/longer-answer QA.
- OptiLLMBench: package-specific benchmark generation and evaluation.
- Router classifier training: `train_optillm_classifier.py` supports the router plugin, not ordinary inference.

## Why these scripts are reference-only by default

Most benchmark scripts need at least one of:

- Provider API keys.
- Network access to datasets or model endpoints.
- Long runtimes and many LLM calls.
- Large output files or leaderboard-specific formats.
- Optional packages from `scripts/requirements.txt`.

Do not run them as a quick correctness check unless the user explicitly authorizes cost, credentials, datasets, and runtime.

## Safe evaluation plan

1. **Choose a minimal problem set.** Start with one or a few examples before a full benchmark.
2. **Fix the model and approach.** Record base model, approach string, request config, temperature, max tokens, and provider.
3. **Bound cost.** Set small counts (`n`, BoN candidates, MARS agents/iterations, CePO planning counts) for smoke runs.
4. **Define answer extraction.** For numerical tasks, use consistent extraction; for proofs/code, avoid stripping required reasoning or code fences.
5. **Store outputs separately.** Keep raw provider responses and parsed results for auditing.
6. **Compare against direct baseline.** Run `none` or raw provider output with the same prompt/model where possible.
7. **Scale only after smoke success.** Move from smoke to subset to full benchmark.

## Native tests before benchmarks

When editing or validating the repo, run CPU-safe tests first:

```bash
python -m pytest tests/test_approaches.py -q
python -m pytest tests/test_reasoning_simple.py -q
```

Use this skill's root `scripts/run_safe_native_checks.sh` if you are inside a checkout and want a bounded native check wrapper.

## Approach-specific evaluation caveats

- `moa`, `bon`, `self_consistency`, `pvg`, `cepo`, and `mars` can multiply provider calls.
- `mars` proof tasks may need thinking tags disabled or answer extraction mode changed.
- `cepo` majority rating needs answer formats compatible with extraction.
- `z3` depends on successful code/expression extraction and should be checked for solver-time or code execution limits.
- Endpoints without multiple-completion support can distort comparisons for sampling approaches.

## Reporting template

For each run, record:

```text
model: <base model>
approach: <slug or composition>
provider/base_url: <provider family, not secret>
request_config: <n, max_tokens, approach-specific knobs>
dataset/subset: <benchmark and count>
answer extraction: <method>
accuracy/pass rate: <metric>
latency/cost: <if available>
failures: <timeouts, empty responses, parse failures>
```

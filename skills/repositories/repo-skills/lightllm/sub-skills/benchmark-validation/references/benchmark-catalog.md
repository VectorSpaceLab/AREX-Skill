# Benchmark catalog

This catalog groups the repository-native validation workflows by purpose.
Use the smallest benchmark that answers the user’s question.

## Service throughput and latency

| Script | Purpose | Typical use |
| --- | --- | --- |
| `test/benchmark/service/benchmark_qps.py` | QPS and latency across concurrent requests | Compare serving throughput. |
| `test/benchmark/service/benchmark_sharegpt.py` | ShareGPT-style request replay | Evaluate conversation-like workloads. |
| `test/benchmark/service/benchmark_multiturn.py` | Multi-turn service benchmark | Measure turn-by-turn latency and throughput. |
| `test/benchmark/service/benchmark_mcq.py` | Multiple-choice benchmark | Exercise a classification / choice-style serving path. |
| `test/benchmark/service/benchmark_prompt_cache.py` | Prompt-cache behavior | Validate cache reuse across turns. |
| `test/benchmark/service/benchmark_prompt_cache_multi_server.py` | Multi-server prompt-cache behavior | Validate cache reuse across split or federated serving setups. |

Common inputs:
- `--url` / `--model_url`
- `--model_name`
- `--tokenizer_path` or `--MODEL_DIR`
- concurrency / worker counts
- input and output token lengths
- result or log directory

## Static inference

| Script | Purpose | Typical use |
| --- | --- | --- |
| `test/benchmark/static_inference/test_model.py` | Text-model inference speed | Measure a model package without the full service benchmark wrapper. |
| `test/benchmark/static_inference/test_vit.py` | Vision transformer inference speed | Exercise multimodal / vision-side inference. |
| `test/benchmark/static_inference/profile_demo.py` | Profiling-oriented demo | Inspect a smaller inference path with profiling context. |

## Accuracy / scenario regressions

| Script | Purpose | Notes |
| --- | --- | --- |
| `test/acc/test_pd.sh` | PD topology regression | Depends on the PD service topology being ready. |
| `test/acc/test_qwen3.sh` | Qwen3 scenario regression | Model-specific regression coverage. |
| `test/acc/test_qwen3_vl.sh` | Qwen3-VL regression | Multimodal scenario coverage. |
| `test/acc/test_deepseekr1.sh` | DeepSeek-R1 scenario regression | Model-specific coverage. |
| `test/acc/test_deepseekr1_mtp*.sh` | MTP variants | Requires the corresponding draft-model / MTP setup. |
| `test/acc/test_deepseekv32_ep.sh` | EP variant regression | Requires the matching backend path. |

## Format and constrained-output validation

| Script / test | Purpose |
| --- | --- |
| `test/format_out/test_constraint_server.py` | Constraint server behavior. |
| `test/format_out/test_demo.py` | Demo path for constrained output. |
| `test/format_out/test_xgrammar_constraint.py` | xgrammar-based constrained output behavior. |
| `format_out/impl.py` | A direct helper for regex / JSON-schema-guided generation. |

## Existing repo-local evidence skills

These are not generated runtime skills yet, but they are useful evidence:

- `skills/test_model/SKILL.md`
- `skills/test_model/qwen3-8b-pd-nixl/SKILL.md`
- `skills/lightllm-profiler-control/SKILL.md`

## How to choose a benchmark

- Use a single request smoke first if the user only needs a readiness check.
- Use throughput scripts when the user asks for QPS, latency, or concurrency.
- Use static inference when the user cares about the model-side kernel path.
- Use `test/acc` when the question is about a specific model family or PD
  regression scenario.
- Use format/output validation when the user is debugging constrained generation
  or structured outputs.

## Result logging

Common outputs include:

- a per-run log directory,
- a summary file,
- benchmark-specific timing tables or percentiles,
- and optional cached result files for repeat comparisons.

Record the endpoint family and tokenizer / model path used for the run so that
latency numbers can be compared meaningfully later.

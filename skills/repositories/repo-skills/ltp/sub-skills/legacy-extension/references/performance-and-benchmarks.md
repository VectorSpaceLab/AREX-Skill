# Performance and Benchmark Notes

## What legacy optimizes

The legacy extension is written in Rust and targets fast CWS/POS/NER using averaged/perceptron-style models. It trades the full neural task set for speed and lightweight CPU execution.

## Reported benchmark context

The repository documentation reports legacy CWS and CWS/POS/NER pipeline throughput improvements over older LTP 3-style Python/C++ bindings, with higher throughput as thread counts increase. Those numbers were measured on specific hardware and benchmark files. Treat them as comparative evidence, not guaranteed production throughput.

## Why bundled helpers do not run benchmarks

Benchmark scripts require model files and sizable corpus inputs. Running them automatically would create long CPU jobs and may need files that are not present. This skill therefore bundles only safe import/rule/trainer-validation helpers and leaves benchmark execution to explicit user approval.

## If a user asks to benchmark

1. Confirm model files and corpus paths.
2. Record CPU model, thread count, package versions, and `parallelism` setting.
3. Warm up before measuring.
4. Separate CWS-only, POS, NER, and full CWS/POS/NER pipeline timing.
5. Report tokens/sentences/KB per second with input size and sentence count.
6. Keep correctness checks: sample output and expected labels/spans.

## Performance pitfalls

- `parallelism=True` may not help tiny batches; use larger batches for throughput measurements.
- Custom CWS rules can change segmentation and downstream POS/NER inputs; benchmark after enabling domain rules.
- Missing model files or fallback to high-level Hugging Face loading can dominate timing.
- Compare legacy only on CWS/POS/NER; neural SRL/DEP/SDP/SDPG are different task families.

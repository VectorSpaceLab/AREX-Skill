# vLLM vs SGLang: Qwen3.5-4B Serving Benchmark

This directory is a curated evidence bundle from a DisCo Researcher session.
It contains the benchmark contract, deterministic workloads, selected server
commands, aggregate measurements, correctness comparisons, and version
summaries. It is intended to make the research decisions and reported results
auditable without publishing a machine-specific runtime workspace.

It is **not** a complete reproduction environment. Model weights, virtual
environments, caches, raw server logs, process and socket state, and full host
environment dumps are intentionally excluded. The recorded commands therefore
document the selected runs but are not directly executable from this directory
alone.

## Executive summary

The benchmark was run on August 31, 2026 local time on two NVIDIA A100-SXM4-40GB
GPUs. Both frameworks served the same Qwen3.5-4B checkpoint with BF16 weights,
tensor parallelism of 2, a 32,768-token maximum context, a 0.80 numeric GPU
memory limit, and the same external OpenAI-compatible completion client.

For the selected 1,024-input / 128-output workload:

- **SGLang had the best throughput and latency.** At concurrency 32 it reached
  **2,384.74 output tokens/s**, compared with **2,314.27 output tokens/s** for
  tuned vLLM, a 2.96% difference in favor of SGLang.
- **SGLang also won the serial latency profile.** Mean TTFT was 42.84 ms and
  mean TPOT was 5.065 ms, compared with 64.16 ms and 5.458 ms for vLLM.
- **vLLM used less peak GPU memory.** Under the throughput profile its peak was
  33,437 MiB on each GPU, while SGLang reached 35,312 MiB on GPU 0 and 34,812
  MiB on GPU 1. The aggregate peak was 4.63% lower for vLLM.
- Every timed request succeeded and reported exactly 1,024 prompt tokens and
  128 output tokens. In a separate serial greedy correctness lane, both
  frameworks succeeded on 8/8 prompts and produced byte-identical text on 7/8.

The machine-readable source for these headline values is
[`results/aggregate/comparison.json`](results/aggregate/comparison.json).

## Authoritative results

Values below are means across three independent client runs. `±` is the
standard deviation across those run-level values. P99 values are computed
within each run and then averaged across the three runs.

### Latency profile

Concurrency was 1, with 20 requests per run and 1,024 input tokens plus 128
output tokens per request.

| Metric | SGLang | Tuned vLLM | vLLM vs SGLang |
| --- | ---: | ---: | ---: |
| Request throughput | 1.457 ± 0.010 req/s | 1.320 ± 0.004 req/s | -9.41% |
| Output throughput | 186.54 ± 1.31 tok/s | 169.00 ± 0.51 tok/s | -9.41% |
| Mean latency | 686.12 ± 4.82 ms | 757.35 ± 2.27 ms | +10.38% |
| P99 latency | 701.33 ms | 774.79 ms | +10.47% |
| Mean TTFT | 42.84 ± 2.04 ms | 64.16 ± 2.15 ms | +49.78% |
| P99 TTFT | 57.36 ms | 76.42 ms | +33.23% |
| Mean TPOT | 5.065 ± 0.022 ms | 5.458 ± 0.002 ms | +7.76% |
| P99 TPOT | 5.146 ms | 5.509 ms | +7.05% |
| Peak GPU memory, physical 0 / 1 | 35,164 / 34,664 MiB | 33,437 / 33,437 MiB | lower for vLLM |

### Throughput profile

Concurrency was 32, with 128 requests per run and the same 1,024-input /
128-output shape.

| Metric | SGLang | Tuned vLLM | vLLM vs SGLang |
| --- | ---: | ---: | ---: |
| Request throughput | 18.631 ± 0.046 req/s | 18.080 ± 0.020 req/s | -2.96% |
| Output throughput | 2,384.74 ± 5.87 tok/s | 2,314.27 ± 2.61 tok/s | -2.96% |
| Total token throughput | 21,462.66 ± 52.83 tok/s | 20,828.40 ± 23.48 tok/s | -2.96% |
| Mean latency | 1,713.43 ± 3.90 ms | 1,764.19 ± 1.93 ms | +2.96% |
| P99 latency | 1,740.46 ms | 1,845.59 ms | +6.04% |
| Mean TTFT | 495.32 ± 3.08 ms | 506.34 ± 4.81 ms | +2.22% |
| P99 TTFT | 805.19 ms | 824.35 ms | +2.38% |
| Mean TPOT | 9.591 ± 0.007 ms | 9.904 ± 0.027 ms | +3.26% |
| P99 TPOT | 12.531 ms | 13.197 ms | +5.32% |
| Peak GPU memory, physical 0 / 1 | 35,312 / 34,812 MiB | 33,437 / 33,437 MiB | lower for vLLM |
| Peak aggregate GPU memory | 70,124 MiB | 66,874 MiB | -4.63% |

The complete aggregate records are available under
[`results/aggregate/`](results/aggregate/), including the per-framework
latency and throughput files.

## Correctness verification

Correctness was measured in an independent serial lane rather than inferred
from the performance runs. It used eight fixed prompts, greedy decoding
(`temperature=0`), `seed=42`, `ignore_eos=true`, 32 output tokens, and
concurrency 1.

- Successful responses: **8/8 in both frameworks**
- Exact expected prompt-token count: **8/8 in both frameworks**
- Exact requested output-token count: **8/8 in both frameworks**
- Byte-identical generated text: **7/8**
- The one non-identical response agreed for 120 characters before taking two
  different but coherent continuations. This observed difference is retained
  in the comparison artifact rather than hidden.

The comparison is in
[`results/aggregate/correctness_serial.json`](results/aggregate/correctness_serial.json).
The compact workload and the fixed correctness workload are in
[`workloads/correctness.jsonl`](workloads/correctness.jsonl) and
[`workloads/fixed_correctness.jsonl`](workloads/fixed_correctness.jsonl).

The timed performance lanes also recorded zero failures and exact 1,024/128
input/output token counts for every request: 60/60 latency-lane responses and
384/384 throughput-lane responses per framework.

## Controlled configuration

The shared benchmark contract is recorded in
[`config/benchmark.json`](config/benchmark.json). The important controls were:

| Control | Value in both frameworks |
| --- | --- |
| Model | Qwen3.5-4B |
| Physical GPUs | 0 and 1 only |
| GPU type | 2 × NVIDIA A100-SXM4-40GB |
| Tensor parallelism | 2 |
| Weight and activation dtype | BF16 |
| Quantization | None |
| Maximum context | 32,768 tokens |
| Numeric GPU memory limit | 0.80 per framework instance |
| Maximum running sequences | 256 |
| Endpoint | `/v1/completions` over loopback HTTP |
| Prompt/output shape | 1,024 input + 128 output tokens |
| Sampling | temperature 0, seed 42, ignore EOS |
| Prefix cache | Disabled |
| Timed repetitions | 3 |
| Server reuse | One warm server per framework; load time excluded from timed metrics |

The numeric memory fractions are equal, but their implementation semantics are
not identical: SGLang's setting covers model weights and static KV/cache pools,
while vLLM's setting is the executor's per-instance target. Peak memory is
therefore reported separately for each runtime rather than treated as a
perfectly interchangeable limit.

Selected framework-specific settings were:

- **SGLang:** chunked prefill, its resolved prefill and scheduler defaults,
  CUDA graphs, and radix cache disabled.
- **vLLM:** a bounded sweep selected `--max-num-batched-tokens 8192`, with
  chunked prefill, FlashAttention 2, CUDA graphs, and prefix caching disabled.

Speculative/MTP decoding and quantization were disabled in both runtimes.
The selected server commands are preserved in
[`commands/sglang_baseline.txt`](commands/sglang_baseline.txt) and
[`commands/vllm_final.txt`](commands/vllm_final.txt).

## vLLM bounded tuning

The tuning lane screened 64 requests with 1,024 input tokens, 128 output
tokens, and concurrency 32. These were one-run screening measurements, not the
final three-repetition measurements.

| Candidate | vLLM-only settings | Output tok/s | Mean TTFT | Mean TPOT | Outcome |
| --- | --- | ---: | ---: | ---: | --- |
| A | batch-token budget 4,096; prefix off; language-model-only | 2,272.60 | 435.3 ms | 10.627 ms | rejected |
| B | batch-token budget 8,192; prefix off; language-model-only | **2,313.11** | 518.3 ms | 9.774 ms | selected budget |
| C | batch-token budget 16,384; prefix off; language-model-only | 2,312.30 | 577.7 ms | 9.336 ms | no throughput gain |
| D | batch-token budget 8,192; prefix on; language-model-only | 2,199.69 | 657.8 ms | 9.421 ms | rejected |
| E | batch-token budget 2,048; prefix off; full model capability | 2,004.01 | 451.7 ms | 12.301 ms | rejected |

The final vLLM run used candidate B's 8,192-token scheduler budget but omitted
`--language-model-only` for capability parity with SGLang. Its final output
throughput was 2,314.27 tok/s, consistent with the screening result. The
individual screening aggregates are in
[`results/aggregate/vllm_tuning_a.json`](results/aggregate/vllm_tuning_a.json)
through [`results/aggregate/vllm_tuning_e.json`](results/aggregate/vllm_tuning_e.json).

An early diagnostic vLLM run left prefix caching enabled and reused identical
prompts across repetitions. Those measurements are excluded from the
authoritative aggregates; prefix caching is disabled in both selected
configurations.

## Metric definitions

The same external client measured both OpenAI-compatible servers.

- **Latency:** request start immediately before the HTTP POST through final
  streamed response completion.
- **TTFT:** request start through the first non-empty streamed text event.
- **TPOT:** `(latency - TTFT) / (reported_output_tokens - 1)`.
- **Request throughput:** successful requests divided by wall-clock makespan.
- **Output/total token throughput:** server-reported tokens divided by
  wall-clock makespan.
- **Peak GPU memory:** maximum physical-GPU memory used sampled at a requested
  100 ms interval.

Prompts are deterministic and tokenized offline to exact lengths. Their hashes,
seeds, and request counts are recorded in
[`workloads/manifest.json`](workloads/manifest.json); the workload files are
listed in [`versions/workload-hashes.txt`](versions/workload-hashes.txt).

## Version boundary and limitations

The version summary is in
[`versions/framework-versions.txt`](versions/framework-versions.txt), with
benchmark and validation notes in the other files under
[`versions/`](versions/).

The run used the following notable version combination:

- vLLM `0.28.1rc1.dev119+g56058fd57`, PyTorch `2.13.0+cu132`, CUDA reported by
  PyTorch as 13.2, and Transformers 5.16.1.
- SGLang `0.5.6.post3.dev9748+g6a9366f03`, PyTorch `2.13.0+cu130`, CUDA
  reported by PyTorch as 13.0, and Transformers 5.12.1.
- FlashInfer 0.6.17 in both environments.

The framework environments require different compatible CUDA-enabled runtime
stacks. Dtype, quantization, model, tensor parallelism, context, and workload
were held constant, but the runtime dependency stacks were not identical.
This benchmark therefore describes the observed behavior of these selected
builds, not a universal ranking of vLLM and SGLang.

Other limitations:

- Results are from two A100-SXM4-40GB GPUs and a single Qwen3.5-4B checkpoint.
- The checkpoint advertises a longer native context, but this benchmark fixes
  both servers at 32,768 tokens and is not a long-context evaluation.
- The correctness lane had one non-byte-identical greedy continuation. Both
  outputs were successful and coherent, but exact equivalence should not be
  assumed for every prompt or runtime combination.
- Model weights, installation inputs, raw server traces, and host evidence are
  not part of this public evidence bundle.

## Artifact map

| Path | Purpose |
| --- | --- |
| `config/benchmark.json` | Shared benchmark contract |
| `workloads/` | Deterministic request inputs and workload manifest |
| `commands/` | Selected SGLang and vLLM server command lines |
| `results/aggregate/` | Correctness, latency, throughput, and tuning aggregates |
| `versions/` | Version, hash, and validation summaries |
| `artifact-manifest.json` | Explicit list and scope of included files |

The bundle's file hashes are generated from the sanitized files currently in
this directory. For the exact boundary, see
[`artifact-manifest.json`](artifact-manifest.json).

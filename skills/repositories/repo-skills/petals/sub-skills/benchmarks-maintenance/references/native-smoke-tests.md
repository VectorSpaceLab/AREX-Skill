# Native Smoke Selection and CI-Style Maintenance

This reference is for planning and maintenance triage. Do not run native tests, benchmarks, model downloads, DHT nodes, or servers without explicit approval.

Distributed native checks need environment variables for model id, reference model id, optional adapter id, and private DHT peer multiaddrs. Missing values cause early configuration errors.

A CI-style private CPU swarm pattern starts a DHT bootstrap, starts several CPU servers with explicit `--device cpu`, `--torch_dtype float32`, private peers, block ranges, and tiny throughput, then runs focused checks and tiny benchmark invocations. Every background process must have tracked PIDs and cleanup on success, failure, timeout, or interruption.

Select checks by changed area rather than running everything:

| Changed area | Candidate category |
| --- | --- |
| Import/package laziness | base import and optional bitsandbytes-laziness check |
| DHT routing and sequence choice | focused route/remote-sequence checks in a live private swarm |
| Full generation behavior | small exact-generation checks with a reference model |
| Server stats/cache/scheduling | local utility checks plus live swarm where needed |
| Throughput utilities | CPU compute smoke and speedtest dependency probe |
| Dtype/tensor parallel | model-family-specific dtype and tensor-parallel checks |
| PEFT/adapters | safetensors adapter safety and adapter-enabled generation only when backend stack is verified |

If required variables, credentials, model access, or cleanup permission is missing, stop at command construction and report the blocker.

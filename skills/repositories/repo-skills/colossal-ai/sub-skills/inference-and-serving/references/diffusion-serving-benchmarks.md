# Diffusion, Serving, and Benchmark Notes

## Stable Diffusion 3 command shape

ColossalAI examples use a diffusion pipeline with a model path and prompt:

```bash
colossalai run --nproc_per_node 1 sd3_generation.py -m MODEL_PATH -p "hello world"
```

Patched parallelism uses more processes:

```bash
colossalai run --nproc_per_node 2 sd3_generation.py -m MODEL_PATH
```

Use this as command anatomy, not as a dependency on the original example script. If the example script is absent, create a local script using `DiffusionPipeline` and ColossalAI inference config concepts.

## Serving and clients

Serving/client examples can involve long-running servers, ports, Locust traffic generation, or model downloads. Do not start them as validation by default. First verify imports, model/tokenizer paths, `InferenceConfig`, chosen port availability, authentication or API URL requirements, and one small request path.

## Kernel benchmarks

Kernel benchmark scripts are GPU-size-specific. Use them only for performance investigation, not functional correctness. For correctness, prefer small configuration/API tests and model-free command generation.

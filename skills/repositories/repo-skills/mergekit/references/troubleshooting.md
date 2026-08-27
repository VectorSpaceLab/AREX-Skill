# Cross-cutting troubleshooting

Read the nearest route first, then use this table to classify the failure.

## Install and import

If `import mergekit` or a console entry point fails, confirm the active Python,
`python -m pip check`, and the distribution versions for mergekit, torch,
Transformers, safetensors, and PEFT. Install optional `[evolve]` or `[vllm]`
only for the requested route; a missing `cma`, Ray, lm-eval, W&B, or vLLM does
not block core YAML merges. Do not repair a user-owned environment implicitly.

## Configuration and CLI

If Pydantic rejects the YAML, validate the top-level topology, required
method/base model, per-model parameter level, and mutual exclusion of modern
`tokenizer` versus legacy `tokenizer_source`. Use the bundled parser in the
merge-configs route; it does not check local files or tensor shapes. If Click
reports an unknown option, run the installed command's `--help` and keep the
exact version's spelling rather than copying flags from a different release.

## Models, architecture, and IO

A parseable model reference can still fail because a local file, revision,
config, tokenizer, shard, or Hub credential is missing. Compare model types,
module names, tensor shapes, and checkpoint key layouts before enabling any
exception. `--allow-crimes` permits risky mixing; it is not a compatibility
fix. Use the model-IO diagnostic and inspect output `config.json`, shard index,
all shards, tokenizer files, and model card after writing.

## Backend and memory

A CPU import is not CUDA verification. Probe `torch.cuda.is_available()`, device
count/capability, and one tiny allocation before using `--cuda` or `--gpu-rich`.
For OOM, reduce dtype, threads, asynchronous writes, or parallelism and choose
an explicit device; for `no kernel image` or `undefined symbol`, match the torch
CUDA build to the driver/GPU and isolate extension packages. `--trust-remote-code`
can execute model code and requires explicit trust.

## Outputs and external effects

Use a new output directory, preserve the exact command/config, and do not write
over an input or an existing model without approval. Network model downloads,
Hub uploads, W&B logging, Ray clusters, vLLM servers, and evaluator credentials
are external effects; stop and request the missing permission or dependency
instead of turning them into an implicit smoke test.

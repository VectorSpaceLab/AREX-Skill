# rag-and-acceleration troubleshooting

This file collects the common failure modes for CoRAG and LLMA. Shared repo-wide install, credential, GPU, and cache advice lives in the root LMOps troubleshooting reference; use this file for workflow-specific ordering and shape issues.

## Missing data, embeddings, or model cache

### CoRAG

Typical symptoms:

- the search server cannot find `e5-large-shard-*.pt` files;
- the E5 server starts but returns empty retrieval results;
- the vLLM server cannot resolve the requested model id;
- the evaluation job fails while loading `corag/multihopqa` or `corag/kilt-corpus`.

Checks:

- confirm the embedding directory contains all forty shards;
- confirm the E5 model name is valid for the local cache;
- confirm the CoRAG model id is available to the vLLM server;
- confirm the dataset cache can read the public CoRAG datasets.

Recovery:

- rerun the bundled planner and verify the staging order before restarting anything;
- clear only the broken service state, not the embeddings or outputs, if the run was interrupted;
- if the download step failed, stage embeddings again before starting the E5 service.

### LLMA

Typical symptoms:

- `model_path` points to an unconverted checkpoint;
- tokenizer/model loading fails because the weights are not in Hugging Face format;
- the input JSONL file does not contain `docs` or `result.text` when `forced_decoding` is expected.

Checks:

- verify the model directory is a converted LLaMA-family checkpoint;
- verify the JSONL records contain the prompt, document list, and any target text needed for benchmarking;
- verify the demo script is not being used as a substitute for a real GPU run.

## E5 and vLLM server ordering

The required order for CoRAG is:

1. embeddings staged;
2. E5 server ready on port `8090`;
3. vLLM server ready on port `8000`;
4. evaluation started only after both services respond.

Do not reverse the order. Starting evaluation before the search server is ready usually produces retrieval failures, empty contexts, or repeated retry noise.

Important log files:

- `e5_server.log`
- `vllm_server.log`

If a port is already occupied, first confirm it is the expected service. A stale process on the same port can look healthy but serve the wrong model or index.

## Port and log issues

### Search server

- default port: `8090`
- health check concept: local HTTP POST to the root route
- common issue: missing index directory or incomplete shards

### vLLM server

- default port: `8000`
- health check concept: OpenAI-compatible `/v1/models`
- common issue: insufficient GPUs or tensor-parallel mismatch

When either log shows startup failure, use the planner output to check the intended model, port, and output-file placement before retrying.

## GPU and hardware notes

- CoRAG was tested on eight NVIDIA A100 40GB GPUs.
- The vLLM launcher uses the detected GPU count as tensor parallel size.
- The E5 searcher places embedding shards on CUDA devices.
- LLMA's real decoder also expects a CUDA-capable environment and enough memory for the chosen model.

If the machine has fewer GPUs than the intended launch plan, reduce expectations or stop at planning time. Do not assume the default tensor-parallel size will work on a smaller machine.

## Decode-path length and search cost

For CoRAG:

- `max_path_length` controls the number of retrieval hops.
- higher values increase LLM calls, retrieval calls, and token usage;
- `decode_strategy=tree_search` or `best_of_n` costs more than `greedy`;
- setting `max_path_length < 1` effectively collapses to greedy behavior.

For LLMA:

- too small `n` may miss useful overlap triggers;
- too large `n` can be overly strict;
- too large `k` may waste verification work when only a short span overlaps;
- if no overlap exists, the method can behave like the baseline with added overhead.

## Metrics JSON confusion

For CoRAG, the standard metric JSON is named by task, split, and decode strategy. The most common fields are EM/F1 plus bookkeeping such as token consumption and sample count. If a downstream tool expects `accuracy`, check whether it is reading an older or alternative metrics file rather than the default implementation in this snapshot.

If the metrics file is missing:

- confirm the output directory exists and is writable;
- confirm the job completed past prediction generation;
- confirm the service tokens were not exhausted before the final answer pass.

## Reference-overlap assumptions for LLMA

LLMA only helps when the target output overlaps the references. Common reasons for poor results:

- the task is mostly novel generation;
- the documents are unrelated or too short;
- the prompt is not arranged in a way that exposes the reference overlap;
- the user expects approximate acceleration instead of verified lossless copying.

If in doubt, run the CPU demo script with a tiny handcrafted example. If the proposal/verification trace shows no copied span being accepted, the task likely has insufficient overlap for LLMA to matter.

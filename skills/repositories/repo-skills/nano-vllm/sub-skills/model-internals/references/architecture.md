# nano-vLLM architecture

## Public-to-internal flow

`LLM` is a thin subclass of `LLMEngine`. Constructing it creates a `Config`,
sets the sequence block size, starts tensor-parallel worker processes for ranks
above zero, builds a rank-0 `ModelRunner`, loads a fast tokenizer, initializes
the scheduler, and registers `exit()` for cleanup.

`generate` adds one `Sequence` per prompt, repeatedly calls `step()`, gathers
finished completion token ids by sequence id, decodes them with the tokenizer,
and returns dictionaries with `text` and `token_ids`.

## Scheduler and sequence state

A `Sequence` owns prompt token ids, appended completion ids, scheduling counters,
status, and a KV block table. The scheduler has waiting and running queues:

- Prefill consumes waiting sequences, allocating block tables and scheduling as
  many uncached prompt tokens as the token budget allows.
- Decode schedules one next-token step per running sequence, appending a KV
  block when needed.
- If no block is available, a running sequence can be preempted: its blocks are
  deallocated and it returns to waiting for recomputation.
- Finished sequences deallocate their KV blocks.

`BlockManager` hashes full prompt blocks with xxhash. Cached prefixes can be
reused only when a full block's hash and token ids match.

## ModelRunner execution

Each runner initializes a NCCL process group, selects its CUDA rank, sets the
default dtype to the Hugging Face config dtype, sets the default device to
CUDA, builds `Qwen3ForCausalLM`, loads safetensors weights, warms up the model,
allocates KV cache, and optionally captures CUDA graphs for decode.

Rank 0 receives public method calls. When `tensor_parallel_size > 1`, rank 0
serializes method names and arguments into shared memory and signals worker
rank events. Workers run the same method and remain in a loop until `exit`.

## Qwen3 model graph

`Qwen3ForCausalLM` contains `Qwen3Model` plus `ParallelLMHead`:

```text
input ids -> VocabParallelEmbedding
          -> repeated Qwen3DecoderLayer
          -> RMSNorm
          -> ParallelLMHead logits
```

Each decoder layer applies RMSNorm, Qwen3 attention, RMSNorm with residual, and
MLP. Attention uses packed QKV projection, optional Q/K RMSNorm when the config
has no QKV bias, rotary embedding, FlashAttention-backed attention, and a row
parallel output projection. The MLP uses a packed gate/up projection,
`SiluAndMul`, and a row parallel down projection.

## Attention context

Attention reads a global context object. Prefill context includes cumulative
query/key lengths, max sequence lengths, a slot mapping for storing new KV
entries, and optionally block tables when prefix cache is active. Decode
context includes slot mapping, current context lengths, and block tables.

The attention module first stores K/V tensors into cache when cache tensors are
attached. Prefill calls varlen FlashAttention; decode calls FlashAttention with
KV cache. If context is missing or mismatched, failures surface as shape,
indexing, or FlashAttention errors rather than clean user-facing exceptions.

## Tensor-parallel layers

- `VocabParallelEmbedding` shards vocabulary rows and all-reduces embeddings
  when the input token belongs to another shard.
- `ParallelLMHead` gathers shard logits on rank 0.
- `ColumnParallelLinear` shards output features.
- `MergedColumnParallelLinear` packs multiple column-parallel matrices such as
  gate/up.
- `QKVParallelLinear` packs Q/K/V into one output matrix and selects shard ids
  `q`, `k`, or `v` during loading.
- `RowParallelLinear` shards input features and all-reduces outputs.

These layers assume model dimensions divide by tensor-parallel size. Use the
contract checker before trying a new model or TP degree.

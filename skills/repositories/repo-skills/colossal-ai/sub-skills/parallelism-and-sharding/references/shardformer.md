# ShardFormer Reference

ShardFormer parallelizes supported Transformer-style models using policies and `ShardConfig`.

## Key APIs

Inspected signatures include:

```text
ShardConfig(tensor_parallel_process_group=None, sequence_parallel_process_group=None, pipeline_stage_manager=None, enable_tensor_parallelism=True, enable_all_optimization=False, enable_fused_normalization=False, enable_flash_attention=False, enable_jit_fused=False, enable_sequence_parallelism=False, sequence_parallelism_mode=None, parallel_output=True, make_vocab_size_divisible_by=64, gradient_checkpoint_config=None, ...)
ShardFormer(shard_config)
ModelSharder(model, policy, shard_config=None)
```

## Workflow

1. Launch distributed state and create process groups/stage managers through the plugin or cluster utilities.
2. Choose or let ColossalAI infer a model policy for the Hugging Face model family.
3. Create `ShardConfig` with tensor/sequence/pipeline options.
4. Shard the model through the plugin/Booster path or `ShardFormer` when doing low-level integration.
5. Run a tiny forward/backward or utility check before full training.

## Model-family signals

Tests and policies indicate coverage across common Hugging Face families such as BERT, GPT-2/GPT-J, OPT, Bloom, LLaMA, Mistral/Mixtral, Falcon, T5, ViT, SAM, Whisper, Qwen, ChatGLM, DeepSeek, BLIP2, and related command/custom model paths. Exact support depends on installed Transformers version and policy code in the package.

Use `scripts/shardformer_model_matrix.py` to print a routing checklist.

## Common policy questions

- Is the model architecture explicitly supported by a policy?
- Does the policy support the requested TP/SP/PP combination?
- Does the model require special vocabulary divisibility or tied-weight handling?
- Are fused attention/normalization flags supported on this GPU and dependency stack?
- Are model weights available locally or through an approved download path?

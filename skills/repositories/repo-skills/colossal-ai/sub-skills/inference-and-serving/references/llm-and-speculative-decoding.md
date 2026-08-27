# LLM Generation and Speculative Decoding

## Basic LLaMA-style command shape

```bash
colossalai run --nproc_per_node 1 llama_generation.py -m MODEL_PATH --max_length 128
```

Tensor-parallel inference uses more processes and a matching `--tp_size` argument in the user script:

```bash
colossalai run --nproc_per_node 2 llama_generation.py -m MODEL_PATH --max_length 128 --tp_size 2
```

The script name above represents a ColossalAI-style generation script; when the original example is not available, use the pattern to build your own script around `InferenceConfig` and `InferenceEngine`.

## Speculative decoding

Speculative decoding uses a smaller drafter model plus a main model. The drafter proposes tokens; the main model validates them in parallel.

Command shape:

```bash
colossalai run --nproc_per_node 1 llama_generation.py -m MAIN_MODEL --drafter_model DRAFTER_MODEL --max_length 128
```

For GLIDE-style drafter models, the drafter architecture can reuse main-model key/value caches. Verify the drafter model class and compatibility before enabling GLIDE mode.

## Validation checklist

- Main model path exists or download is approved.
- Tokenizer matches the model.
- `tp_size` equals launched process count unless the script explicitly handles another layout.
- Drafter model uses compatible tokenizer/vocabulary and device dtype.
- CUDA memory is sufficient for main + drafter + KV cache.
- Disable speculative decoding first if ordinary generation fails.

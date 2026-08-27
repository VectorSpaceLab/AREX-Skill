# Weight conversion for llama.cpp backend

Prefer the released GGUF bundle when possible. Convert weights yourself only when you need a different source checkpoint, quantization, or model variant compatible with the MOSS-TTS-Delay architecture.

## Target artifacts

The llama.cpp backend needs four groups:

1. **Backbone GGUF** — a Qwen3ForCausalLM-format language backbone converted to GGUF.
2. **Embedding tables** — NumPy `.npy` files used before the backbone.
3. **LM heads** — NumPy `.npy` files used after the backbone hidden state.
4. **Tokenizer directory** — `tokenizer.json` plus any supporting tokenizer files.

Expected final layout:

```text
MOSS-TTS-GGUF/
  MOSS_TTS_Q4_K_M.gguf              # or another chosen quantization name
  embeddings/
    embed_tokens.npy
    emb_ext_00.npy ... emb_ext_31.npy
  lm_heads/
    lm_head_text.npy
    lm_head_audio_00.npy ... lm_head_audio_31.npy
  tokenizer/
    tokenizer.json
    tokenizer_config.json
    special_tokens_map.json
    added_tokens.json / merges.txt / vocab.json as available
```

## Extraction logic from a full checkpoint

A full MOSS-TTS-Delay checkpoint stores a language backbone plus MOSS-specific multi-codebook embedding/head tensors. Extraction separates them:

| Source tensor pattern | Destination |
|---|---|
| `language_model.*` | Qwen3 backbone tensor named `model.*`. |
| `language_model.embed_tokens.weight` | `embeddings/embed_tokens.npy` and also backbone embedding tensor as applicable. |
| `emb_ext.<i>.weight` | `embeddings/emb_ext_<i:02d>.npy` for 32 external audio-code embeddings. |
| `lm_heads.0.weight` | `lm_heads/lm_head_text.npy` and Qwen3 `lm_head.weight`. |
| `lm_heads.<1..32>.weight` | `lm_heads/lm_head_audio_<i-1:02d>.npy`. |

The Qwen3 backbone config is derived from the checkpoint's `language_config` with:

```json
{
  "architectures": ["Qwen3ForCausalLM"],
  "model_type": "qwen3"
}
```

The extractor also records metadata such as `n_vq`, hidden size, text vocab size, audio vocab size, and destination directories. For the released Delay model, `n_vq` is 32, so the backend expects one text channel plus 32 audio channels.

## Conversion sequence

1. Start with a local full MOSS-TTS-Delay checkpoint containing `config.json` and either `model.safetensors` or `model.safetensors.index.json` plus shards.
2. Extract tensors into an intermediate directory:

   ```text
   extracted/
     qwen3_backbone/
       config.json
       model.safetensors or sharded safetensors + index
       tokenizer files copied from source checkpoint
     embeddings/
       *.npy
     lm_heads/
       *.npy
     extraction_meta.json
   ```

3. Convert `extracted/qwen3_backbone` to GGUF with the llama.cpp Hugging Face conversion utility.
4. Quantize the GGUF if desired. The released bundle uses Q4_K_M; quality/latency tradeoffs can be evaluated with Q8_0, Q6_K, Q5_K_M, and Q4_K_M.
5. Assemble the final runtime layout by placing the GGUF, `embeddings/`, `lm_heads/`, and tokenizer files under one configured `MOSS-TTS-GGUF` directory.
6. Run the bundled config inspector on the YAML that points to those artifacts.
7. Run a short inference smoke test before any benchmark.

Example GGUF conversion pattern:

```bash
python <llama-cpp>/convert_hf_to_gguf.py \
  <work>/extracted/qwen3_backbone \
  --outfile <work>/MOSS_TTS_F16.gguf \
  --outtype f16

<llama-cpp>/build/bin/llama-quantize \
  <work>/MOSS_TTS_F16.gguf \
  <work>/MOSS_TTS_Q4_K_M.gguf \
  Q4_K_M
```

Use the paths and quantization names appropriate to the installed llama.cpp version.

## Validation checklist

Before running generation, verify:

- `backbone_gguf` points to the final `.gguf` file, not the intermediate safetensors directory.
- `embedding_dir` contains `embed_tokens.npy` and 32 `emb_ext_*.npy` files.
- `lm_head_dir` contains `lm_head_text.npy` and 32 `lm_head_audio_*.npy` files.
- `tokenizer_dir/tokenizer.json` exists and matches the source checkpoint.
- The GGUF was converted from the matching `language_config`; hidden size/vocab mismatches fail later during embedding or head operations.
- The C bridge was compiled against a llama.cpp version compatible with the GGUF.
- ONNX audio files or TensorRT engines are built separately; they are not produced by backbone conversion.

## Common conversion mistakes

- Using the full MOSS checkpoint directly as `backbone_gguf`. The backend needs a Qwen3 GGUF backbone plus separate NumPy side weights.
- Omitting tokenizer files. The prompt builder loads `tokenizer.json` through the Rust `tokenizers` library.
- Mixing embeddings/heads from one checkpoint with a GGUF converted from another checkpoint.
- Quantizing before proving the f16 GGUF loads. Debug conversion first, then quantize.
- Expecting TensorRT engines to be portable across machines. Rebuild engines on the target GPU/TensorRT stack.

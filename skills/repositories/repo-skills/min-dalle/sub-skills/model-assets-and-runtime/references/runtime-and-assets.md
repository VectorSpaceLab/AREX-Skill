# Runtime and Model Assets

This reference covers cache layout, model asset names, Hugging Face download behavior, model-size constants, and safe runtime choices for min(DALL·E). Use it before any full generation run.

## Cache directory layout

`models_root` defaults to `pretrained`, but callers may set it to any writable directory. The constructor creates the variant directory and shared VQGAN directory when they do not already exist.

```text
models_root/
  dalle_bart_mega/        # when is_mega=True
    vocab.json
    merges.txt
    encoder.pt
    decoder.pt
  dalle_bart_mini/        # when is_mega=False
    vocab.json
    merges.txt
    encoder.pt
    decoder.pt
  vqgan/
    detoker.pt
```

Only one of `dalle_bart_mega/` or `dalle_bart_mini/` is required for a chosen run. `vqgan/detoker.pt` is shared by both variants.

## Hugging Face asset URL behavior

The asset base URL is:

```text
https://huggingface.co/kuprel/min-dalle/resolve/main/
```

Local filenames are normalized to the names shown above, but the remote filenames differ by variant:

| Asset purpose | Mega remote name (`is_mega=True`) | Mini remote name (`is_mega=False`) | Local path under `models_root` |
|---|---:|---:|---|
| Download trigger/config | `config.json` | `config.json` | not persisted by the package |
| Vocabulary | `vocab.json` | `vocab_mini.json` | `dalle_bart_mega/vocab.json` or `dalle_bart_mini/vocab.json` |
| BPE merges | `merges.txt` | `merges_mini.txt` | `dalle_bart_mega/merges.txt` or `dalle_bart_mini/merges.txt` |
| Encoder weights | `encoder.pt` | `encoder_mini.pt` | `dalle_bart_mega/encoder.pt` or `dalle_bart_mini/encoder.pt` |
| Decoder weights | `decoder.pt` | `decoder_mini.pt` | `dalle_bart_mega/decoder.pt` or `dalle_bart_mini/decoder.pt` |
| VQGAN detokenizer weights | `detoker.pt` | `detoker.pt` | `vqgan/detoker.pt` |

Important side effects:

- Constructing `MinDalle` always initializes the tokenizer.
- Tokenizer initialization makes a `config.json` request to the asset base URL before checking local `vocab.json` and `merges.txt`.
- If tokenizer files are missing, tokenizer download requests `config.json` again and then requests the variant-specific vocabulary and merge files.
- With `is_reusable=True`, construction also initializes encoder, decoder, and detokenizer, downloading missing `.pt` files and loading them into memory.
- With `is_reusable=False`, construction still initializes/downloads the tokenizer, but encoder/decoder/detokenizer are loaded later during generation and may be deleted between stages.
- The package writes HTTP response bodies directly to destination files and does not perform status-code, checksum, or minimum-size validation. Treat tiny `.pt`, HTML, JSON error pages, or zero-byte files as suspect.

## Model variant constants

Both variants use 64 text-token slots and sample 256 image tokens per image. The variant flag changes architecture size and vocabulary counts:

| Constant | Mega (`is_mega=True`) | Mini (`is_mega=False`) |
|---|---:|---:|
| DALL·E BART directory | `dalle_bart_mega` | `dalle_bart_mini` |
| Layer count | 24 | 12 |
| Attention heads | 32 | 16 |
| Embedding width | 2048 | 1024 |
| GLU hidden width | 4096 | 2730 |
| Text vocabulary count | 50272 | 50264 |
| Image vocabulary count for decoder embeddings | 16415 | 16384 |
| Text token count | 64 | 64 |
| Image token count | 256 | 256 |

Practical choice:

- Use Mega for highest-fidelity behavior when GPU memory and download time are acceptable.
- Use Mini when memory, latency, or disk budget is tight, or when a smoke workflow should prove control flow without the larger BART weights.
- Do not mix Mega tokenizer/encoder/decoder assets with Mini assets. The local filenames are the same, so the directory name is the disambiguator.

## Device, dtype, and reusable loading

Constructor defaults:

- `device=None` selects `cuda` when `torch.cuda.is_available()` is true, otherwise `cpu`.
- `dtype` defaults to `torch.float32`.
- `is_mega=True` and `is_reusable=True` are the default full-quality, full-load behavior.

Guidance:

| Situation | Recommended setting | Rationale |
|---|---|---|
| CPU-only or unknown hardware | `device='cpu'`, `dtype=torch.float32`, usually `is_mega=False` for exploratory runs | CPU generation is slow and fp16/bf16 CPU kernels may be unsupported or slower. |
| CUDA GPU with limited VRAM | `device='cuda'`, consider `dtype=torch.float16`, consider `is_reusable=False` or Mini | fp16 reduces activation/weight memory; non-reusable mode trades repeated load time for lower peak memory. |
| Ampere-or-newer CUDA GPU | `device='cuda'`, consider `dtype=torch.bfloat16` | bfloat16 is recommended only where hardware and PyTorch support it. |
| Multiple generations from one process | `is_reusable=True` when memory permits | Encoder, decoder, and detokenizer stay resident after construction. |
| One-off generation under memory pressure | `is_reusable=False` | Loads and deletes components around stages, reducing resident memory but increasing disk I/O and initialization time. |
| Tokenizer/cache inspection only | Do not instantiate `MinDalle`; use a synthetic tokenizer check or file-system preflight | Avoids the constructor's network request and any weight loading. |

Notes:

- The generation path uses CUDA autocast contexts with the configured dtype around encoder/decoder calls. Unsupported dtype/device combinations can fail at runtime rather than at construction.
- `torch.cuda.empty_cache()` is called around stages, but it cannot compensate for a grid size or variant that exceeds available VRAM.
- `grid_size` affects image count as `grid_size ** 2`; memory for text/attention and detokenization grows with that count.

## Safe checks before full generation

Run these checks before approving a full text-to-image call:

1. Decide variant and cache root. Confirm that only the matching `dalle_bart_mega/` or `dalle_bart_mini/` directory is required for the requested run.
2. Check asset presence and obvious corruption without loading weights:
   - tokenizer: `vocab.json` exists, parses as JSON, and contains `<s>`, `</s>`, and `<unk>`;
   - merges: `merges.txt` exists, is non-empty, and has merge lines after the header;
   - weights: `encoder.pt`, `decoder.pt`, and `vqgan/detoker.pt` exist and have plausible non-zero sizes.
3. Run the bundled no-network tokenizer smoke: `python scripts/tokenizer_smoke.py --verbose` from this sub-skill directory.
4. Inspect PyTorch before selecting CUDA/dtype: `torch.cuda.is_available()`, GPU name/VRAM if CUDA is required, and whether fp16/bf16 kernels are expected to work.
5. If downloads are needed, confirm network/proxy/SSL access to the Hugging Face base URL and use a fresh cache directory so partial files are easy to spot.
6. If only API wiring is being checked, stop here and route generation recipes to `../text-to-image-generation/SKILL.md` rather than constructing a full model.

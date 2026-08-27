# Troubleshooting: Assets, Runtime, and Tokenization

Use this guide when min(DALL·E) fails before or during model asset setup, tokenizer initialization, device/dtype selection, or low-level tensor handling. For generation-loop parameters and output conversion, route to `../text-to-image-generation/SKILL.md`. For CLI, GUI, notebook, or Replicate issues, route to `../deployment-and-interfaces/SKILL.md`.

## Asset download or cache failures

Symptoms:

- Construction prints download messages and then fails with a `requests`, SSL, timeout, proxy, or HTTP-related error.
- A later `torch.load()` fails on a cached `.pt` file.
- `json.load()` fails for `vocab.json`, or tokenizer initialization fails after a download.

Likely causes:

- Missing files under the selected `models_root` trigger downloads from the min-dalle model host.
- The package writes response bodies directly and does not validate HTTP status codes or checksums.
- A partial download, HTML error page, proxy block, or zero-byte file may be stored at the expected filename.

Recovery:

1. Identify the requested variant: `dalle_bart_mega` when `is_mega=True`, `dalle_bart_mini` when `is_mega=False`; `vqgan/detoker.pt` is shared.
2. Check only file presence, JSON parseability, and non-zero/plausible sizes before loading weights.
3. If a file is tiny, zero bytes, or contains an HTML/JSON error response, move it aside and re-download in a fresh cache directory when network access is approved.
4. Use a cache directory dedicated to one run when diagnosing network failures so stale partial files do not mask the next attempt.
5. If the environment is offline, stage known-good assets into the exact cache layout before constructing `MinDalle`.

## Tokenizer initializes even when full generation is not intended

Symptoms:

- `MinDalle(is_reusable=False, ...)` still contacts the model host.
- A task meant to inspect API wiring unexpectedly downloads `vocab.json` or `merges.txt`.

Cause:

- The constructor always calls `init_tokenizer()`. `is_reusable=False` delays encoder/decoder/detokenizer loading, but not tokenizer initialization.

Recovery:

- For no-download API checks, inspect signatures or use this sub-skill's `scripts/tokenizer_smoke.py` instead of constructing `MinDalle`.
- For actual generation, pre-stage `vocab.json` and `merges.txt` in the chosen variant directory, then construct the model.

## CPU-only PyTorch when CUDA was expected

Symptoms:

- `torch.cuda.is_available()` is false.
- The constructor prints `using device cpu` when `device=None` was expected to pick CUDA.
- Passing `device='cuda'` raises CUDA initialization errors.

Recovery:

1. Verify that the installed PyTorch build supports CUDA, not just that the machine has an NVIDIA GPU.
2. Check the driver and PyTorch CUDA runtime compatibility before installing CUDA wheels.
3. Use `device='cpu'` and `dtype=torch.float32` for portability checks.
4. Do not claim CUDA verification from a CPU-only import. Re-run with a CUDA-enabled PyTorch build when CUDA generation is required.

## CUDA out of memory or process killed

Symptoms:

- `CUDA out of memory`, OS process kill, or severe slowdown during generation.
- Failures appear after increasing `grid_size`, using Mega, enabling progressive outputs, or setting `is_reusable=True`.

Recovery:

1. Reduce `grid_size`; image count grows as `grid_size ** 2`.
2. Use `is_mega=False` for the smaller Mini variant.
3. On CUDA, try `dtype=torch.float16`; on Ampere-or-newer CUDA, consider `torch.bfloat16` only after a backend check.
4. Use `is_reusable=False` for one-shot runs to avoid retaining all major modules after each phase.
5. Disable progressive outputs unless intermediate frames are required.

## Unsupported dtype or precision surprises

Symptoms:

- fp16/bf16 operations fail on CPU.
- Autocast warnings appear.
- Generation is slower or numerically unstable after changing dtype.

Recovery:

- Start with `torch.float32`, especially on CPU.
- Use `torch.float16` primarily for CUDA memory reduction.
- Use `torch.bfloat16` only where hardware and PyTorch explicitly support it; the public README points to Ampere-class GPUs for bfloat16.
- Keep dtype, device, and model variant constant when comparing outputs.

## Tokenizer output does not match prompt text

Symptoms:

- Case, accents, emoji, or non-ASCII punctuation seem ignored.
- Long prompts lose trailing detail.
- Many tokens map to the unknown id.

Cause:

- `TextTokenizer` demojizes emoji, lowercases text, drops non-ASCII characters, splits on spaces, applies BPE, maps missing subwords to `<unk>`, and generation truncates to 64 text tokens.

Recovery:

1. Rewrite the prompt in plain ASCII words and put critical concepts early.
2. Run `python scripts/tokenizer_smoke.py --verbose --text "your prompt"` only to understand normalization behavior with a synthetic vocabulary. It is not the real model vocabulary.
3. If real vocabulary behavior must be inspected, use a verified cache containing the package's `vocab.json` and `merges.txt`, then construct a `TextTokenizer` directly from those files instead of full `MinDalle`.

## `top_k`, image-token, or shape errors

Symptoms:

- Index errors around sampling.
- Detokenizer shape errors or non-square grids.
- Custom token code produces unexpected image shapes.

Recovery:

- Keep `top_k` in `1..16384` because sampling slices logits to the first `2 ** 14` image tokens and indexes `top_k - 1`.
- Keep image token tensors shaped `(grid_size ** 2, 256)` before calling detokenization helpers.
- Ensure the number of images is a perfect square because the detokenizer infers `grid_size` with `sqrt(number_of_images)`.

## Import errors for dependencies

Symptoms:

- Import fails for `torch`, `PIL`, `requests`, `emoji`, `numpy`, or `typing_extensions`.

Recovery:

- Install the package runtime dependencies listed by the distribution metadata: `torch>=1.11`, `typing_extensions>=4.1`, `numpy>=1.21`, `pillow>=7.1`, `requests>=2.23`, and `emoji`.
- Re-run a no-download smoke such as `python scripts/tokenizer_smoke.py` before attempting full generation.
- If the task is CLI-specific, use the deployment/interface helper in dry-run mode first.

# Model Reconstruction Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| User asks for complete weights from this project | The project releases LoRA adapters, not original LLaMA full weights. | Explain the legal boundary. Ask the user to provide licensed original LLaMA-compatible base weights or a compatible base model path. |
| `adapter_model.bin` SHA256 mismatch | Corrupted download, wrong model variant, or incomplete extraction. | Re-download the LoRA archive/model, verify file size, and compare against `checksums.md` before merging. |
| Tokenizer SHA256 mismatch | Wrong tokenizer family or corrupted tokenizer. | Stop. Confirm whether the target is Chinese LLaMA or Chinese Alpaca; do not merge with an untrusted tokenizer. |
| Assertion says tokenizer vocab is smaller than model vocab | Tokenizer path does not match model or LoRA family. | Use the tokenizer packaged with the intended LoRA/model family. Alpaca and LLaMA tokenizers differ. |
| Error mentions `[49953, 4096]` or LoRA weight/tokenizer vocab mismatch | Common sign of using a LLaMA tokenizer with an Alpaca LoRA or vice versa. | Use LLaMA tokenizer with Chinese LLaMA LoRA and Alpaca tokenizer with Chinese Alpaca LoRA. |
| Merge script downloads from Hugging Face unexpectedly | `--lora_model` was a model id or local path did not contain `adapter_model.bin`. | If offline, provide a local LoRA directory containing adapter files. If online download is intended, confirm network and cache policy. |
| `ModuleNotFoundError: peft`, `transformers`, `torch`, or `sentencepiece` | Runtime environment lacks core requirements. | Install the package requirements compatible with `torch==1.13.1`, `transformers==4.30.0`, PEFT, and `sentencepiece==0.1.97`, then rerun `--help` first. |
| `peft.LoraModel` API or `merge_and_unload` mismatch | PEFT version differs from the source era. | Prefer the PEFT commit used by the original `requirements.txt`; if using a newer PEFT, run a small metadata-only import check before large merges. |
| Process is killed or machine swaps heavily | Insufficient RAM for standard merge. | Use `merge_llama_with_chinese_lora_low_mem.py`, reduce other processes, ensure enough temporary disk, or move to a larger machine. |
| Output directory already contains partial shards | Interrupted merge or accidental reuse. | Do not overwrite silently. Move partial output aside or use a fresh `--output_dir` after user approval. |
| PTH output has wrong shard count | Wrong inferred model size, interrupted save, or output cleanup issue. | Match shard count to model size: 7B=1, 13B=2, 33B=4, 65B=8. Re-run into a clean output directory if incomplete. |
| Hugging Face output loads tokenizer but not model | Merge failed after tokenizer save, or output lacks model files. | Inspect script logs. Re-run merge after verifying base model path, LoRA path, and disk space. |
| `NotImplementedError` in state dict key translation | Model architecture differs from original LLaMA keys. | These scripts target LLaMA-style architectures. Use a compatible base or a different converter for newer architectures. |
| `nvcc not found` | Not normally required for these CPU merge scripts. | Ignore unless installing/building CUDA extensions for a separate workflow. Merge scripts load on CPU. |
| Resulting Alpaca responses are short or poor | Using Plus where Pro is recommended, wrong prompt template, or wrong model family. | For chat/instruction tasks, prefer Chinese Alpaca Pro when available and route to inference guidance for `--with_prompt`. |

## Safe Retry Checklist

1. Verify original base, LoRA adapter, and tokenizer SHA256 when expected digests exist.
2. Confirm model family and tokenizer family before running a large merge.
3. Use a new output directory or intentionally clear partial outputs.
4. Prefer Hugging Face output when downstream use is Transformers/Gradio/API/C-Eval.
5. Use low-memory merge for 13B/33B or constrained RAM.
6. Run a metadata-only tokenizer load before a generation test.

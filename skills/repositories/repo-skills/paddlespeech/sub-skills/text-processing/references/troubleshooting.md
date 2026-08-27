# Text Processing Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Invalid input string` | Cleaning removed all supported characters. | Preview with `prepare_punctuation_input.py`; provide Chinese/letter/digit content. |
| Import error involving AIStudio SDK or PaddleNLP | Version mismatch for punctuation tokenizer/model imports. | Align PaddleNLP and AIStudio SDK; verify `from paddlespeech.cli.text.infer import TextExecutor`. |
| First punctuation run is slow | Pretrained ERNIE resources download. | Confirm network/cache and use `PPSPEECH_HOME` for controlled cache. |
| `.job` text with spaces fails | Shared parser expects id/value only. | Use direct `--input` for spaced text or one safe whitespace-free item per line. |
| MFA/G2P/TN recipe fails on missing tools | External aligner/scoring/tokenizer tools not installed. | Treat as recipe preparation; install tools only after user approval. |
| English punctuation quality poor or unsupported | Released punctuation resources are Chinese-focused. | Do not promise English punctuation restoration from these tags; use another tool if needed. |

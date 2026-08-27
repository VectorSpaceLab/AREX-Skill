# PAWS-X Troubleshooting

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError: cannot import name 'AdamW' from transformers` | The installed `transformers` release is too new | Use a 4.x release that still exports `AdamW`. |
| The tokenizer or model download stalls | `bert-base-multilingual-cased` is fetched on first use | Allow network access or prefill the Hugging Face cache. |
| Cached features are missing or stale | The cache directory is not writable or the files were generated with a different tokenizer config | Delete the stale cache and regenerate it with the same settings. |
| The loader cannot find a TSV file | The dataset root does not contain the expected `pawsx` tree | Restore the raw TSV files or point the workflow at the correct dataset root. |
| Raw preprocess helpers fail on `networkx` | The legacy helper assumes old `networkx` APIs | Treat the raw preprocess path as compatibility-sensitive and use a patched or older networkx stack if you really need it. |
| The example fails before any training step | The script was run from the wrong directory or the local helper modules did not resolve | Run from the benchmark directory and keep the helper modules together. |

## Recovery path

1. Confirm the raw TSV tree.
2. Confirm the cache directory is writable.
3. Confirm `transformers.AdamW` exists.
4. Confirm CUDA is available.
5. Re-run the bundled PAWS-X data checker if the layout still looks wrong.

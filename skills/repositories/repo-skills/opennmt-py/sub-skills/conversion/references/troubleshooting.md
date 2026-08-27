# Conversion Troubleshooting

## Purpose

Use this reference when checkpoint averaging, release, CTranslate2 conversion, external-family conversion, vocabulary/embedding extraction, or LoRA merging fails. Keep private model paths, hub tokens, cache directories, and local environment names out of notes and reports.

## General checkpoint inspection failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `torch.load` refuses to unpickle or reports unsupported globals. | Newer PyTorch defaults to safer loading, while OpenNMT-py checkpoints often contain `argparse.Namespace` and other Python objects. | Inspect only trusted checkpoints. The bundled checker calls `torch.load(..., weights_only=False)` because OpenNMT-py metadata needs it. If trust is unclear, isolate the file first instead of loading it in a shared environment. |
| CUDA memory changes during inspection. | A script loaded tensors without `map_location="cpu"` or model code moved tensors to GPU. | Use `scripts/check_checkpoint_file.py`; it maps tensors to CPU/fake tensors and does not call CUDA. For custom inspection, always pass `map_location="cpu"`. |
| The checker says fake loading failed. | The checkpoint uses a pickle pattern or object not supported by fake tensors. | If the file is trusted and small enough for RAM, retry `--allow-cpu-tensor-load`. Otherwise inspect on a larger isolated CPU host or produce a smaller metadata-only checkpoint. |
| Missing `model`, `generator`, `vocab`, or `opt`. | The file is not an OpenNMT-py training checkpoint, is a CT2 directory file, is a sidecar safetensors shard, or is an adapter-only artifact. | Verify the artifact family. CT2 has directory files such as `model.bin`; safetensors sidecars need their companion metadata `.pt`; LoRA adapters need the compatible base checkpoint. |

## Averaging failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| KeyError while averaging `model` or `generator`. | Input checkpoints do not have identical tensor keys. | Compare checker `tensor_sections` summaries for every input. Average only checkpoints from the same architecture, vocab, and training run family. |
| Output quality collapses after averaging. | Averaged checkpoints came from different training regimes, vocabularies, data transforms, or LoRA/base states. | Compare `opt` fields such as `model_task`, layer counts, hidden size, `share_vocab`, tokenizer fields, and LoRA/quantization fields. Re-average only compatible adjacent checkpoints. |
| Output dtype is unexpected. | The average command preserves input dtype unless `-fp32` is set. | Use `onmt_average_models -fp32` when a full-precision release is required; otherwise document the intended dtype. |
| CPU out-of-memory. | Averaging loads every tensor on CPU and accumulates averages. | Use fewer/lower precision checkpoints, a larger CPU-memory host, or pre-release checkpoints without optimizer state. Do not move averaging to GPU just to avoid CPU memory without planning GPU memory. |

## PyTorch release and CTranslate2 failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: ctranslate2` or converter import failure. | The CT2 optional dependency is missing or incompatible. | Install a CTranslate2 version supported by the OpenNMT-py install. Re-run `onmt_release_model --format ctranslate2` after import succeeds. |
| CT2 conversion fails with unsupported architecture or missing option fields. | The checkpoint was not created by a supported OpenNMT-py architecture path, or external conversion produced incomplete `opt`. | Inspect `option_summary`. Confirm `model_task`, encoder/decoder types, layer counts, hidden sizes, vocab sizes, and generator shapes before retrying. |
| CT2 output is a file instead of a directory, or inference expects `.pt`. | The release command used `--format pytorch` or the inference config points at the wrong artifact type. | For CT2 use `--format ctranslate2 --output ct2_dir`. Point CT2 inference at the directory and keep `.pt` checkpoints for PyTorch inference/training. |
| Quantized CT2 model gives invalid or poor output. | Quantization mode is not appropriate for the target hardware/model or the wrong tokenizer/vocabulary is used. | Retry `float16` or no quantization for diagnosis. Verify CT2 `vocabulary.json` and tokenizer model paths in the inference config. |
| Released PyTorch checkpoint is still large. | Optimizer state was not removed or sidecar shards still contain large tensors. | Use `onmt_release_model --format pytorch`; verify checker reports `optim` as `None`. Large model tensors are expected to remain. |

## External/Hugging Face conversion failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Missing `pyonmttok`, `sentencepiece`, `safetensors`, `transformers`, or `huggingface_hub`. | External conversion utilities need optional tokenizer/model dependencies beyond the minimal import path. | Install only the optional packages required for the selected family. Re-run a help/import smoke check before loading full weights. |
| Local model directory error: missing `config.json`, tokenizer, weight index, or weight file. | The directory does not match the expected Hugging Face or original-family layout. | Confirm the required files for the chosen contract: HF-style config/tokenizer/weights, original LLaMA `params.json` plus consolidated shards and tokenizer model, or family-specific vocab file. |
| Hub download fails or returns permission errors. | Gated/private model, missing token, network issue, or local cache permission problem. | Use an explicit token only in the runtime command environment, never in reusable notes. If network is unavailable, stage files locally and use local-directory conversion. |
| `Can convert only awq models for now` or unknown quantization config. | The converter saw a quantization configuration it does not support. | Convert an unquantized checkpoint if available, or verify that the model's quantization config is AWQ with a supported backend/version. |
| Multiple PyTorch shards requested and conversion raises an error. | Some converters support multi-shard output only for safetensors. | Use `--format safetensors --nshards N`, or set `--nshards 1` for PyTorch output. |
| v2-to-v3 conversion fails on `imp`. | The legacy converter imports Python's removed `imp` module. | Use a Python version where `imp` exists or patch the converter to use modern importlib loading before executing it. |
| Output checkpoint lacks `vocab` or `opt`. | Conversion stopped early or a task-local converter copied only tensors. | Rebuild the OpenNMT-py metadata. A usable OpenNMT-py checkpoint needs `model`, `generator`, `vocab`, and `opt` for downstream release/training. |

## Vocabulary and embedding extraction failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `KeyError: 'src'` or `KeyError: 'tgt'`. | The checkpoint vocabulary does not have the requested side, or the checkpoint is not OpenNMT-py format. | Run the checker and choose an existing side. For shared LM vocabularies, source and target may be identical or one side may be enough for the target task. |
| Extracted vocabulary line count does not match `src_vocab_size` or `tgt_vocab_size`. | Vocab metadata and option fields are stale, padded, or from different conversion steps. | Compare actual vocab length, option vocab sizes, and generator weight rows. Prefer actual vocab length for file validation and investigate mismatches before release. |
| Embedding conversion reports many missing tokens. | Wrong pretrained embedding file, tokenization mismatch, skipped header lines, or using source embeddings for target vocab incorrectly. | Confirm GloVe vs word2vec header behavior, `skip_lines`, tokenizer normalization, and whether source and target vocabularies are shared. |
| Extracting embeddings fails while building the model. | The OpenNMT-py package/options do not match the checkpoint, optional tokenizer dependency is missing, or the checkpoint was externally converted with incomplete options. | Validate model options, install the required tokenizer packages, and patch missing default option fields only when you know the target OpenNMT-py version. |

## LoRA merge or concat failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Base checkpoint fails to load into the LoRA model. | Base and LoRA checkpoints are from different architectures, vocabularies, hidden sizes, quantization settings, or model tasks. | Compare both checker outputs: `model_task`, layer counts, hidden sizes, vocab sizes, tokenizer fields, and tensor key samples. Use the exact base checkpoint used for LoRA fine-tuning. |
| Merged output still contains LoRA keys. | Merge did not run through eval-mode merge logic, or the wrong action/output format was used. | Choose `merge` for inference release. After output, inspect model keys for `lora`; merged PyTorch output should filter LoRA-specific keys. |
| Optimizer state missing after concatenation. | `merge` was used instead of `concat`, or the LoRA checkpoint did not carry optimizer state. | Use `concat` only for continued training and verify `optim` in the output. For inference release, missing optimizer state is expected. |
| Safetensors LoRA output has missing shard files. | Output prefix or base shard discovery did not match the expected safetensors sidecar layout. | Keep the metadata `.pt` and sidecar shards together. Check sidecar files with the same prefix and numeric suffix before release/inference. |
| Merge consumes too much CPU memory. | LoRA merging rebuilds the model and loads base plus adapter weights on CPU. | Use a larger-memory host, merge a smaller shard layout if supported, or perform a PyTorch release first to drop optimizer state. Do not silently switch to GPU without checking available memory. |

## When to stop and ask for more information

Stop before running conversion when any of these are unknown and cannot be inferred from the checkpoint checker:

- Which checkpoint family the input belongs to: OpenNMT-py `.pt`, CT2 directory, Hugging Face directory, original LLaMA shards, safetensors metadata plus sidecars, or LoRA adapter.
- Whether a `torch.load` pickle checkpoint is trusted.
- Which output is required: resumed training checkpoint, PyTorch inference checkpoint, CTranslate2 directory, vocab text file, embedding tensors, or merged LoRA release.
- Whether optional downloads or gated model access are allowed.
- Whether CPU memory is sufficient for full tensor loading or merge.

# Checkpoint and Conversion Tools

## Purpose

Read this reference when an OpenNMT-py task touches saved checkpoints, release artifacts, CTranslate2 conversion, external model-family conversion, vocabulary or embedding extraction, or LoRA weight merging. It distills the behavior of OpenNMT-py conversion entry points and source utilities into self-contained operating guidance. Do not require a future agent to open or execute source checkout scripts from a particular repository path.

## Evidence and invariants

Evidence was distilled from these repo-relative sources: `onmt/bin/average_models.py`, `onmt/bin/release_model.py`, source utility contracts under `tools/`, the Vicuna fine-tuning/conversion example, CT2 test fixtures, and CLI help for the installed average/release entry points.

OpenNMT-py `.pt` checkpoints are Python pickle files loaded with `torch.load`. A normal training checkpoint is a dictionary with these important sections:

| Section | Expected role |
| --- | --- |
| `model` | Model state dictionary, usually excluding generator weights. |
| `generator` | Generator/output projection state dictionary. |
| `vocab` | Vocabulary data, usually keyed by `src` and `tgt` for seq2seq and often shared for LM conversions. |
| `opt` | Training/model options, often an `argparse.Namespace` with architecture, vocab, tokenizer, quantization, and LoRA fields. |
| `optim` | Optimizer state; can be large and is intentionally set to `None` for released inference checkpoints. |

Some conversion workflows save an OpenNMT-py metadata `.pt` file plus sidecar `.safetensors` shards. In that case the `.pt` file still needs `vocab`, `opt`, and optimizer metadata, while tensor weights may live in files named with numeric shard suffixes.

## First diagnostic: inspect the checkpoint

From this sub-skill directory, run:

```bash
python scripts/check_checkpoint_file.py path/to/model.pt --json
```

Use the output before any destructive conversion:

- `top_level_keys` should include the sections needed by the workflow.
- `vocab_summary` should show the sides you expect (`src`, `tgt`, or both) and nonzero sizes.
- `option_summary` should include `model_task`, encoder/decoder types, layer counts, hidden sizes, vocab sizes, quantization fields, and LoRA fields when present.
- `tensor_sections.model` and `tensor_sections.generator` should have plausible counts and sample shapes.
- `conversion_readiness.average_models` and `conversion_readiness.release_model` flag missing sections that would make the standard package commands fail.

The helper uses CPU/fake-tensor loading by default. If fake loading is not supported by a checkpoint and the file is trusted and small enough for CPU RAM, retry with `--allow-cpu-tensor-load`.

## Average compatible checkpoints

Package entry point:

```bash
onmt_average_models \
  -models model_step_1000.pt model_step_2000.pt model_step_3000.pt \
  -output averaged.pt
```

Options verified from CLI help and implementation:

| Option | Meaning |
| --- | --- |
| `-models`, `-m` | One or more input checkpoints. Required. |
| `-output`, `-o` | Output checkpoint path. Required. |
| `-fp32`, `-f` | Cast averaged model and generator tensors to float32 before saving. |

Behavior to remember:

- The command loads every checkpoint on CPU.
- It copies `vocab` and `opt` from the first checkpoint.
- It averages matching `model` and `generator` tensor keys with an incremental mean.
- It writes `optim: None` in the final checkpoint.

Preflight checklist:

1. Run the bundled checkpoint checker on every input.
2. Confirm every input has `model`, `generator`, `vocab`, and `opt`.
3. Compare vocab sizes/sides and key counts; do not average checkpoints with different vocabularies or architectures.
4. If inputs are LoRA checkpoints, decide whether to merge/concat LoRA first; do not average a base checkpoint together with an adapter-only checkpoint.
5. Use `-fp32` only when the output should be full precision. Otherwise the averaged tensors keep their input dtype.

## Release a PyTorch inference checkpoint

Package entry point:

```bash
onmt_release_model \
  --model trained.pt \
  --output released.pt \
  --format pytorch
```

Behavior:

- Loads the checkpoint on CPU.
- Sets `optim` to `None`.
- Saves the remaining checkpoint dictionary to the output path.

Use this before distribution, CT2 conversion, or any workflow where optimizer state is unnecessary.

## Convert an OpenNMT-py checkpoint to CTranslate2

Package entry point:

```bash
onmt_release_model \
  --model released.pt \
  --output ct2_model_dir \
  --format ctranslate2 \
  --quantization int8_float16
```

Options verified from CLI help and implementation:

| Option | Meaning |
| --- | --- |
| `--model`, `-m` | Input OpenNMT-py checkpoint. Required. |
| `--output`, `-o` | Output model directory for CT2 or output checkpoint for PyTorch release. Required. |
| `--format` | `pytorch` or `ctranslate2`; default is `pytorch`. |
| `--quantization`, `-q` | CT2 quantization: `int8`, `int16`, `float16`, or `int8_float16`. |

Implementation fact: CT2 release calls `ctranslate2.converters.OpenNMTPyConverter(input_model).convert(output_dir, force=True, quantization=...)`.

A direct API equivalent when a task-local script is safer than a CLI shell command:

```python
import ctranslate2
converter = ctranslate2.converters.OpenNMTPyConverter("released.pt")
converter.convert("ct2_model_dir", force=True, quantization="int8_float16")
```

Post-checks:

- The CT2 output is a directory, not a `.pt` file.
- Typical CT2 files include `model.bin`, `config.json`, and `vocabulary.json`.
- CT2 inference configs should point `model` at the CT2 directory and, for tokenized LM examples, may also need `src_subword_vocab` to point at the generated `vocabulary.json`.
- Quantized CT2 output is for inference; do not feed it back into `onmt_train`.

## External and Hugging Face family conversion contracts

The source utilities convert external model weights into an OpenNMT-py checkpoint by creating OpenNMT-style `model`, `generator`, `vocab`, and `opt` sections. They are large, family-specific, optional-dependency-heavy utilities and are intentionally reference-only in this skill. When actual execution is needed, use these contracts to write or vendor a task-local reviewed converter instead of depending on a particular source checkout path.

| Family/contract | Required inputs | Output controls | Important facts |
| --- | --- | --- | --- |
| Generic Hugging Face causal LM (`convert_HF` contract) | `--model_dir` local directory or hub id; config, tokenizer, and weights; optional `--token` for gated hub access. | `--output`, `--format pytorch|safetensors`, `--nshards`. | Handles several HF architectures including Llama/Mistral/Mixtral/Phi-style mappings. Requires tokenizer/config consistency; may download missing hub files. AWQ quantization support is explicitly checked when quantization config is present. |
| LLaMA-like Hugging Face (`convert_HF_llamalike` contract) | Same as generic HF. | Same as generic HF. | Narrower LLaMA-like mapping; creates shared vocab and LM `opt` fields. |
| Original LLaMA (`convert_llama` contract) | `--model_dir` containing `params.json` and `consolidated.*.pth`; `--tokenizer_model`. | `--output`, `--format pytorch|safetensors`, `--nshards`. | Reads CPU tensors, concatenates model-parallel shards where needed, sets LLaMA-compatible LM options such as RMS norm, rotary settings, SwiGLU, and decoder start token. |
| T5 (`convert_T5` contract) | `--model_dir`; `--tokenizer_model`. | `--output`, `--format pytorch|safetensors`, `--nshards`. | Builds a seq2seq OpenNMT-py checkpoint. The converter rescales T5 query weights rather than changing OpenNMT-py multi-head attention. Multiple PyTorch shards are not supported; use safetensors for sharded output. |
| MPT/Falcon/RedPajama/XGen contracts | `--model_dir`; `--vocab_file` for the tokenizer/vocab source. | `--output`, `--format pytorch|safetensors`, `--nshards`. | Create LM checkpoints with architecture-specific layer norm, activation, multi-query, rotary/relative-position, and vocabulary settings. |
| OpenNMT-py v2 to v3 (`convertv2_v3` contract) | `-v2model`; `-v3model`. | Writes converted target checkpoint. | Legacy converter imports Python's removed `imp` module, so use a compatible Python version or patch the import path before relying on it. |

Validation after any external conversion:

```bash
python scripts/check_checkpoint_file.py converted.pt --json
```

Then check:

- `model_task` is correct: `lm` for decoder-only families, `seq2seq` for T5-style encoder-decoder conversion.
- `share_vocab`, `src_vocab_size`, `tgt_vocab_size`, and actual vocab lengths match the intended tokenizer.
- `generator.weight` shape agrees with the vocabulary size.
- For safetensors output, sidecar shards exist and the metadata `.pt` still carries `vocab` and `opt`.
- If the model will be released to CT2, run the PyTorch release step first when optimizer state is present.

## Extract vocabularies

The source vocabulary extraction utility reads `checkpoint["vocab"][side]` and writes one token per line. To avoid source checkout dependencies, use this task-local pattern after confirming `vocab` with the bundled checker:

```python
import torch

checkpoint = torch.load("model.pt", map_location="cpu", weights_only=False)
side = "src"  # or "tgt"
vocab = checkpoint["vocab"][side]
with open("vocab.txt", "w", encoding="utf-8") as out:
    for token in vocab:
        out.write(f"{token}\n")
```

Rules:

- Always choose `src` or `tgt` explicitly.
- For shared-vocabulary LM conversions, source and target sides may be identical.
- For CT2 output, inspect `vocabulary.json` in the CT2 directory instead of expecting a `.pt` checkpoint.

## Extract or convert embeddings

Two source utility contracts matter:

- **Extract checkpoint embeddings**: load a checkpoint, rebuild the OpenNMT-py model on CPU by applying defaults and validating model options, then write `src_embeddings.txt` and `tgt_embeddings.txt` text files with token plus vector columns.
- **Convert pretrained embeddings to tensors**: read a checkpoint vocabulary and GloVe/word2vec-style embedding files, filter to source/target vocab tokens, report match/missing percentages, and save `<output>.enc.pt` and `<output>.dec.pt` tensors.

Use these workflows only when the OpenNMT-py package and optional tokenizer dependencies import successfully. Preflight with the checkpoint checker and verify that the vocabulary lengths match the expected embedding rows. For large embedding files, stream the text file and avoid loading unrelated vectors when a vocabulary filter is available.

## Merge or concatenate LoRA weights

The LoRA utility contract has these options:

| Option | Meaning |
| --- | --- |
| `--action merge|concat` | `merge` is for inference release; `concat` preserves LoRA state for continued training. Default is `merge`. |
| `--base_model` | Compatible base OpenNMT-py checkpoint or safetensors-backed checkpoint prefix. |
| `--lora_weights` | LoRA checkpoint trained from the base model. |
| `--output` | Output checkpoint path or prefix. |
| `--format pytorch|safetensors` | Save a single PyTorch checkpoint or metadata plus safetensors shards. |

Behavior distilled from the implementation:

- Loads both checkpoints through OpenNMT-py checkpoint loading on CPU.
- Converts the LoRA checkpoint vocab dictionary into OpenNMT-py vocabs and rebuilds the base model from LoRA options.
- Clears quantized layer settings before merge and uses data-parallel mode for the rebuild.
- Loads base weights first, then LoRA weights.
- `merge`: switches the model to eval mode so LoRA weights merge into main weights, saves half precision, drops optimizer, filters LoRA-specific keys from PyTorch output, and keeps the base options.
- `concat`: saves half precision with LoRA state kept for continued training, restores the LoRA optimizer, and keeps the LoRA options.
- Safetensors output writes a metadata `.pt` file and shard sidecars derived from the base shard layout.

LoRA preflight checklist:

1. Inspect base and LoRA checkpoints; both should have compatible `vocab` and architecture options.
2. Confirm the LoRA checkpoint has LoRA option fields such as `lora_layers`, `lora_rank`, `lora_alpha`, or LoRA-named tensor keys.
3. Choose `merge` for inference/CT2 release; choose `concat` only if training will continue.
4. After output, run the checkpoint checker. For `merge`, no model keys should contain `lora`; for `concat`, LoRA keys may remain.
5. Release to PyTorch or CT2 only after the merged checkpoint has `model`, `generator`, `vocab`, and `opt` sections.

## Vicuna-style conversion chain

The Vicuna example demonstrates a full chain for an instruction-tuned LLaMA-family model:

1. Convert the base LLaMA-family checkpoint into OpenNMT-py format.
2. Extract or reuse the tokenizer vocabulary.
3. Fine-tune with LoRA and optional quantized layers.
4. Merge the LoRA checkpoint into the compatible base checkpoint for inference.
5. Release the merged checkpoint to CTranslate2 with an inference quantization such as `int8_float16`.
6. Run inference using a CT2 model directory and matching tokenizer/vocabulary files.

Use this as a workflow shape, not as a path template. Substitute project-local model, tokenizer, data, and output paths.

# Troubleshooting

## Missing dependency signals

| Symptom | Likely cause | Safe response |
| --- | --- | --- |
| `ModuleNotFoundError: torch` | No PyTorch in the runtime | Do not install an old stack blindly; confirm required CUDA/PyTorch version and whether CPU planning is enough. |
| `ModuleNotFoundError: scipy` during legacy BERT/model import | Legacy modeling imports optional scientific dependencies through old code paths | Treat model facts as source-inspected unless the environment is intentionally prepared. |
| `Please install apex` or `ModuleNotFoundError: apex` | `--fp16` or `--amp` selected without NVIDIA Apex | Remove mixed-precision flags for CPU/debug, or prepare the exact old Apex/Torch-compatible environment. |
| `ModuleNotFoundError: pyrouge` or Perl ROUGE errors | ROUGE-1.5.5/pyrouge not installed/configured | First validate prediction/gold files; use Python ROUGE mode when acceptable, or prepare ROUGE separately. |
| `LookupError: punkt` | NLTK sentence tokenizer data missing | Install/download NLTK punkt only after the user approves downloads. |
| `ModuleNotFoundError: lmdb` | `--lmdb_cache` selected without LMDB | Omit LMDB cache or install LMDB in a prepared environment. |

## Old Torch/Apex requirements

UniLMv1 examples were written for old PyTorch and Apex behavior. The documented Docker path used PyTorch 1.1 with CUDA 10.0 and a specific Apex commit; `s2s-ft` examples used PyTorch 1.2 with CUDA 10.0 and another Apex commit. Modern PyTorch/Apex combinations may fail at import, AMP initialization, distributed launch, or checkpoint loading.

Safe handling:

1. Build a command plan first.
2. Confirm whether the user needs an actual native run or only a command/template.
3. If running, isolate the environment and pin the legacy stack deliberately.
4. Remove `--fp16`, `--amp`, or `--fp16_opt_level` for CPU smoke tests or missing Apex.

## FP16 and AMP misuse

- In UniLMv1, `--fp16 --amp` uses old Apex AMP; `--fp16` without compatible Apex can also break optimizer paths.
- In `s2s-ft`, `--fp16` imports Apex AMP and uses `--fp16_opt_level`.
- Do not use FP16 on CPU-only runs.
- If loss scaling, CUDA kernels, or Apex extension imports fail, retry a minimal command without FP16 before changing data/model settings.

## Checkpoint/tokenizer/config mismatch

Common mismatch patterns:

| Symptom | Check |
| --- | --- |
| Many `[UNK]` tokens or poor output | Wrong vocab, missing `--do_lower_case`, or cased/uncased mismatch. |
| `KeyError` for `[S2S_SOS]`, `[S2S_CLS]`, or `[S2S_SEP]` | Vocab lacks UniLM seq2seq special tokens but a special-token mode was enabled. |
| Position embedding size error | `--max_seq_length` or `--max_position_embeddings` exceeds checkpoint/config capacity. |
| Token type embedding size mismatch logs | `--new_segment_ids` or S2S segment settings do not match checkpoint assumptions. |
| Missing or unexpected checkpoint keys | Wrong model family (`unilm` vs `bert` vs `minilm`), wrong config, or checkpoint is not in expected native format. |

Use `scripts/inspect_legacy_tokenizers.py --vocab-file VOCAB --show-remappings --sample "Example text"` to inspect a local vocab before changing model flags.

## Missing required paths

`s2s-ft` training requires `--train_file`, `--model_type`, `--model_name_or_path`, and `--output_dir`. Decoding requires `--model_type`, `--model_path`, `--tokenizer_name`, and `--input_file`.

UniLMv1 training requires a valid `--bert_model`, data directory, output directory, and usually `--model_recover_path`. The native script asserts that `--model_recover_path` exists when supplied. Decoding requires a checkpoint path and input file.

The bundled command planner rejects missing required arguments before printing a command.

## Distributed launch and GPU visibility

- `--nproc_per_node` should match the number of visible GPUs.
- `CUDA_VISIBLE_DEVICES=0,1,2,3` exposes four devices; `--nproc_per_node=8` with four visible devices will fail.
- Distributed launch initializes one process per local rank; file downloads/caches may be gated by rank in native code.
- If debugging, reduce to one GPU or CPU-style command before testing distributed launch.

## Sequence truncation and length errors

- `s2s-ft` training truncates source and target independently with `--max_source_seq_length` and `--max_target_seq_length`.
- `s2s-ft` decoding uses `--max_seq_length` as a total budget; the native decoder rejects `--max_tgt_length >= --max_seq_length - 2`.
- UniLMv1 uses total `--max_seq_length` plus legacy truncation controls such as `--max_len_a`, `--max_len_b`, `--trunc_seg`, and `--always_truncate_tail`.
- If outputs are empty or too short, check `--min_len`, `--max_tgt_length`, input truncation, and whether the source was accidentally tokenized twice.

## `tokenized_input` mistakes

Use tokenized input only when the files already contain tokens from the exact expected vocabulary. Common failures:

- raw text passed with `--tokenized_input`, causing punctuation/casing/token splitting to differ from training;
- token IDs passed instead of token strings;
- WordPiece tokens from a cased tokenizer used with an uncased checkpoint;
- JSON token lists mixed with text strings across examples;
- legacy UniLMv1 `train.src`/`train.tgt` line counts not aligned.

For `s2s-ft`, JSON list values trigger tokenized mode; raw strings trigger tokenizer mode. For UniLMv1, `--tokenized_input` switches from BERT tokenization to whitespace tokenization.

## ROUGE and evaluation failures

Before blaming ROUGE, check:

```bash
wc -l predictions.txt references.target
head -n 2 predictions.txt
head -n 2 references.target
```

Then check task-specific details:

- XSum/Gigaword usually need one-line summaries/headlines and no CNN/DM truncation.
- CNN/DM evaluation often uses `--trunc_len 160` in `s2s-ft`; older UniLMv1 examples may use different truncation.
- Perl ROUGE and pyrouge require external configuration and can fail even when prediction files are valid.
- QG evaluation in the legacy tree depended on older Python-2-era scripts and cased-vs-uncased reference handling.

## When to route elsewhere

- E5 or SimLM dense retrieval, embedding indexes, reranking, and retrieval metrics belong to `embeddings-retrieval`.
- OCR, form understanding, document image models, and LayoutLM/LayoutReader image-layout tasks belong to `vision-document-ai`.
- Kosmos, TextDiffuser, audio, LatentLM, and multimodal generation belong to `multimodal-generation`.
- Distributed pretraining architecture research, PFPO, and ReSA details belong to `architectures-training`.

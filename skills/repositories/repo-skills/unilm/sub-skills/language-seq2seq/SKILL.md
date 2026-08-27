---
name: language-seq2seq
description: "Plan and troubleshoot UniLM language sequence-to-sequence
  fine-tuning, decoding, evaluation, and related language adaptation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# language-seq2seq

Use this sub-skill when a task asks for UniLM, UniLMv1, `s2s-ft`, MiniLM NLG, AdaLM, DeltaLM, InfoXLM, EdgeLM, LayoutReader, XTune, or legacy language sequence-to-sequence command construction and diagnosis.

## What this covers

- Build safe command plans for summarization, question generation, JSONL seq2seq training, decoding, and ROUGE evaluation.
- Choose between legacy UniLMv1 scripts, newer `s2s-ft` scripts, MiniLM NLG paths, multilingual/domain-adaptation language components, and fairseq-style generation stacks.
- Validate `src`/`tgt` JSONL, tokenized list inputs, parallel `train.src`/`train.tgt` files, vocabulary/config/checkpoint expectations, and prediction/evaluation files.
- Diagnose old Torch/Apex/ROUGE/tokenizer/checkpoint failures without downloading model weights or starting heavy jobs.

## First routing choice

- Use `s2s-ft` command patterns for modern UniLM/MiniLM/Roberta/XLM-R/Electra seq2seq JSONL workflows.
- Use UniLMv1 command patterns only when the request explicitly targets `biunilm/run_seq2seq.py`, `biunilm/decode_seq2seq.py`, legacy BERT vocab/config/checkpoints, or old `train.src`/`train.tgt` data.
- Use AdaLM notes for biomedical/computer-science domain-adapted BERT-style fine-tuning, not generic seq2seq generation.
- Use DeltaLM or EdgeLM notes for fairseq encoder-decoder translation/generation workflows.
- Route dense retrieval, OCR/form/image, multimodal generation, and architecture/distributed-research questions to sibling skills instead of this one.

## Bundled references and scripts

- Read [references/workflows.md](references/workflows.md) to choose the correct UniLM-family language workflow and safety posture.
- Read [references/api-and-cli.md](references/api-and-cli.md) for supported scripts, flags, model choices, and evaluation commands.
- Read [references/data-formats.md](references/data-formats.md) before preparing JSONL, tokenized inputs, legacy parallel files, predictions, or ROUGE files.
- Read [references/troubleshooting.md](references/troubleshooting.md) when dependencies, checkpoints, tokenizers, CUDA/Apex, distributed launch, or ROUGE evaluation fail.
- Run [scripts/build_seq2seq_command.py](scripts/build_seq2seq_command.py) to validate required planning arguments and print safe `s2s-ft` train/decode/eval command templates without executing them.
- Run [scripts/inspect_legacy_tokenizers.py](scripts/inspect_legacy_tokenizers.py) to inspect a local BERT/UniLM vocabulary and special-token compatibility without downloading models.

## Safety rules

- Do not run training, decoding, distributed launch, downloads, ROUGE Perl, or GPU-only examples unless the user explicitly asks and the runtime is prepared.
- Treat UniLMv1 full scripts as reference-only unless an old PyTorch 1.1-style environment, matching Apex build, checkpoint, config, and vocab are confirmed.
- Prefer command planning and file validation first; then ask before executing any heavy or credentialed workflow.

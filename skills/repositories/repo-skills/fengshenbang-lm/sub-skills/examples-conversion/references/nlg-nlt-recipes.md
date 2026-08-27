# NLG and NLT recipes

This reference covers Fengshen example families for summarization, question generation, generative QA, translation, medical close-book QA, and causal reasoning. It records data shapes, model choices, and resource gates without reproducing source training scripts.

## Decision table

| User task | Recommended family | Typical model/source | Data shape | Main gates |
|---|---|---|---|---|
| Chinese text summarization | Randeng T5/BART/PEGASUS summary examples | Randeng T5 70M/784M, Randeng PEGASUS 523M, BART-style seq2seq | LCSTS-style records with source text and summary; prompt often `summary:`; max source about 128 and target about 64 in example scripts | `transformers`, `torch`, Lightning, ROUGE metric dependencies, model download/cache, GPU for realistic fine-tune. |
| Question generation | Randeng-BART QG | `IDEA-CCNL/Randeng-BART-139M-QG-Chinese` | Context string with answer marked by `<ans>`; generated target is a question | Add `<ans>` special token; GPU optional for inference but needed for practical training; training writes checkpoints. |
| Generative reading comprehension QA | Randeng T5 QA | `IDEA-CCNL/Randeng-T5-784M-QA-Chinese` | `question:<question>knowledge:<context>answer<extra_id_0>`-style T5 input; answer target | Long contexts require careful max lengths; Deepspeed/DDP optional; CMRC/ChineseSQuAD-style data. |
| Translation | Randeng DeltaLM | `IDEA-CCNL/Randeng-Deltalm-362M-En-Zn` or `IDEA-CCNL/Randeng-Deltalm-362M-Zh-En` | JSONL lines such as `{"src": "...", "tgt": "..."}` after external preprocessing | Source/target preprocessing is mostly external; compatible older stack noted by examples; label smoothing defaults matter. |
| Medical close-book QA | Wenzhong/Yuyuan GPT2 | Yuyuan medical GPT2-style checkpoints | Lines shaped like question/answer pairs; inference prompt `Question:{question} answer:` | Very large model; example fine-tune used multi-GPU/Deepspeed; demo code may call service endpoints. |
| Causal reasoning generation | Randeng Transformer-XL reasoning | `Randeng-TransformerXL-5B-Deduction-Chinese`, `Randeng-TransformerXL-5B-Abduction-Chinese` | Input sentence(s), output generated causes/effects | 5B model size; model download/cache and GPU memory are likely needed. |

## Summary recipe

Use when the user asks to adapt the summary examples rather than the generic pipeline CLI.

### Planning steps

1. Confirm whether the goal is **inference**, **fine-tuning**, or **data-format migration**.
2. Confirm a local/cached seq2seq model or an allowed model ID download.
3. Confirm data fields. The example family assumes source text plus target summary and commonly uses LCSTS naming.
4. Choose prompt style. T5 examples use a textual prompt such as `summary:`; BART/PEGASUS examples may use an empty or quote-like prompt.
5. Keep Trainer, optimizer, scheduler, and checkpoint mechanics in `../data-training/SKILL.md`.

### Minimal data schema

```jsonl
{"text": "source article text", "summary": "target summary"}
{"text": "第二条原文", "summary": "第二条摘要"}
```

Exact dataloader field names can vary by the selected Fengshen data module. Before execution, map user fields to the expected source text and summary fields and run a tiny schema check outside any training loop.

### Important example-derived defaults

- Common max source/target lengths in summary scripts are around `max_enc_length=128` and `max_dec_length=64` for LCSTS-style data.
- Large Randeng summary examples used Deepspeed stage 1 or DDP and FP16; these are not required for static planning but are realistic for training.
- Summary validation computes ROUGE on Chinese text after character tokenization; make sure metric package versions match the training stack.

## Question generation recipe

Use when the user wants a model to generate questions from a passage and an answer.

### Inference prompt shape

The QG example marks the answer span using `<ans>` inside the context. A sanitized pattern is:

```text
知识：<context with <ans> marking the answer span> 回答：<answer>
```

Then use a BART conditional generation model/tokenizer that includes `<ans>` as an additional special token. Do not run this automatically because `from_pretrained` may download model weights.

### Training data expectations

- Training/dev/test files are JSON-like records consumed by the QG script and utility code.
- Max lengths in the example family separate source/context/answer and target question lengths.
- Deepspeed config and checkpoint paths in the source examples are local-workflow choices; replace them with user-approved output directories.

## Generative QA recipe

Use when the user asks for T5-style answer generation from a passage and question.

### Prompt shape

A representative T5 input is:

```text
question:<question>knowledge:<context>answer<extra_id_0></s>
```

The target is the generated answer. For inference, cap input length and target length explicitly. For training, route data module and checkpoint details to `../data-training/SKILL.md`.

### Resource notes

- The 784M QA model is much smaller than Ziya/Taiyi but still benefits from CUDA for practical inference/training.
- Example training uses Lightning, optional Deepspeed stage 1, FP16, and accumulated gradients.
- If Deepspeed is unavailable, switch to DDP or single-device planning only after verifying dependencies.

## Translation / DeltaLM recipe

Use when the user asks for machine translation examples or DeltaLM fine-tuning.

### Data preparation

The source examples expect external preprocessing first, then a merge step into JSONL:

```jsonl
{"src": "und was menschliche gesundheit ist ...", "tgt": "and it can be ..."}
{"src": "source sentence", "tgt": "target sentence"}
```

The repository provided a simple source/target merger, not a full tokenization/cleaning pipeline. If the user expects production translation preprocessing, ask for language pair, tokenization rules, filtering, train/dev/test split, and whether external tools are permitted.

### Model/runtime notes

- DeltaLM model IDs include English-to-Chinese and Chinese-to-English variants. Confirm direction before selecting `--reverse_src_tgt` or `--tgt_zh`-style flags.
- The example notes an older compatible stack around Python 3.8, PyTorch 1.10, Transformers 4.20, and PyTorch Lightning 1.6. Treat newer stacks as unverified until import-tested.
- Label smoothing is meaningful; the example script uses a non-zero label smoothing default.

## Medical close-book QA recipe

Use when the user asks about the Wenzhong/Yuyuan medical QA examples.

### Prompt/data shape

- Fine-tuning data is question/answer pairs, often shown as text lines shaped like `{'question':'...', 'answer':'...'}`.
- Inference prompt shape is:

```text
Question:<user medical question> answer:
```

The model continues the prompt to generate the answer.

### Safety notes

- The model family is domain-specific and may generate unsupported medical text. Do not present outputs as medical advice.
- Example fine-tuning used large GPT2-style checkpoints with Deepspeed and multi-GPU settings. Treat it as heavy optional training.
- FastDemo examples may call backend HTTP services; do not reuse service endpoints. See [troubleshooting.md](troubleshooting.md).

## Causal reasoning recipe

Use when the user asks for deduction/abduction examples.

- Deduction generates possible consequences from an input cause or statement.
- Abduction generates possible causes/explanations for an input statement.
- The example family loads Transformer-XL reasoning models and custom generation helpers; this is model-download and memory dependent.
- If the user asks for a lightweight plan, describe prompt shape and model IDs only. If execution is requested, require cache status, device, RAM/VRAM, and output handling.

## Static requirement checks

```bash
python ../scripts/check_recipe_requirements.py --recipe nlg-summary --device cuda --gpus 1 --vram-gb 24
python ../scripts/check_recipe_requirements.py --recipe qa-t5 --device cpu --precision fp32
python ../scripts/check_recipe_requirements.py --recipe translation-deltalm --device cuda --gpus 1 --vram-gb 16
python ../scripts/check_recipe_requirements.py --recipe wenzhong-qa --device cuda --gpus 16 --vram-gb 40
```

## Common failure modes

| Symptom | Likely cause | Safe response |
|---|---|---|
| Import errors in `torchmetrics`, Lightning, or Transformers | Example stack is older than the current environment | Use an isolated compatible env; inspect versions before running. |
| Training script references unavailable paths | Source shell script had local workspace paths | Replace all data/model/output paths with user-provided paths; never copy source paths. |
| Model load unexpectedly downloads | Model ID passed to `from_pretrained` without local cache | Ask whether downloads are allowed or require a local model path. |
| Deepspeed strategy fails | Missing Deepspeed, incompatible CUDA/toolchain, or CPU-only host | Switch to help/static planning, or prepare a CUDA-specific env before execution. |
| Output/checkpoint collision | Reusing an existing checkpoint/output directory | Require a fresh output directory or explicit overwrite/backup approval. |

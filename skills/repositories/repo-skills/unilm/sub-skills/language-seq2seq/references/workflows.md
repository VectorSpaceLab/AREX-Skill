# Language Seq2Seq Workflows

## Select the implementation family

| Request signal | Use | Why |
| --- | --- | --- |
| `s2s-ft`, JSON lines with `src`/`tgt`, XSum, CNN/DM, UniLM 1.2/2, MiniLM NLG | `s2s-ft` train/decode/eval patterns | Newer runner supports model types `bert`, `minilm`, `roberta`, `xlm-roberta`, `unilm`, and `electra`; JSONL input can be raw text or token lists. |
| `biunilm`, UniLMv1, `train.src`/`train.tgt`, `bert-large-cased`, `model_recover_path` | UniLMv1 reference patterns | Legacy runner is tied to old `pytorch_pretrained_bert`, PyTorch 1.1-era mixed precision, and BERT-format vocab/config/checkpoints. |
| MiniLM NLG | `s2s-ft` with `model_type minilm` or `bert` depending on checkpoint layout | MiniLM NLG reuses UniLM-style self-attention masks through `s2s-ft`; use MiniLM vocab/config paths when local checkpoint files are supplied. |
| AdaLM biomedical/computer-science adaptation | AdaLM fine-tuning notes | AdaLM is domain/task adaptation for BERT-like classification/NER/PICO, not a generic seq2seq decoder. |
| DeltaLM translation or multilingual text-to-text | Fairseq DeltaLM workflow | DeltaLM uses SentencePiece, fairseq preprocessing, `train.py`, and `generate.py`, not `s2s-ft` JSONL. |
| InfoXLM/XLM-Align cross-lingual pretraining or XLM-R replacement | InfoXLM or XTune workflow | InfoXLM uses XLM-R-compatible tokenizers and fairseq mmap data for MLM/TLM/XlCo; XTune fine-tunes XTREME tasks. |
| EdgeLM/EdgeFormer on-device seq2seq | Fairseq EdgeFormer workflow | EdgeLM uses fairseq `fairseq-train`/`fairseq-generate` with compact encoder-decoder architecture. |
| LayoutReader reading order | Route to vision/document workflow | It is text-plus-layout OCR reading-order prediction and requires LayoutLM-style document data. |

## Safe `s2s-ft` planning loop

1. Confirm task: `xsum`, `cnndm`, `gigaword`, or `custom-json`.
2. Confirm data: one UTF-8 JSON object per line with `src` and `tgt` for training, and at least `src` for decoding.
3. Confirm model family: `unilm`, `minilm`, `bert`, `roberta`, `xlm-roberta`, or `electra`.
4. Confirm casing: include `--do_lower_case` for uncased checkpoints/tokenizers; omit it for cased checkpoints.
5. Use the bundled command planner before any native run:

```bash
python scripts/build_seq2seq_command.py \
  --task xsum --mode all \
  --train-file data/train.json --input-file data/validation.json --gold-file data/validation.target \
  --output-dir runs/xsum --model-path runs/xsum/ckpt-32000 \
  --model-type unilm --model-name-or-path unilm1.2-base-uncased \
  --tokenizer-name unilm1.2-base-uncased --cache-dir cache \
  --gpus 0,1,2,3 --nproc-per-node 4 --do-lower-case --fp16
```

The planner prints commands only. Review the printed commands, runtime environment, GPU visibility, data paths, and model/checkpoint availability before running them manually.

## `s2s-ft` command shape

Training uses `run_seq2seq.py` with `--train_file`, `--output_dir`, `--model_type`, `--model_name_or_path`, source/target maximum lengths, batch size, gradient accumulation, learning rate, warmup, and total training steps. Multi-GPU examples use `python -m torch.distributed.launch --nproc_per_node=N run_seq2seq.py ...`.

Decoding uses `decode_seq2seq.py` with `--model_type`, `--tokenizer_name`, `--input_file`, `--split`, `--model_path`, `--max_seq_length`, `--max_tgt_length`, `--batch_size`, `--beam_size`, `--length_penalty`, and `--mode s2s`. A checkpoint directory is expected, and default output is usually derived from the model path plus split unless `--output_file` is provided.

Evaluation uses one of the task-specific scripts:

- `evaluations/eval_for_xsum.py --pred PRED --gold GOLD --split SPLIT`
- `evaluations/eval_for_cnndm.py --pred PRED --gold GOLD --split SPLIT --trunc_len 160`
- `evaluations/eval_for_gigaword.py --pred PRED --gold GOLD --split SPLIT`

## UniLMv1 reference-only workflow

Use UniLMv1 only when the user has a legacy-compatible environment and explicitly targets the older code path. Typical legacy training requires:

```bash
python biunilm/run_seq2seq.py --do_train --num_workers 0 \
  --bert_model bert-large-cased --new_segment_ids --tokenized_input \
  --data_dir DATA_DIR --src_file train.src --tgt_file train.tgt \
  --output_dir OUTPUT_DIR/bert_save --log_dir OUTPUT_DIR/bert_log \
  --model_recover_path PRETRAINED_OR_RECOVERED_MODEL.bin \
  --max_seq_length 192 --max_position_embeddings 192 \
  --trunc_seg a --always_truncate_tail --max_len_b 64 \
  --mask_prob 0.7 --max_pred 64 \
  --train_batch_size 128 --gradient_accumulation_steps 1 \
  --learning_rate 0.00001 --warmup_proportion 0.1 --label_smoothing 0.1 \
  --num_train_epochs 30
```

Legacy decoding usually requires:

```bash
python biunilm/decode_seq2seq.py \
  --bert_model bert-large-cased --new_segment_ids --mode s2s --need_score_traces \
  --input_file DATA_DIR/test.src --split test --tokenized_input \
  --model_recover_path FINETUNED_MODEL.bin \
  --max_seq_length 192 --max_tgt_length 32 \
  --batch_size 64 --beam_size 5 --length_penalty 0 \
  --forbid_duplicate_ngrams --forbid_ignore_word "."
```

Do not execute these templates blindly. They require old Torch/Apex-compatible installations, matching BERT vocab/config/checkpoints, and task-specific data.

## Task presets

| Task | Typical source/target lengths | Decode target | Notes |
| --- | --- | --- | --- |
| XSum | `464`/`48` in early `s2s-ft`; later UniLM2 examples use longer source up to `720` | `48` | Use uncased flag with uncased UniLM/MiniLM models; target mask probability around `0.4`-`0.5` is common for UniLM2-style examples. |
| CNN/DailyMail | `608`/`160` in `s2s-ft`; UniLMv1 legacy examples use total length `768` | `128`-`160` | Use `--trunc_len 160` for `s2s-ft` CNN/DM evaluation; legacy ROUGE examples may use `--trunc_len 70`. |
| Gigaword | Legacy UniLMv1 uses total length `192`, target up to `32` or `64` | `32` | Legacy data is often tokenized and digit-normalized; direct checkpoint reuse may require matching preprocessing. |
| SQuAD question generation | Legacy UniLMv1 uses total length `512`, target `48` | `48` | Legacy evaluation depends on Python-2-era QG scripts; lowercase predictions when comparing to uncased references if required by the chosen benchmark. |
| Custom JSON | Choose lengths from data histograms | Choose based on desired max output | Validate JSONL shape first; use a task-specific evaluator or a simple line-count/content check if no metric script exists. |

## Domain and multilingual routing notes

- AdaLM checkpoints are domain-specific BERT-style models for biomedical and computer-science tasks. Confirm `config`, `vocab`, checkpoint, task labels, cache paths, and `--do_lower_case` before classification/NER/PICO fine-tuning.
- DeltaLM supports multilingual generation and translation with SentencePiece plus fairseq binary data. Confirm `spm.model`, `dict.txt`, source/target language files, and fairseq install before planning.
- InfoXLM/XLM-Align uses XLM-R-compatible vocabulary and Hugging Face model names for downstream fine-tuning; pretraining uses fairseq mmap data and old Apex/fairseq stacks.
- XTune is for consistency-regularized cross-lingual fine-tuning on XTREME tasks, not seq2seq decoding.
- EdgeLM/EdgeFormer targets compact on-device English seq2seq generation with fairseq; confirm task, binarized data, checkpoint, and `fairseq-generate` settings.

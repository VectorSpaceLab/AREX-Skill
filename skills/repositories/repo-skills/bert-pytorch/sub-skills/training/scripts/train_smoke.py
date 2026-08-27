#!/usr/bin/env python3
"""Train BERT-pytorch on a tiny corpus with an explicit CPU or CUDA device choice."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Dataset

from bert_pytorch import BERT
from bert_pytorch.dataset import WordVocab
from bert_pytorch.trainer import BERTTrainer

SKILL_ROOT = Path(__file__).resolve().parents[3]
TINY_CORPUS_HELPER = SKILL_ROOT / "scripts" / "make_tiny_corpus.py"


def make_corpus(path: Path) -> Path:
    subprocess.run([sys.executable, str(TINY_CORPUS_HELPER), "--output", str(path), "--overwrite"], check=True)
    return path


class SmokeDataset(Dataset):
    """Deterministic dataset wrapper that guarantees masked tokens per sample."""

    def __init__(self, corpus_path: Path, vocab: WordVocab, seq_len: int):
        self.vocab = vocab
        self.seq_len = seq_len
        with corpus_path.open("r", encoding="utf-8") as handle:
            self.lines = [line.rstrip("\n").split("\t") for line in handle if line.strip()]
        if not self.lines:
            raise SystemExit(f"empty corpus: {corpus_path}")

    def __len__(self) -> int:
        return len(self.lines)

    def _encode(self, sentence: str) -> list[int]:
        return [self.vocab.stoi.get(token, self.vocab.unk_index) for token in sentence.split()]

    def _mask_first_token(self, tokens: list[int]) -> tuple[list[int], list[int]]:
        input_ids: list[int] = []
        label_ids: list[int] = []
        for index, token_id in enumerate(tokens):
            if index == 0:
                input_ids.append(self.vocab.mask_index)
                label_ids.append(token_id)
            else:
                input_ids.append(token_id)
                label_ids.append(0)
        return input_ids, label_ids

    def __getitem__(self, index: int):
        t1, t2 = self.lines[index]
        is_next = 1
        if index % 2 == 1 and len(self.lines) > 1:
            t2 = self.lines[(index + 1) % len(self.lines)][1]
            is_next = 0

        t1_input, t1_label = self._mask_first_token(self._encode(t1))
        t2_input, t2_label = self._mask_first_token(self._encode(t2))

        t1_input = [self.vocab.sos_index] + t1_input + [self.vocab.eos_index]
        t1_label = [0] + t1_label + [0]
        t2_input = t2_input + [self.vocab.eos_index]
        t2_label = t2_label + [0]

        segment_label = ([1] * len(t1_input) + [2] * len(t2_input))[: self.seq_len]
        bert_input = (t1_input + t2_input)[: self.seq_len]
        bert_label = (t1_label + t2_label)[: self.seq_len]

        pad_len = self.seq_len - len(bert_input)
        if pad_len > 0:
            padding = [self.vocab.pad_index for _ in range(pad_len)]
            bert_input.extend(padding)
            bert_label.extend(padding)
            segment_label.extend(padding)

        output = {
            "bert_input": bert_input,
            "bert_label": bert_label,
            "segment_label": segment_label,
            "is_next": is_next,
        }
        return {key: torch.tensor(value) for key, value in output.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny BERT-pytorch training smoke on CPU or CUDA.")
    parser.add_argument("--workdir", type=Path, default=None, help="Directory for generated smoke files.")
    parser.add_argument("--corpus", type=Path, default=None, help="Use an existing corpus instead of generating one.")
    parser.add_argument("--output-prefix", type=Path, default=None, help="Checkpoint prefix; defaults inside workdir.")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="Explicit target device.")
    parser.add_argument("--epochs", type=int, default=1, help="Epoch count for the smoke run.")
    parser.add_argument("--batch-size", type=int, default=2, help="Batch size for the smoke run.")
    parser.add_argument("--seq-len", type=int, default=8, help="Maximum sequence length.")
    parser.add_argument("--hidden", type=int, default=32, help="Hidden size for the tiny model.")
    parser.add_argument("--layers", type=int, default=2, help="Transformer layer count.")
    parser.add_argument("--attn-heads", type=int, default=4, help="Attention head count.")
    parser.add_argument("--num-workers", type=int, default=0, help="DataLoader worker count.")
    parser.add_argument("--lr", type=float, default=1e-3, help="Adam learning rate for the smoke run.")
    parser.add_argument("--log-freq", type=int, default=1, help="Iteration logging frequency.")
    parser.add_argument("--cuda-devices", type=int, nargs="*", default=None, help="Optional CUDA device ids for DataParallel.")
    args = parser.parse_args()

    if args.hidden % args.attn_heads != 0:
        raise SystemExit(f"hidden must be divisible by attn_heads: hidden={args.hidden}, attn_heads={args.attn_heads}")

    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA was requested but torch.cuda.is_available() is false in this environment")

    workdir = args.workdir or Path(tempfile.mkdtemp(prefix="bert-pytorch-train-smoke-"))
    workdir.mkdir(parents=True, exist_ok=True)

    corpus_path = args.corpus or workdir / "tiny_corpus.txt"
    if args.corpus is None:
        make_corpus(corpus_path)
        repeated_corpus = workdir / "train_corpus.txt"
        repeated_corpus.write_text(corpus_path.read_text(encoding="utf-8") * 20, encoding="utf-8")
        corpus_path = repeated_corpus
    elif not corpus_path.exists():
        raise SystemExit(f"corpus does not exist: {corpus_path}")

    torch.manual_seed(0)

    with corpus_path.open("r", encoding="utf-8") as handle:
        vocab = WordVocab(handle)

    vocab_path = workdir / "tiny_vocab.pkl"
    vocab.save_vocab(str(vocab_path))
    vocab = WordVocab.load_vocab(str(vocab_path))

    dataset = SmokeDataset(corpus_path, vocab, seq_len=args.seq_len)
    data_loader = DataLoader(dataset, batch_size=args.batch_size, num_workers=args.num_workers)

    bert = BERT(len(vocab), hidden=args.hidden, n_layers=args.layers, attn_heads=args.attn_heads)
    trainer = BERTTrainer(
        bert,
        len(vocab),
        train_dataloader=data_loader,
        lr=args.lr,
        with_cuda=(args.device == "cuda"),
        cuda_devices=args.cuda_devices,
        log_freq=args.log_freq,
    )

    output_prefix = args.output_prefix or workdir / "bert_smoke.model"
    output_prefix.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(args.epochs):
        trainer.train(epoch)
        checkpoint = trainer.save(epoch, str(output_prefix))
        print(f"checkpoint={checkpoint}")

    print(f"device={trainer.device}")
    print(f"corpus={corpus_path}")
    print(f"vocab={vocab_path}")
    print(f"workdir={workdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""No-download smoke checks for HanLP rule and string utilities."""
from __future__ import annotations
import argparse
from hanlp.utils.rules import split_sentence
from hanlp.utils.string_util import possible_tokenization, split_long_sentence_into

def main():
    ap = argparse.ArgumentParser(description="Run HanLP rule/string utility smoke checks.")
    ap.add_argument("--text", default="他说：“加油。”谢谢")
    a = ap.parse_args()
    assert list(split_sentence("叶")) == ["叶"]
    toks = possible_tokenization("商品和服务")
    assert len(set(toks)) == 2 ** (len("商品和服务") - 1)
    assert list(split_long_sentence_into(list("甲乙，丙丁。"), max_seq_length=4, hard_constraint=True))
    print("rules smoke passed")
    print(list(split_sentence(a.text)))
    return 0
if __name__ == "__main__": raise SystemExit(main())

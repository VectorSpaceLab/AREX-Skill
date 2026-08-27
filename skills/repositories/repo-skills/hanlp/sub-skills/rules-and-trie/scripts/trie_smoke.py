#!/usr/bin/env python3
"""No-download smoke checks for HanLP Trie and TrieDict behavior."""
from __future__ import annotations
import argparse
from hanlp_trie import Trie, TrieDict

def main():
    ap = argparse.ArgumentParser(description="Run HanLP trie smoke checks.")
    ap.add_argument("--text", default="商品和服务")
    a = ap.parse_args()
    trie = Trie({'商品':'goods','和':'and','和服':'kimono','服务':'service','务':'business'})
    assert trie.parse(a.text) and trie.parse_longest(a.text)
    d = TrieDict({'重要':'important'})
    data = ['第一个词语很重要，第二个词语也很重要']
    nd, belongs, parts = d.split_batch(data)
    merged = d.merge_batch(data, [list(x) for x in nd], belongs, parts)
    assert merged[0].count('important') == 2
    print("trie smoke passed")
    print(trie.parse(a.text)); print(trie.parse_longest(a.text)); print(merged)
    return 0
if __name__ == "__main__": raise SystemExit(main())

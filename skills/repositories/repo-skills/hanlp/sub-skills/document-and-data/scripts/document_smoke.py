#!/usr/bin/env python3
"""Tiny HanLP Document smoke test for JSON, prefix, CoNLL, and pretty APIs."""
from __future__ import annotations
import argparse
from hanlp_common.document import Document

def main():
    ap = argparse.ArgumentParser(description="Run a tiny HanLP Document smoke test.")
    ap.add_argument("--pretty", action="store_true")
    a = ap.parse_args()
    doc = Document(tok=[["晓美焰", "来到", "北京", "。"]], pos=[["NR", "VV", "NR", "PU"]], ner=[[["北京", "LOCATION", 2, 3]]], dep=[[[2,"nsubj"],[0,"root"],[2,"dobj"],[2,"punct"]]])
    assert doc.count_sentences() == 1 and doc.get_by_prefix("tok")
    assert doc.to_conll()
    print(doc.to_json())
    if a.pretty: print("\n\n".join(doc.to_pretty()))
    print("document smoke passed")
    return 0
if __name__ == "__main__": raise SystemExit(main())

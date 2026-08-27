#!/usr/bin/env python3
"""Smoke check for JioNLP dictionaries and language-analysis helpers."""

from __future__ import annotations

import tempfile
from pathlib import Path

import jionlp as jio


class EchoApi:
    def __call__(self, text, from_lang=None, to_lang=None):
        return f"{text}:{from_lang}->{to_lang}"


def main() -> int:
    assert isinstance(jio.stopwords_loader(), list)
    assert isinstance(jio.china_location_loader(), dict)
    assert len(jio.llm_test_dataset_loader(version="1.1")) >= 1

    keyphrases = jio.keyphrase.extract_keyphrase("朝鲜确认金正恩出访俄罗斯 将与普京举行会谈")
    assert isinstance(keyphrases, list) and keyphrases

    summary = jio.summary.extract_summary("不交五险一金，老了会怎样？众所周知，五险一金非常重要。")
    assert isinstance(summary, str) and summary

    sentiment = jio.sentiment.LexiconSentiment()("14岁女孩坠亡生前遭强奸致孕。")
    assert 0.0 <= sentiment <= 1.0

    freq = jio.text_classification.analyse_freq_words(
        [["糟糕", "没有"], ["糟糕", "差"], ["不错"]],
        ["负", "负", "正"],
        min_word_freq=1,
        min_word_threshold=0.5,
    )
    assert "负" in freq and "糟糕" in freq["负"]

    with tempfile.TemporaryDirectory() as tmpdir:
        corpus = Path(tmpdir) / "corpus.txt"
        corpus.write_text(
            "浑水创始人：七月开始调查贝壳，因为好得难以置信\n"
            "做空机构浑水在社交媒体上公开表示，正在做空美股上市公司贝壳...\n",
            encoding="utf-8",
        )
        discovery = jio.new_word.new_word_discovery(str(corpus), min_freq=1, min_mutual_information=1, min_entropy=0)
    assert isinstance(discovery, dict)

    encoded = jio.bpe.byte_level_bpe.encode("你好，JioNLP")
    assert jio.bpe.byte_level_bpe.decode(encoded) == "你好，JioNLP"

    mellm = jio.mellm.MELLM(["demo"], [EchoApi()], [{"score": 1, "question": "示例问题"}])
    assert mellm.llm_num == 1 and mellm.question_num == 1

    print("language tools smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

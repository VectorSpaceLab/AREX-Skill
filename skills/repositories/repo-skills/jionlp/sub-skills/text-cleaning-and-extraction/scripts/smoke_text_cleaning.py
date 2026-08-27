#!/usr/bin/env python3
"""Smoke check for JioNLP text cleaning and extraction helpers."""

from __future__ import annotations

import tempfile
from pathlib import Path

import jionlp as jio


def main() -> int:
    assert jio.remove_url("see https://example.com now") == "see  now"
    assert jio.replace_url("see https://example.com now") == "see <url> now"
    assert jio.check_any_chinese_char("abc中文") is True
    assert jio.check_all_arabic_num("20221128") is True
    assert jio.extract_parentheses("A（B）C【D】") == ["（B）", "【D】"]
    assert jio.split_sentence("中华古汉语，泱泱大国，历史传承的瑰宝。", criterion="fine") == [
        "中华古汉语，",
        "泱泱大国，",
        "历史传承的瑰宝。",
    ]

    html = '<html><head><meta name="description" content="hello"></head><body><p>你好 &amp; world</p></body></html>'
    cleaned, meta = jio.clean_html(html)
    assert "你好 & world" in cleaned
    assert meta == {}

    assert jio.remove_stopwords(["我", "在", "北京", "工作", "了"], remove_location=True, save_negative_words=True) == [
        "我",
        "工作",
    ]

    sample = "联系我：a@example.com，电话：13288568202。"
    assert jio.extract_email(sample, detail=True)[0]["domain_name"] == "example"
    assert jio.extract_phone_number(sample, detail=True)[0]["type"] == "cell_phone"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir) / "sample.jsonl"
        payload = ["alpha", {"x": 1}]
        jio.write_file_by_line(payload, tmp)
        assert jio.read_file_by_line(tmp) == ["alpha", {"x": 1}]

    print("text cleaning smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

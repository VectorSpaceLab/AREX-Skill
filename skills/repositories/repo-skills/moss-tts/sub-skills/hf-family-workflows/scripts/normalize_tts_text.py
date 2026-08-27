#!/usr/bin/env python3
"""Stdlib-only robust text normalizer for MOSS-TTS prompts.

This helper performs non-semantic cleanup for text-to-speech robustness. It does
not expand numbers, dates, currencies, units, Pinyin, or IPA. It preserves square
and curly bracket controls such as [S1], [pause 3.2s], and {whisper}.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

# Scripts that do not rely on spaces for word boundaries: Han + Japanese kana.
_CJK_CHARS = r"\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff"
_CJK = f"[{_CJK_CHARS}]"
_PROT = r"___PROT\d+___"

_URL_RE = re.compile(r"https?://[^\s\u3000，。！？；、）】》〉」』]+")
_EMAIL_RE = re.compile(r"(?<![\w.+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w.-])")
_MENTION_RE = re.compile(r"(?<![A-Za-z0-9_])@[A-Za-z0-9_]{1,32}")
_REDDIT_RE = re.compile(r"(?<![A-Za-z0-9_])(?:u|r)/[A-Za-z0-9_]+")
_HASHTAG_RE = re.compile(r"(?<![A-Za-z0-9_])#(?!\s)[^\s#]+")
_DOT_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_])\.(?=[A-Za-z0-9._-]*[A-Za-z0-9])[A-Za-z0-9._-]+")
_FILELIKE_RE = re.compile(
    r"(?<![A-Za-z0-9_])"
    r"(?=[A-Za-z0-9._/+:-]*[A-Za-z])"
    r"(?=[A-Za-z0-9._/+:-]*[._/+:-])"
    r"[A-Za-z0-9](?:[A-Za-z0-9._/+:-]*[A-Za-z0-9])?"
    r"(?![A-Za-z0-9_])"
)
_LATINISH = rf"(?:{_PROT}|(?=[A-Za-z0-9._/+:-]*[A-Za-z])[A-Za-z0-9][A-Za-z0-9._/+:-]*)"
_ZERO_WIDTH_RE = re.compile(r"[\u200b-\u200d\ufeff]")


def normalize_tts_text(text: str) -> str:
    """Normalize prompt text without changing intended semantics."""
    text = _base_cleanup(text)
    text = _normalize_markdown_and_lines(text)
    text, protected = _protect_spans(text)
    text = _normalize_spaces(text)
    text = _normalize_structural_punctuation(text)
    text = _normalize_repeated_punctuation(text)
    text = _normalize_spaces(text)
    text = _restore_spans(text, protected)
    return text.strip()


def _base_cleanup(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u3000", " ")
    text = _ZERO_WIDTH_RE.sub("", text)
    cleaned: list[str] = []
    for ch in text:
        cat = unicodedata.category(ch)
        if ch in "\n\t " or not cat.startswith("C"):
            cleaned.append(ch)
    return "".join(cleaned)


def _normalize_markdown_and_lines(text: str) -> str:
    text = re.sub(r"\[([^\[\]]+?)\]\((https?://[^)\s]+)\)", r"\1 \2", text)
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^#{1,6}\s+", "", line)
        line = re.sub(r"^>\s+", "", line)
        line = re.sub(r"^[-*+]\s+", "", line)
        line = re.sub(r"^\d+[.)]\s+", "", line)
        lines.append(line)
    return "。".join(lines) if lines else ""


def _protect_spans(text: str) -> tuple[str, list[str]]:
    protected: list[str] = []

    def repl(match: re.Match[str]) -> str:
        idx = len(protected)
        protected.append(match.group(0))
        return f"___PROT{idx}___"

    for pattern in (
        _URL_RE,
        _EMAIL_RE,
        _MENTION_RE,
        _REDDIT_RE,
        _HASHTAG_RE,
        _DOT_TOKEN_RE,
        _FILELIKE_RE,
    ):
        text = pattern.sub(repl, text)
    return text, protected


def _restore_spans(text: str, protected: list[str]) -> str:
    for idx, original in enumerate(protected):
        text = text.replace(f"___PROT{idx}___", original)
    return text


def _normalize_spaces(text: str) -> str:
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(rf"({_CJK})\s+(?={_CJK})", r"\1", text)
    text = re.sub(rf"({_CJK})\s+(?=\d)", r"\1", text)
    text = re.sub(rf"(\d)\s+(?={_CJK})", r"\1", text)
    text = re.sub(rf"({_CJK})(?=({_LATINISH}))", r"\1 ", text)
    text = re.sub(rf"(({_LATINISH}))(?={_CJK})", r"\1 ", text)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\s+([，。！？；：、”’」』】）》])", r"\1", text)
    text = re.sub(r"([（【「『《“‘])\s+", r"\1", text)
    text = re.sub(r"([，。！？；：、])\s*", r"\1", text)
    text = re.sub(r"\s+([,.;!?])", r"\1", text)
    return re.sub(r" {2,}", " ", text).strip()


def _normalize_structural_punctuation(text: str) -> str:
    for _ in range(2):
        text = re.sub(
            r"(^|[。！？!?；;]\s*)[【〖『「]([^】〗』」]+)[】〗』」]\s*",
            r"\1\2。",
            text,
        )
    text = re.sub(
        r"(^|[。！？!?；;]\s*)《([^》]+)》(?=\s*(?:___PROT\d+___|[—–―-]{2,}|$|[。！？!?；;，,]))",
        r"\1\2",
        text,
    )
    text = re.sub(
        r"\s*(?:<[-=]+>|[-=]+>|<[-=]+|[→←↔⇒⇐⇔⟶⟵⟷⟹⟸⟺↦↤↪↩])\s*",
        "，",
        text,
    )
    text = re.sub(r"\s*(?:—|–|―|-){2,}\s*", "。", text)
    return text


def _normalize_repeated_punctuation(text: str) -> str:
    text = re.sub(r"(?:\.{3,}|…{2,}|……+)", "。", text)
    text = re.sub(r"[。．]{2,}", "。", text)
    text = re.sub(r"[，,]{2,}", "，", text)
    text = re.sub(r"[!！]{2,}", "！", text)
    text = re.sub(r"[?？]{2,}", "？", text)

    def mixed_qe(match: re.Match[str]) -> str:
        value = match.group(0)
        has_q = any(ch in value for ch in "?？")
        has_e = any(ch in value for ch in "!！")
        if has_q and has_e:
            return "？！"
        return "？" if has_q else "！"

    return re.sub(r"[!?！？]{2,}", mixed_qe, text)


_TEST_CASES: tuple[tuple[str, str, str], ...] = (
    (
        "dot_map_sentence",
        "2026 年 3 月 31 日，安全研究员 Chaofan Shou (@Fried_rice) 发现 Anthropic 的 npm 包中暴露了 .map 文件，",
        "2026年3月31日，安全研究员 Chaofan Shou (@Fried_rice) 发现 Anthropic 的 npm 包中暴露了 .map 文件，",
    ),
    ("dot_tokens", "别把 .env、.npmrc、.gitignore 提交上去。", "别把 .env、.npmrc、.gitignore 提交上去。"),
    ("file_names", "请检查 bundle.min.js、package.json 和 processing_moss_tts.py。", "请检查 bundle.min.js、package.json 和 processing_moss_tts.py。"),
    ("version_build", "Bug 的讨论可以精确到 v2.3.1 (Build 15)。", "Bug 的讨论可以精确到 v2.3.1 (Build 15)。"),
    ("url", "仓库地址是 https://github.com/instructkr/claude-code", "仓库地址是 https://github.com/instructkr/claude-code"),
    ("email", "联系邮箱：ops+tts@example.ai", "联系邮箱：ops+tts@example.ai"),
    ("mention_hashtag_boundary", "关注@biscuit0228_并转发#thetime_tbs", "关注 @biscuit0228_ 并转发 #thetime_tbs"),
    ("speaker_bracket", "[S1]你好。[S2]收到。", "[S1]你好。[S2]收到。"),
    ("pause_bracket", "它的名字是[pause 3.2s]静夜思！", "它的名字是[pause 3.2s]静夜思！"),
    ("event_bracket", "请模仿 {whisper} 的语气说“别出声”。", "请模仿 {whisper} 的语气说“别出声”。"),
    ("struct_headline", "〖重磅〗《新品发布》——现在开始！", "重磅。新品发布。现在开始！"),
    ("flow_arrow_chain", "请求接入 -> 身份与策略判定 -> 域服务处理", "请求接入，身份与策略判定，域服务处理"),
    ("embedded_title", "我喜欢《哈姆雷特》这本书。", "我喜欢《哈姆雷特》这本书。"),
    ("noise_qe", "真的假的？？？！！！", "真的假的？！"),
    ("noise_ellipsis", "这个包把 app.js.map 也发上去了......太离谱了！！！", "这个包把 app.js.map 也发上去了。太离谱了！"),
    ("english_spaces", "This   is   a   test.", "This is a test."),
    ("chinese_spaces", "这 是　一 段  含有多种空白的文本。", "这是一段含有多种空白的文本。"),
    ("mixed_spaces_1", "这是Anthropic的npm包", "这是 Anthropic 的 npm 包"),
    ("mixed_spaces_2", "今天update到v2.3.1了", "今天 update 到 v2.3.1 了"),
    ("markdown_link", "详情见 [release note](https://github.com/example/release)", "详情见 release note https://github.com/example/release"),
    ("list_lines", "- 修复 .map 泄露\n- 发布 v2.3.1", "修复 .map 泄露。发布 v2.3.1"),
    ("zero_width_url", "详见 https://x.com/\u200bSafety", "详见 https://x.com/Safety"),
)


def run_self_test(verbose: bool = True) -> None:
    failures: list[tuple[str, str, str, str]] = []
    for name, text, expected in _TEST_CASES:
        actual = normalize_tts_text(text)
        if actual != expected:
            failures.append((name, text, expected, actual))
            continue
        second = normalize_tts_text(actual)
        if second != actual:
            failures.append((name + "_idempotence", actual, actual, second))
    if failures:
        parts = ["SELF-TEST FAILED"]
        for name, text, expected, actual in failures:
            parts.extend([
                f"[{name}]",
                f"input   : {text}",
                f"expected: {expected}",
                f"actual  : {actual}",
            ])
        raise AssertionError("\n".join(parts))
    if verbose:
        print(f"All {len(_TEST_CASES)} normalize_tts_text self-tests passed.")


def _read_input(args: argparse.Namespace) -> str:
    if args.text is not None and args.input_file is not None:
        raise SystemExit("Use only one of --text or --input-file.")
    if args.text is not None:
        return args.text
    if args.input_file is not None:
        return Path(args.input_file).read_text(encoding=args.encoding)
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("Provide --text, --input-file, stdin, or --self-test.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize MOSS-TTS prompt text with no external dependencies.")
    parser.add_argument("--text", help="Text to normalize. Mutually exclusive with --input-file.")
    parser.add_argument("--input-file", help="Read text from this file.")
    parser.add_argument("--output-file", help="Write normalized text to this file instead of stdout.")
    parser.add_argument("--encoding", default="utf-8", help="File encoding for --input-file/--output-file (default: utf-8).")
    parser.add_argument("--self-test", action="store_true", help="Run bundled self-tests and exit unless text input is also provided.")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test(verbose=True)
        if args.text is None and args.input_file is None and sys.stdin.isatty():
            return 0

    normalized = normalize_tts_text(_read_input(args))
    if args.output_file:
        Path(args.output_file).write_text(normalized + "\n", encoding=args.encoding)
    else:
        print(normalized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

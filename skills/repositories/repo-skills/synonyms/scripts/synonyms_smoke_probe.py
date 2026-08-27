#!/usr/bin/env python3
"""Safe smoke probe for the installed `synonyms` package.

This helper is adapted from the repository's demo/test intent, but it is
checkout-independent and does not run maintainer scripts. It can either use a
real word2vec binary model supplied with --model-path, rely on the package's
normal SYNONYMS_DL_LICENSE / packaged-model behavior, or generate a tiny local
word2vec fixture with --use-tiny-fixture to verify API mechanics only.

Examples:
  python scripts/synonyms_smoke_probe.py --use-tiny-fixture --word 人脸
  python scripts/synonyms_smoke_probe.py --model-path /path/to/words.vector.gz --word 飞机
"""
from __future__ import annotations

import argparse
import contextlib
import gzip
import io
import json
import os
import random
import struct
import sys
import tempfile
from pathlib import Path
from typing import Any

MODEL_ENV = "SYNONYMS_WORD2VEC_BIN_MODEL_ZH_CN"

TINY_WORDS = [
    "人脸", "图片", "图像", "飞机", "直升机", "客机", "汽车", "轿车", "教学", "老师",
    "中文", "近义词", "工具包", "华为", "芯片", "供应", "三国", "奥运", "北新桥", "能量",
    "道路", "旗帜", "方向", "命运", "大家", "你们好呀",
]


def _vector_for(word: str, dim: int = 100) -> list[float]:
    """Build a deterministic 100-d vector for a tiny diagnostic model."""
    rng = random.Random("synonyms-smoke:" + word)
    vec = [rng.uniform(-0.2, 0.2) for _ in range(dim)]
    clusters = {
        "人脸": (0.91, 0.81, 0.69),
        "图片": (0.90, 0.80, 0.70),
        "图像": (0.89, 0.82, 0.71),
        "汽车": (0.40, 0.80, 0.20),
        "轿车": (0.41, 0.79, 0.21),
        "教学": (0.10, 0.70, 0.50),
        "老师": (0.11, 0.69, 0.51),
    }
    if word in clusters:
        vec[:3] = list(clusters[word])
    return vec


def write_tiny_word2vec(path: Path) -> None:
    """Write a small binary word2vec-format gzip file compatible with Synonyms."""
    dim = 100
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wb") as fout:
        fout.write(f"{len(TINY_WORDS)} {dim}\n".encode("utf-8"))
        for word in TINY_WORDS:
            fout.write(word.encode("utf-8") + b" ")
            fout.write(struct.pack("<" + "f" * dim, *_vector_for(word, dim)))
            fout.write(b"\n")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Probe an installed synonyms package. Use --model-path for a real "
            "word2vec model, or --use-tiny-fixture for API mechanics only."
        )
    )
    model_group = parser.add_mutually_exclusive_group()
    model_group.add_argument(
        "--model-path",
        help=(
            "Path to an existing word2vec binary model. The script sets "
            "SYNONYMS_WORD2VEC_BIN_MODEL_ZH_CN before importing synonyms."
        ),
    )
    model_group.add_argument(
        "--use-tiny-fixture",
        action="store_true",
        help="Generate a tiny temporary 100-d word2vec model for API-mechanics checks only.",
    )
    parser.add_argument("--word", default="人脸", help="Word to query with nearby() and v().")
    parser.add_argument("--topk", type=int, default=5, help="Number of nearby words to request.")
    parser.add_argument("--segment-text", default="中文近义词工具包", help="Text for synonyms.seg().")
    parser.add_argument("--keywords-text", default="华为芯片供应出现变化", help="Text for synonyms.keywords().")
    parser.add_argument("--sentence-a", default="旗帜引领方向", help="First sentence for synonyms.compare().")
    parser.add_argument("--sentence-b", default="旗帜指引道路", help="Second sentence for synonyms.compare().")
    parser.add_argument(
        "--show-package-output",
        action="store_true",
        help="Do not capture Synonyms/jieba import-time prints and describe() output.",
    )
    return parser.parse_args(argv)


def captured_call(show_output: bool, func, *args, **kwargs):
    if show_output:
        return func(*args, **kwargs), "", ""
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        value = func(*args, **kwargs)
    return value, out.getvalue(), err.getvalue()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.topk <= 0:
        print("--topk must be positive", file=sys.stderr)
        return 2

    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    model_mode = "package-default-or-license"
    model_path: str | None = None

    if args.model_path:
        supplied = Path(args.model_path).expanduser()
        if not supplied.is_file():
            print(f"Model file does not exist: {supplied}", file=sys.stderr)
            return 2
        os.environ[MODEL_ENV] = str(supplied)
        model_mode = "explicit-model-path"
        model_path = str(supplied)
    elif args.use_tiny_fixture:
        temp_dir = tempfile.TemporaryDirectory(prefix="synonyms-tiny-word2vec-")
        tiny_path = Path(temp_dir.name) / "tiny_words.vector.gz"
        write_tiny_word2vec(tiny_path)
        os.environ[MODEL_ENV] = str(tiny_path)
        model_mode = "tiny-fixture-api-mechanics-only"
        model_path = str(tiny_path)

    package_stdout = ""
    package_stderr = ""
    try:
        if args.show_package_output:
            import synonyms  # type: ignore
        else:
            out = io.StringIO()
            err = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                import synonyms  # type: ignore
            package_stdout = out.getvalue()
            package_stderr = err.getvalue()
    except Exception as exc:  # noqa: BLE001 - diagnostic helper should explain raw import failures.
        print(
            json.dumps(
                {
                    "ok": False,
                    "stage": "import",
                    "model_mode": model_mode,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "recovery": [
                        "Set SYNONYMS_DL_LICENSE so Synonyms can download the licensed model on first import.",
                        f"Or pass --model-path and verify {MODEL_ENV} points to a compatible binary word2vec .gz file.",
                        "Or rerun with --use-tiny-fixture when you only need to test package/API mechanics, not semantic quality.",
                    ],
                    "captured_stdout_tail": package_stdout[-1200:],
                    "captured_stderr_tail": package_stderr[-1200:],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        if temp_dir is not None:
            temp_dir.cleanup()
        return 1

    failures: list[dict[str, Any]] = []
    result: dict[str, Any] = {
        "ok": True,
        "model_mode": model_mode,
        "model_path_used": model_path,
        "note": "Tiny fixture checks prove API mechanics only; use a real licensed/equivalent model for semantic quality.",
        "captured_import_stdout_tail": package_stdout[-1200:],
        "captured_import_stderr_tail": package_stderr[-1200:],
        "checks": {},
    }

    def record(name: str, fn) -> None:
        try:
            value, stdout, stderr = captured_call(args.show_package_output, fn)
            result["checks"][name] = {"ok": True, "value": value, "stdout_tail": stdout[-800:], "stderr_tail": stderr[-800:]}
        except Exception as exc:  # noqa: BLE001 - report all package/API failures compactly.
            failures.append({"check": name, "error_type": type(exc).__name__, "error": str(exc)})
            result["checks"][name] = {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}

    record("describe", lambda: synonyms.describe())
    record("seg", lambda: {"words": list(synonyms.seg(args.segment_text)[0]), "tags": list(synonyms.seg(args.segment_text)[1])})
    record("keywords", lambda: list(synonyms.keywords(args.keywords_text, topK=3)))
    record("nearby", lambda: {"words": list(synonyms.nearby(args.word, args.topk)[0]), "scores": list(map(float, synonyms.nearby(args.word, args.topk)[1]))})
    record("vector", lambda: {"shape": list(synonyms.v(args.word).shape), "dtype": str(synonyms.v(args.word).dtype)})
    record("compare", lambda: float(synonyms.compare(args.sentence_a, args.sentence_b)))

    if failures:
        result["ok"] = False
        result["failures"] = failures

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))

    if temp_dir is not None:
        temp_dir.cleanup()
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

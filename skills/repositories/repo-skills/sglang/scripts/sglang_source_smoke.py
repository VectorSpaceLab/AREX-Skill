#!/usr/bin/env python3
from pathlib import Path


def main() -> int:
    repo = Path.cwd()
    pyproject = repo / "python" / "pyproject.toml"
    source = repo / "python" / "sglang"
    cli = source / "cli" / "main.py"
    assert pyproject.exists(), "missing python/pyproject.toml"
    assert source.exists(), "missing python/sglang"
    assert cli.exists(), "missing python/sglang/cli/main.py"
    text = pyproject.read_text(encoding="utf-8")
    for token in ["torch==", "transformers==", "flashinfer", "sglang"]:
        assert token in text, f"expected dependency/source marker not found: {token}"
    print({"ok": True, "source": str(source), "cli": str(cli)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

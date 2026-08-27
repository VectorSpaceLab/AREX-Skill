#!/usr/bin/env python3
"""Heuristically classify a GPT Academic agent-tooling request."""
from __future__ import annotations

import argparse
import json
import re

WRITE_WORDS = ["modify", "edit", "delete", "clear", "remove", "overwrite", "配置", "修改", "删除", "清除", "写入"]
SHELL_WORDS = ["command", "shell", "docker", "pip install", "apt", "run", "命令", "终端", "执行"]
CODE_WORDS = ["code interpreter", "python", "script", "uploaded file", "生成代码", "代码解释器"]
PLUGIN_WORDS = ["plugin", "插件", "调用", "void terminal", "虚空终端"]
SECRET_WORDS = ["api key", "token", "secret", "password", "密钥", "令牌", "密码"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("text", nargs="*", help="user request text")
    args = parser.parse_args()
    text = " ".join(args.text).strip()
    low = text.lower()
    rec = "direct-plugin-or-domain-subskill"
    if any(w in low for w in CODE_WORDS):
        rec = "code-interpreter"
    if any(w in low for w in SHELL_WORDS):
        rec = "commandline-assistant"
    if any(w in low for w in PLUGIN_WORDS):
        rec = "void-terminal-or-plugin-dispatch"
    risks = []
    if any(w in low for w in WRITE_WORDS):
        risks.append("write/destructive action: require explicit confirmation and backup")
    if any(w in low for w in SECRET_WORDS):
        risks.append("secret-handling risk: do not paste or print credentials")
    if re.search(r"(rm -rf|sudo|chmod|chown|curl .*\|\s*sh)", low):
        risks.append("unsafe shell pattern detected")
    print(json.dumps({"request": text, "recommended_surface": rec, "risks": risks, "requires_confirmation": bool(risks)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

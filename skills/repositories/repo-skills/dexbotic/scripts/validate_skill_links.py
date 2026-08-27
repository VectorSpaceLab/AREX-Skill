#!/usr/bin/env python3
"""Check internal Markdown links and required frontmatter in a runtime tree."""
from __future__ import annotations
import argparse,re
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("root",type=Path); a=ap.parse_args(); errors=[]
    skills=sorted(a.root.rglob("SKILL.md"))
    if not (a.root/"SKILL.md").exists(): errors.append("missing root SKILL.md")
    for p in skills:
        text=p.read_text(encoding="utf-8")
        if not re.search(r'^name:\s*[a-z0-9][a-z0-9-]*\s*$',text,re.M): errors.append(f"{p}: invalid name")
        if not re.search(r'^description:\s*\"',text,re.M): errors.append(f"{p}: description must be quoted")
        if "disco-role: operating" not in text: errors.append(f"{p}: missing operating role")
        if "disable-model-invocation: true" not in text: errors.append(f"{p}: missing disable flag")
        for target in re.findall(r'\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)',text):
            if target.startswith(("http:","https:","mailto:")): continue
            q=(p.parent/target).resolve()
            if not q.exists(): errors.append(f"{p}: broken link {target}")
    print("OK" if not errors else "\n".join(errors)); raise SystemExit(0 if not errors else 1)
if __name__=="__main__":main()

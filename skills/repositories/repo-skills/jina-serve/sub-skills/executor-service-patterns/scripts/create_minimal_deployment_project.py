#!/usr/bin/env python3
"""Create a minimal self-contained Jina Deployment project."""

from __future__ import annotations

import argparse
from pathlib import Path

EXECUTOR = '''from jina import Executor, requests
from docarray import BaseDoc, DocList


class TextDoc(BaseDoc):
    text: str = ""


class MyExecutor(Executor):
    @requests(on="/uppercase")
    def uppercase(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        for doc in docs:
            doc.text = doc.text.upper()
        return docs
'''

DEPLOYMENT = '''jtype: Deployment
with:
  uses: MyExecutor
  py_modules:
    - executor.py
  port: 12345
'''

CLIENT = '''from jina import Client
from docarray import DocList
from executor import TextDoc

client = Client(port=12345)
result = client.post("/uppercase", DocList[TextDoc]([TextDoc(text="hello")]), return_type=DocList[TextDoc])
print(result[0].text)
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Directory to create. It must not already contain files unless --force is set.")
    parser.add_argument("--force", action="store_true", help="Overwrite files in an existing directory.")
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    if root.exists() and any(root.iterdir()) and not args.force:
        raise SystemExit(f"Refusing to write into non-empty directory without --force: {root}")
    root.mkdir(parents=True, exist_ok=True)
    (root / "executor.py").write_text(EXECUTOR, encoding="utf-8")
    (root / "deployment.yml").write_text(DEPLOYMENT, encoding="utf-8")
    (root / "client.py").write_text(CLIENT, encoding="utf-8")
    (root / "requirements.txt").write_text("jina\n", encoding="utf-8")
    print(f"Created {root}")
    print("Run: jina deployment --uses deployment.yml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

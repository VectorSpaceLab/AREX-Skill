#!/usr/bin/env python3
"""Create a minimal Jina Flow project for local experimentation."""

from __future__ import annotations

import argparse
from pathlib import Path

EXECUTOR = '''from jina import Executor, requests
from docarray import BaseDoc, DocList


class TextDoc(BaseDoc):
    text: str = ""


class EchoExecutor(Executor):
    @requests(on="/echo")
    def echo(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        for doc in docs:
            doc.text = f"echo:{doc.text}"
        return docs
'''

FLOW = '''jtype: Flow
version: "1"
gateway:
  protocol: [grpc, http, websocket]
  port: [54321, 54322, 54323]
executors:
  - name: echo
    uses: executor.yml
'''

EXECUTOR_YAML = '''jtype: EchoExecutor
py_modules:
  - executor.py
'''

CLIENT = '''from jina import Client
from docarray import DocList
from executor import TextDoc

client = Client(port=54321)
out = client.post("/echo", DocList[TextDoc]([TextDoc(text="hello")]), return_type=DocList[TextDoc])
print(out[0].text)
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Directory to create.")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    if root.exists() and any(root.iterdir()) and not args.force:
        raise SystemExit(f"Refusing to overwrite non-empty directory without --force: {root}")
    root.mkdir(parents=True, exist_ok=True)
    (root / "executor.py").write_text(EXECUTOR, encoding="utf-8")
    (root / "executor.yml").write_text(EXECUTOR_YAML, encoding="utf-8")
    (root / "flow.yml").write_text(FLOW, encoding="utf-8")
    (root / "client.py").write_text(CLIENT, encoding="utf-8")
    print(f"Created {root}")
    print("Run: jina flow --uses flow.yml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

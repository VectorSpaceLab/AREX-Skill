#!/usr/bin/env python3
"""Create a tiny local Metaflow run and query it through the Client API.

Example:
  python client_query_smoke.py --json
"""
import argparse
import json
import os
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny flow and read an artifact via Metaflow Client API.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--username", default=os.environ.get("USERNAME") or os.environ.get("METAFLOW_USER") or "disco")
    args = parser.parse_args()

    from metaflow import Runner, Run, namespace

    with tempfile.TemporaryDirectory(prefix="metaflow-client-smoke-") as tmp:
        flow = Path(tmp) / "client_skill_flow.py"
        flow.write_text(
            "from metaflow import FlowSpec, step\n"
            "class ClientSkillFlow(FlowSpec):\n"
            "    @step\n"
            "    def start(self):\n"
            "        self.answer = 42\n"
            "        self.next(self.end)\n"
            "    @step\n"
            "    def end(self):\n"
            "        pass\n"
            "if __name__ == '__main__':\n"
            "    ClientSkillFlow()\n",
            encoding="utf-8",
        )
        with Runner(str(flow), show_output=False, pylint=False, env={"USERNAME": args.username}, cwd=tmp) as runner:
            executing = runner.run(max_workers=1)
            pathspec = executing.run.pathspec
            namespace(None)
            answer = Run(pathspec)["end"].task.data.answer
    result = {"pathspec": pathspec, "answer": answer, "status": executing.status}
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else result)
    return 0 if answer == 42 else 1


if __name__ == "__main__":
    raise SystemExit(main())

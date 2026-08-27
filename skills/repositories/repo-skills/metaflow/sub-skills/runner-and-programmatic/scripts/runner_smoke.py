#!/usr/bin/env python3
"""Run a self-contained Metaflow Runner smoke test.

Example:
  python runner_smoke.py --json
"""
import argparse
import json
import os
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a temporary flow, run it with Metaflow Runner, and read an artifact.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("--username", default=os.environ.get("USERNAME") or os.environ.get("METAFLOW_USER") or "disco")
    args = parser.parse_args()

    from metaflow import Runner

    with tempfile.TemporaryDirectory(prefix="metaflow-runner-smoke-") as tmp:
        flow_file = Path(tmp) / "runner_skill_flow.py"
        flow_file.write_text(
            "from metaflow import FlowSpec, step\n"
            "class RunnerSkillFlow(FlowSpec):\n"
            "    @step\n"
            "    def start(self):\n"
            "        self.answer = 42\n"
            "        self.next(self.end)\n"
            "    @step\n"
            "    def end(self):\n"
            "        pass\n"
            "if __name__ == '__main__':\n"
            "    RunnerSkillFlow()\n",
            encoding="utf-8",
        )
        with Runner(str(flow_file), show_output=False, pylint=False, env={"USERNAME": args.username}, cwd=tmp) as runner:
            executing = runner.run(max_workers=1)
            answer = executing.run["end"].task.data.answer
            result = {"status": executing.status, "returncode": executing.returncode, "pathspec": executing.run.pathspec, "answer": answer}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"status={result['status']} returncode={result['returncode']} pathspec={result['pathspec']} answer={result['answer']}")
    return 0 if result["status"] == "successful" and result["answer"] == 42 else 1


if __name__ == "__main__":
    raise SystemExit(main())

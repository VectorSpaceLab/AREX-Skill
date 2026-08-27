#!/usr/bin/env python3
"""Print focused PennyLane development commands for changed files.

This helper does not run commands. Pass changed paths to get a conservative
pytest/lint/format/tach plan.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def test_guess(path: Path) -> str | None:
    if path.parts and path.parts[0] == "tests":
        return f"python -m pytest {path}"
    if path.parts and path.parts[0] == "pennylane" and path.suffix == ".py":
        rel = Path(*path.parts[1:])
        guess = Path("tests") / rel
        if guess.name != "__init__.py":
            return f"python -m pytest {guess.with_name('test_' + guess.name)}"
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Changed files relative to a PennyLane checkout")
    args = parser.parse_args()
    source = [Path(p) for p in args.paths if p.startswith("pennylane/") and p.endswith(".py")]
    tests = [Path(p) for p in args.paths if p.startswith("tests/") and p.endswith(".py")]
    print("# Suggested focused test commands")
    seen = set()
    for path in [*source, *tests]:
        cmd = test_guess(path)
        if cmd and cmd not in seen:
            print(cmd)
            seen.add(cmd)
    print("\n# Lint commands")
    if source:
        print("pylint -rn -sn --persistent=n --rcfile=.pylintrc " + " ".join(map(str, source)))
    if tests:
        print("pylint -rn -sn --persistent=n --rcfile=tests/.pylintrc " + " ".join(map(str, tests)))
    py_files = [*source, *tests]
    if py_files:
        joined = " ".join(map(str, py_files))
        print("\n# Formatting")
        print(f"black --config ./pyproject.toml {joined}")
        print(f"isort --settings-path ./pyproject.toml {joined}")
    print("\n# If imports/module boundaries changed")
    print("tach check")


if __name__ == "__main__":
    main()

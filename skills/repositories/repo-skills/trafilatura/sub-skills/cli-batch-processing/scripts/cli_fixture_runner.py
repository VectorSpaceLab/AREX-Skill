#!/usr/bin/env python3
"""No-network smoke runner for the Trafilatura CLI.

The helper creates temporary HTML fixtures, invokes the installed Trafilatura
CLI via ``python -m trafilatura.cli`` with a console-script fallback, and asserts
that expected title/text appears in stdout and local-directory outputs.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_TITLE = "Trafilatura CLI Fixture"
EXPECTED_PHRASE = "This fixture paragraph proves the command line extractor handled local HTML input."


def build_html() -> bytes:
    """Return an article-like HTML document large enough for extraction."""
    paragraphs = "\n".join(
        f"<p>{EXPECTED_PHRASE} Repeated evidence sentence {idx} keeps the fixture above size thresholds.</p>"
        for idx in range(1, 12)
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{EXPECTED_TITLE}</title>
  <meta name="author" content="DisCo Fixture">
  <meta property="article:published_time" content="2024-01-02">
  <meta name="description" content="A deterministic local Trafilatura CLI fixture.">
</head>
<body>
  <header><nav>Navigation noise that should not dominate extraction.</nav></header>
  <article>
    <h1>{EXPECTED_TITLE}</h1>
    {paragraphs}
    <table><tr><td>Fixture table cell</td></tr></table>
  </article>
  <footer>Footer boilerplate.</footer>
</body>
</html>
"""
    return html.encode("utf-8")


def candidate_commands() -> list[list[str]]:
    """Prefer module invocation, then fall back to the console script."""
    commands = [[sys.executable, "-m", "trafilatura.cli"]]
    script = shutil.which("trafilatura")
    if script:
        commands.append([script])
    return commands


def run_cli(args: list[str], *, input_bytes: bytes | None, cwd: Path, timeout: float) -> tuple[subprocess.CompletedProcess[bytes], str]:
    """Run the CLI and return the first successful invocation."""
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    failures: list[str] = []
    for command in candidate_commands():
        completed = subprocess.run(
            [*command, *args],
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(cwd),
            env=env,
            timeout=timeout,
            check=False,
        )
        if command[:3] == [sys.executable, "-m", "trafilatura.cli"]:
            command_text = "python -m trafilatura.cli " + " ".join(args)
        else:
            command_text = "trafilatura " + " ".join(args)
        if completed.returncode == 0:
            return completed, command_text
        failures.append(
            f"$ {command_text}\n"
            f"exit={completed.returncode}\n"
            f"stdout={completed.stdout.decode('utf-8', 'replace')[:1000]}\n"
            f"stderr={completed.stderr.decode('utf-8', 'replace')[:2000]}"
        )
    raise AssertionError("Trafilatura CLI failed for all invocation forms:\n\n" + "\n\n".join(failures))


def assert_contains(output: str, context: str) -> None:
    """Assert that the expected fixture content is present."""
    missing = [text for text in (EXPECTED_TITLE, EXPECTED_PHRASE) if text not in output]
    if missing:
        raise AssertionError(f"Missing expected content in {context}: {missing!r}\nOutput preview:\n{output[:2000]}")


def run_stdin_check(workdir: Path, *, json_mode: bool, timeout: float) -> str:
    """Run a stdin extraction check."""
    args = ["--json", "--with-metadata"] if json_mode else ["--markdown", "--with-metadata"]
    completed, command_text = run_cli(args, input_bytes=build_html(), cwd=workdir, timeout=timeout)
    stdout = completed.stdout.decode("utf-8", "replace")
    stderr = completed.stderr.decode("utf-8", "replace")
    assert_contains(stdout, "stdin output")

    if json_mode:
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"JSON mode did not produce parseable JSON: {exc}\nstdout={stdout[:2000]}") from exc
        serialized = json.dumps(parsed, ensure_ascii=False)
        assert_contains(serialized, "parsed JSON output")

    if "ERROR:" in stderr:
        raise AssertionError(f"Unexpected CLI error on stderr for {command_text}:\n{stderr}")
    return command_text


def run_directory_check(workdir: Path, *, timeout: float) -> str:
    """Run a local --input-dir/--output-dir smoke check."""
    input_root = workdir / "input-html"
    nested = input_root / "section-a"
    nested.mkdir(parents=True)
    (nested / "page.html").write_bytes(build_html())
    output_root = workdir / "extracted"

    args = [
        "--input-dir",
        "input-html",
        "--output-dir",
        "extracted",
        "--markdown",
        "--parallel",
        "1",
    ]
    completed, command_text = run_cli(args, input_bytes=None, cwd=workdir, timeout=timeout)
    stderr = completed.stderr.decode("utf-8", "replace")
    if "ERROR:" in stderr:
        raise AssertionError(f"Unexpected CLI error on stderr for {command_text}:\n{stderr}")

    candidates = sorted(output_root.rglob("*.txt"))
    if not candidates:
        raise AssertionError(f"No .txt output files created under {output_root}")
    combined = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in candidates)
    assert_contains(combined, "directory output files")
    return command_text


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run no-network Trafilatura CLI fixture checks.")
    parser.add_argument("--json", action="store_true", help="check stdin extraction with --json --with-metadata")
    parser.add_argument(
        "--skip-directory",
        action="store_true",
        help="skip the --input-dir/-o directory smoke check",
    )
    parser.add_argument("--timeout", type=float, default=30.0, help="subprocess timeout in seconds (default: 30)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    with tempfile.TemporaryDirectory(prefix="trafilatura-cli-fixture-") as tmp:
        workdir = Path(tmp)
        commands = [run_stdin_check(workdir, json_mode=args.json, timeout=args.timeout)]
        if not args.skip_directory:
            commands.append(run_directory_check(workdir, timeout=args.timeout))
    print("cli-fixture-ok")
    for command in commands:
        print(f"ran: {command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

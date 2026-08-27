#!/usr/bin/env python3
"""Safe package smoke for speech-to-speech.

This root helper verifies import metadata and CLI help without starting a
server, loading models, opening audio devices, or contacting providers.
"""

from __future__ import annotations

import importlib.metadata as metadata
import os
import subprocess
import sys


def run_help(command: list[str]) -> str:
    env = {**os.environ, "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", "")}
    result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    return result.stdout


def main() -> int:
    import speech_to_speech

    dist_version = metadata.version("speech-to-speech")
    package_version = getattr(speech_to_speech, "__version__", "<missing>")
    if dist_version != package_version:
        raise RuntimeError(f"distribution/package version mismatch: {dist_version} != {package_version}")

    root_help = run_help(["speech-to-speech", "--help"])
    for command in ("serve", "talk", "local"):
        if command not in root_help:
            raise RuntimeError(f"root help missing command {command!r}")
        run_help(["speech-to-speech", command, "--help"])

    print(f"speech-to-speech package smoke passed: version {package_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

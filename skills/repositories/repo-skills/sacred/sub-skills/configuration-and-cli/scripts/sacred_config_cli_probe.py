#!/usr/bin/env python3
"""Safe Sacred configuration and CLI probe.

The probe creates a temporary Sacred experiment script and executes it with the
current Python interpreter. It uses only temporary files/directories, performs no
network access, starts no services, and does not require the original source
checkout. The current Python must already be able to import Sacred.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


EXPERIMENT_SCRIPT = r'''
from sacred import Experiment, cli_option


@cli_option("-z", "--tag")
def tag_option(args, run):
    """Attach a tag in run.info."""
    run.info["tag"] = args


ex = Experiment(
    "config_cli_probe",
    additional_cli_options=[tag_option],
    save_git_info=False,
)

ex.add_config({
    "message": "Hello",
    "recipient": "world",
    "nested": {"value": 2},
    "punctuation": ".",
    "repeat": 1,
    "derived": "",
})


@ex.named_config
def excited():
    """Use an excited greeting."""
    message = "Hi"
    punctuation = "!"


@ex.config_hook
def add_derived(config, command_name, logger):
    return {
        "derived": "{} {}{}".format(
            config["message"], config["recipient"], config["punctuation"]
        )
    }


@ex.command
def greet(message, recipient, punctuation, repeat, nested, derived, _run):
    text = ("{} {}{}".format(message, recipient, punctuation)) * repeat
    print("GREET=" + text)
    print("NESTED_VALUE={}".format(nested["value"]))
    print("DERIVED=" + derived)
    if _run.info.get("tag"):
        print("TAG=" + _run.info["tag"])


@ex.main
def main(message, recipient, punctuation, nested):
    print(
        "MAIN={} {}{} NESTED={}".format(
            message, recipient, punctuation, nested["value"]
        )
    )


if __name__ == "__main__":
    ex.run_commandline()
'''

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def run_case(script_path: Path, label: str, argv: list[str], expected: list[str]) -> str:
    env = os.environ.copy()
    # Avoid accidentally relying on a checkout injected via PYTHONPATH. A normal
    # package install or editable install remains importable through site-packages.
    env.pop("PYTHONPATH", None)

    proc = subprocess.run(
        [sys.executable, str(script_path), *argv],
        cwd=str(script_path.parent),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    combined = proc.stdout + proc.stderr
    clean = strip_ansi(combined)

    if proc.returncode != 0:
        raise AssertionError(
            f"{label} failed with exit code {proc.returncode}\n"
            f"ARGV: {argv!r}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )

    missing = [item for item in expected if item not in clean]
    if missing:
        raise AssertionError(
            f"{label} did not contain expected output {missing!r}\n"
            f"ARGV: {argv!r}\nCOMBINED OUTPUT:\n{clean}"
        )
    return clean


def main() -> int:
    cases = [
        (
            "print_config_with_updates",
            [
                "print_config",
                "with",
                "nested.value=9",
                'message="Hi"',
                "-l",
                "WARNING",
                "-u",
                "-C",
                "no",
            ],
            ["Configuration", "message = 'Hi'", "value = 9", "derived = 'Hi world.'"],
        ),
        (
            "print_named_configs",
            ["print_named_configs", "-l", "WARNING", "-u", "-C", "no"],
            ["Named Configurations", "excited", "Use an excited greeting"],
        ),
        (
            "custom_command_named_config_and_custom_option",
            [
                "greet",
                "with",
                "excited",
                'recipient="Ada"',
                "nested.value=5",
                "repeat=2",
                "--tag=cli-probe",
                "-l",
                "WARNING",
                "-u",
                "-f",
                "-C",
                "no",
            ],
            ["GREET=Hi Ada!Hi Ada!", "NESTED_VALUE=5", "DERIVED=Hi Ada!", "TAG=cli-probe"],
        ),
        (
            "main_command_cli_updates",
            [
                "main",
                "with",
                'recipient="Bob"',
                "nested.value=7",
                "-l",
                "WARNING",
                "-u",
                "-C",
                "no",
            ],
            ["MAIN=Hello Bob. NESTED=7"],
        ),
    ]

    with tempfile.TemporaryDirectory(prefix="sacred-config-cli-probe-") as tmp:
        script_path = Path(tmp) / "probe_experiment.py"
        script_path.write_text(EXPERIMENT_SCRIPT, encoding="utf-8")
        observed = []
        for label, argv, expected in cases:
            run_case(script_path, label, argv, expected)
            observed.append(label)

    print("SACRED_CONFIG_CLI_PROBE_OK " + " ".join(observed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

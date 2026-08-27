#!/usr/bin/env python3
"""Run a safe local smoke test for `labml_remote` project setup.

This script creates a temporary project, feeds deterministic answers to
`labml_remote.configs.defaults.create_default_project`, and validates the parsed
configuration helpers.

Example:
    python scripts/remote_config_smoke.py
"""

from __future__ import annotations

import builtins
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from labml_remote.configs import Configs
from labml_remote.configs.defaults import create_default_project
from labml_remote.util import get_env_vars, template


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="labml-remote-smoke-") as tmp:
        cwd = Path(tmp)
        old_cwd = Path.cwd()
        os.chdir(cwd)
        try:
            answers = iter([
                "sample-project",
                "127.0.0.1",
                "ubuntu",
                "",
            ])
            with patch.object(builtins, "input", lambda prompt='': next(answers)):
                create_default_project(Path("."))

            conf = Configs.get()
            print(f"project_name={conf.name}")
            print(f"servers={list(conf.servers)}")
            print(f"scripts_folder={conf.project_scripts_folder}")
            print(f"logs_folder={conf.project_logs_folder}")
            print(f"jobs_folder={conf.project_jobs_folder}")
            print(f"exclude_file={conf.exclude_file}")
            print(f"env_vars={get_env_vars({'A': '1', 'B': 'two'})}")

            template_file = cwd / "template.txt"
            template_file.write_text("hello %%NAME%%\n")
            rendered = template(template_file, {"name": "world"})
            print(rendered.strip())

            if conf.name != "sample-project":
                return 1
            if list(conf.servers) != ["default"]:
                return 1
            if "export A=1" not in get_env_vars({'A': '1'}):
                return 1
            if rendered.strip() != "hello world":
                return 1
            return 0
        finally:
            os.chdir(old_cwd)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Smoke-test Opyrator wrapping and CLI behavior without external services."""

import argparse
import contextlib
import importlib
import json
import os
import sys
import tempfile
import textwrap
from typing import Any, Dict

FIXTURE_MODULE = "wrapping_cli_fixture"
FIXTURE_SOURCE = textwrap.dedent(
    '''
    import json as _json

    from pydantic import BaseModel

    class CompatBaseModel(BaseModel):
        def json(self, *args, **kwargs):
            indent = kwargs.pop("indent", None)
            if kwargs:
                raise TypeError("unsupported kwargs for CompatBaseModel.json")
            if hasattr(self, "model_dump"):
                return _json.dumps(self.model_dump(), indent=indent)
            return super().json(*args, indent=indent)

    class Input(CompatBaseModel):
        message: str

    class Output(CompatBaseModel):
        message: str

    def hello_world(input: Input) -> Output:
        """Returns a greeting from the fixture."""
        return Output(message="hello " + input.message)

    class Greeter:
        """Callable class docstring used as fallback."""

        def __call__(self, input: Input) -> Output:
            return Output(message="class " + input.message)

    greeter = Greeter()

    def bad_missing_input(input):
        return Output(message=input.message)
    '''
)


@contextlib.contextmanager
def _pushd(path: str):
    previous = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


@contextlib.contextmanager
def _temp_sys_path(path: str):
    sys.path.insert(0, path)
    try:
        yield
    finally:
        try:
            sys.path.remove(path)
        except ValueError:
            pass


def _write_fixture(directory: str) -> str:
    module_path = os.path.join(directory, FIXTURE_MODULE + ".py")
    with open(module_path, "w", encoding="utf-8") as handle:
        handle.write(FIXTURE_SOURCE)
    return module_path


def _invoke_cli(cli: Any, args: list, cwd: str):
    from typer.testing import CliRunner

    runner = CliRunner()
    original_sys_path = list(sys.path)
    try:
        with _pushd(cwd):
            return runner.invoke(cli, args, prog_name="opyrator")
    finally:
        sys.path[:] = original_sys_path


def _combined_output(result: Any) -> str:
    stdout = getattr(result, "output", "") or ""
    try:
        stderr = getattr(result, "stderr", "") or ""
    except Exception:
        stderr = ""
    if stderr and stderr not in stdout:
        return stdout + stderr
    return stdout


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _require_contains(text: str, needle: str, label: str) -> None:
    _require(needle in text, f"missing {label}: {needle!r}\n{text}")


def _run_checks(temp_dir: str) -> Dict[str, Any]:
    from opyrator import Opyrator
    from opyrator._cli import cli as opyrator_cli

    importlib.invalidate_caches()
    with _temp_sys_path(temp_dir):
        fixture = importlib.import_module(FIXTURE_MODULE)

        wrapped = Opyrator(fixture.hello_world)
        _require(wrapped.name == "Hello World", f"unexpected function name: {wrapped.name!r}")
        _require(
            wrapped.description == "Returns a greeting from the fixture.",
            f"unexpected function description: {wrapped.description!r}",
        )
        _require(wrapped.input_type.__name__ == "Input", "unexpected input type")
        _require(wrapped.output_type.__name__ == "Output", "unexpected output type")
        _require(wrapped({"message": "Ada"}).message == "hello Ada", "dict call failed")
        _require(
            wrapped('{"message": "Ada"}').message == "hello Ada",
            "json-string call failed",
        )

        callable_instance = Opyrator("wrapping_cli_fixture:greeter")
        _require(callable_instance.name == "Greeter", f"unexpected class name: {callable_instance.name!r}")
        _require(
            callable_instance.description == "Callable class docstring used as fallback.",
            f"unexpected class description: {callable_instance.description!r}",
        )
        _require(
            callable_instance({"message": "Ada"}).message == "class Ada",
            "callable-instance call failed",
        )

        try:
            Opyrator("wrapping_cli_fixture:bad_missing_input")
        except ValueError as exc:
            _require(
                "input" in str(exc) and "typing annotation" in str(exc),
                f"unexpected missing-input error: {exc}",
            )
        else:
            raise AssertionError("missing-input callable should have been rejected")

        call_help = _invoke_cli(opyrator_cli, ["call", "--help"], temp_dir)
        _require(call_help.exit_code == 0, f"call help failed: {call_help.exit_code}")
        _require_contains(call_help.output, "Usage: opyrator call", "call help usage")
        _require_contains(call_help.output, "INPUT_DATA", "call help input argument")

        export_help = _invoke_cli(opyrator_cli, ["export", "--help"], temp_dir)
        _require(export_help.exit_code == 0, f"export help failed: {export_help.exit_code}")
        _require_contains(export_help.output, "Usage: opyrator export", "export help usage")
        _require_contains(export_help.output, "--format", "export help format option")

        deploy_help = _invoke_cli(opyrator_cli, ["deploy", "--help"], temp_dir)
        _require(deploy_help.exit_code == 0, f"deploy help failed: {deploy_help.exit_code}")
        _require_contains(deploy_help.output, "Usage: opyrator deploy", "deploy help usage")

        call_result = _invoke_cli(
            opyrator_cli,
            ["call", f"{FIXTURE_MODULE}:hello_world", '{"message": "Ada"}'],
            temp_dir,
        )
        _require(call_result.exit_code == 0, f"call failed: {call_result.exit_code}\n{call_result.output}")
        _require(
            json.loads(call_result.output.strip()) == {"message": "hello Ada"},
            f"unexpected call output: {call_result.output!r}",
        )

        export_zip = _invoke_cli(
            opyrator_cli,
            ["export", f"{FIXTURE_MODULE}:hello_world", "bundle.zip"],
            temp_dir,
        )
        export_docker = _invoke_cli(
            opyrator_cli,
            ["export", f"{FIXTURE_MODULE}:hello_world", "bundle-image:latest", "--format", "docker"],
            temp_dir,
        )
        export_pex = _invoke_cli(
            opyrator_cli,
            ["export", f"{FIXTURE_MODULE}:hello_world", "bundle.pex", "--format", "pex"],
            temp_dir,
        )
        for label, result in (
            ("zip export", export_zip),
            ("docker export", export_docker),
            ("pex export", export_pex),
        ):
            _require(result.exit_code == 0, f"{label} failed: {result.exit_code}\n{_combined_output(result)}")
            _require_contains(_combined_output(result), "[WIP] This feature is not finalized yet.", label)
        _require(
            not os.path.exists(os.path.join(temp_dir, "bundle.zip")),
            "export should not create bundle.zip",
        )
        _require(
            not os.path.exists(os.path.join(temp_dir, "bundle-image:latest")),
            "export should not create bundle-image:latest",
        )
        _require(
            not os.path.exists(os.path.join(temp_dir, "bundle.pex")),
            "export should not create bundle.pex",
        )

        deploy_result = _invoke_cli(
            opyrator_cli,
            ["deploy", f"{FIXTURE_MODULE}:hello_world"],
            temp_dir,
        )
        _require(deploy_result.exit_code == 0, f"deploy failed: {deploy_result.exit_code}\n{_combined_output(deploy_result)}")
        _require_contains(_combined_output(deploy_result), "[WIP] This feature is not finalized yet.", "deploy WIP")

        return {
            "function_name": wrapped.name,
            "function_description": wrapped.description,
            "class_name": callable_instance.name,
            "class_description": callable_instance.description,
            "call_stdout": call_result.output.strip(),
            "export_messages": {
                "zip": _combined_output(export_zip).strip(),
                "docker": _combined_output(export_docker).strip(),
                "pex": _combined_output(export_pex).strip(),
            },
            "deploy_stdout": _combined_output(deploy_result).strip(),
            "help_commands_checked": ["call", "export", "deploy"],
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a temporary Opyrator fixture and smoke-test wrapping plus CLI behavior."
    )
    parser.add_argument("--json", action="store_true", help="Print structured JSON output.")
    args = parser.parse_args()

    try:
        import opyrator  # noqa: F401 - import proves the package is available for the smoke run
    except Exception as exc:
        print(f"failed to import opyrator: {exc}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="opyrator-smoke-") as temp_dir:
        _write_fixture(temp_dir)
        summary = _run_checks(temp_dir)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("Opyrator wrapping and CLI smoke checks passed.")
        print("Checked commands: call, export, deploy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

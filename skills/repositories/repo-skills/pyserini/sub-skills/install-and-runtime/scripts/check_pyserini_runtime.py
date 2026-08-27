#!/usr/bin/env python3
"""Safe Pyserini runtime diagnostics for install/import/JVM issues."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str
    hint: str = ""


def sanitize_message(message: object, *, verbose: bool = False) -> str:
    text = str(message).strip()
    if verbose:
        return text
    home = str(Path.home())
    if home and home != "/":
        text = text.replace(home, "<home>")
    cwd = str(Path.cwd())
    if cwd and cwd != "/":
        text = text.replace(cwd, "<cwd>")
    text = re.sub(r"/[^\s:'\")]+(?:/[^\s:'\")]+)+", "<path>", text)
    text = re.sub(r"[A-Za-z]:\\[^\s:'\")]+(?:\\[^\s:'\")]+)+", "<path>", text)
    return text


def add_result(results: list[CheckResult], name: str, status: str, detail: str, hint: str = "") -> None:
    results.append(CheckResult(name=name, status=status, detail=detail, hint=hint))


def parse_java_major(output: str) -> int | None:
    match = re.search(r'(?:version\s+)?"?(\d+)(?:\.(\d+))?', output)
    if not match:
        return None
    first = int(match.group(1))
    second = match.group(2)
    if first == 1 and second is not None:
        return int(second)
    return first


def check_python(results: list[CheckResult]) -> None:
    version = sys.version_info
    version_text = f"{version.major}.{version.minor}.{version.micro} ({platform.python_implementation()})"
    if (version.major, version.minor) == (3, 12):
        add_result(results, "python", "PASS", f"Python {version_text}; Pyserini's documented target is Python 3.12")
    elif (version.major, version.minor) > (3, 12):
        add_result(
            results,
            "python",
            "WARN",
            f"Python {version_text}; metadata permits >=3.12, but Pyserini is documented around 3.12",
            "Prefer Python 3.12 if binary dependency wheels or runtime imports fail.",
        )
    else:
        add_result(
            results,
            "python",
            "FAIL",
            f"Python {version_text}; Pyserini requires Python >=3.12",
            "Create a fresh Python 3.12 environment and reinstall Pyserini.",
        )


def find_java_command() -> tuple[list[str], str]:
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        candidate = Path(java_home) / "bin" / "java"
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return [str(candidate), "-version"], "JAVA_HOME"
    return ["java", "-version"], "PATH"


def check_java(results: list[CheckResult], *, verbose: bool) -> None:
    command, source = find_java_command()
    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
    except FileNotFoundError:
        add_result(results, "java", "FAIL", "java executable not found on PATH and JAVA_HOME/bin/java is not executable", "Install/select JDK 21 before Lucene-backed Pyserini imports.")
        return
    except subprocess.TimeoutExpired:
        add_result(results, "java", "FAIL", f"java -version from {source} timed out", "Fix the Java installation before starting Pyserini JVM checks.")
        return

    output = (completed.stderr or completed.stdout or "").strip()
    safe_output = sanitize_message(output.splitlines()[0] if output else "java produced no version output", verbose=verbose)
    if completed.returncode != 0:
        add_result(results, "java", "FAIL", safe_output, "Install/select a working JDK 21 and retry.")
        return

    major = parse_java_major(output)
    detail = f"{safe_output} ({source})"
    if major == 21:
        add_result(results, "java", "PASS", detail)
    elif major is None:
        add_result(results, "java", "WARN", detail, "Pyserini expects Java 21; verify this Java is compatible.")
    else:
        add_result(results, "java", "WARN", detail, "Select JDK 21 if Lucene/PyJNIus imports fail.")


def import_module_check(results: list[CheckResult], module_name: str, label: str, *, verbose: bool) -> Any | None:
    try:
        module = importlib.import_module(module_name)
    except Exception as exception:
        add_result(
            results,
            label,
            "FAIL",
            sanitize_message(f"{type(exception).__name__}: {exception}", verbose=verbose),
            recovery_hint(module_name, exception),
        )
        return None
    add_result(results, label, "PASS", f"import {module_name} succeeded")
    return module


def recovery_hint(module_name: str, exception: Exception) -> str:
    message = str(exception).lower()
    if "no matching jar file found" in message:
        return "Use the PyPI package or make an anserini-*-fatjar.jar available via package resources or ANSERINI_CLASSPATH."
    if "no module named 'faiss'" in message or "no module named faiss" in message:
        return "Install faiss-cpu or a platform-compatible GPU Faiss package for Faiss/server paths."
    if "no module named 'jnius" in message or "no module named jnius" in message:
        return "Install Pyserini dependencies into the active Python environment; PyJNIus is required for Lucene paths."
    if "classnotfound" in message or "noclassdeffound" in message:
        return "Check that the Anserini fatjar matches this Pyserini version and restart the Python process."
    if module_name.startswith("pyserini.server"):
        return "Server/MCP imports can require Java-backed searchers, optional Faiss, and source-checkout eval resources; rerun with --check-lucene and --check-faiss, then verify repo-development resource setup if MCP still fails."
    return "Inspect the active environment, reinstall the missing dependency, then retry in a fresh Python process."


def check_distribution(results: list[CheckResult], *, verbose: bool) -> None:
    try:
        version = importlib.metadata.version("pyserini")
    except importlib.metadata.PackageNotFoundError:
        add_result(results, "pyserini-distribution", "FAIL", "pyserini distribution metadata not found", "Install Pyserini into the active environment.")
        return
    status = "PASS" if version == "2.3.0" else "WARN"
    hint = "" if version == "2.3.0" else "This skill was drafted against Pyserini 2.3.0; verify behavior against the installed version."
    add_result(results, "pyserini-distribution", status, f"pyserini {version}", hint)

    module = import_module_check(results, "pyserini", "pyserini-import", verbose=verbose)
    if module is None:
        return
    package_file = getattr(module, "__file__", "") or ""
    editable_hint = "source/editable-style import" if package_file and not "site-packages" in package_file else "installed package import"
    add_result(results, "pyserini-import-location", "INFO", editable_hint)


def check_pyjnius(results: list[CheckResult], *, verbose: bool) -> None:
    if importlib.util.find_spec("jnius_config") is None:
        add_result(results, "pyjnius-config", "FAIL", "jnius_config is not importable", "Reinstall Pyserini dependencies in the active environment.")
        return
    import_module_check(results, "jnius_config", "pyjnius-config", verbose=verbose)
    if importlib.util.find_spec("jnius") is None:
        add_result(results, "pyjnius", "FAIL", "jnius is not importable", "Install PyJNIus through Pyserini dependencies.")
    else:
        add_result(results, "pyjnius", "PASS", "jnius module is discoverable")


def check_core_dependencies(results: list[CheckResult], *, verbose: bool) -> None:
    dependency_modules = [
        ("torch", "torch"),
        ("transformers", "transformers"),
        ("onnxruntime", "onnxruntime"),
        ("fastapi", "fastapi"),
        ("fastmcp", "fastmcp"),
        ("yaml", "pyyaml"),
    ]
    for module_name, distribution_name in dependency_modules:
        try:
            module = importlib.import_module(module_name)
        except Exception as exception:
            add_result(
                results,
                f"dependency:{distribution_name}",
                "FAIL",
                sanitize_message(f"{type(exception).__name__}: {exception}", verbose=verbose),
                "Reinstall Pyserini in a fresh Python 3.12 environment or repair the missing dependency.",
            )
            continue
        version = getattr(module, "__version__", None)
        if version is None:
            try:
                version = importlib.metadata.version(distribution_name)
            except importlib.metadata.PackageNotFoundError:
                version = "version unknown"
        add_result(results, f"dependency:{distribution_name}", "PASS", str(version))

    torch_module = sys.modules.get("torch")
    if torch_module is not None:
        try:
            cuda_available = bool(torch_module.cuda.is_available())
            cuda_version = getattr(torch_module.version, "cuda", None)
            add_result(results, "torch-cuda", "INFO", f"cuda_available={cuda_available}; torch_cuda={cuda_version}")
        except Exception as exception:
            add_result(results, "torch-cuda", "WARN", sanitize_message(exception, verbose=verbose), "Use CPU device flags unless CUDA is confirmed healthy.")


def count_anserini_fatjars(directory_name: str | None) -> int | None:
    if not directory_name:
        return None
    try:
        directory = Path(directory_name).expanduser()
        return len(list(directory.glob("anserini-*-fatjar.jar")))
    except Exception:
        return None


def check_fatjar_hint(results: list[CheckResult]) -> None:
    classpath = os.environ.get("ANSERINI_CLASSPATH")
    classpath_count = count_anserini_fatjars(classpath)
    if classpath:
        if classpath_count and classpath_count > 0:
            add_result(results, "anserini-classpath", "INFO", f"ANSERINI_CLASSPATH is set and contains {classpath_count} matching fatjar(s)")
        else:
            add_result(results, "anserini-classpath", "WARN", "ANSERINI_CLASSPATH is set but no matching fatjar was detected", "Point it to a directory containing anserini-*-fatjar.jar or unset it for packaged resources.")
    else:
        add_result(results, "anserini-classpath", "INFO", "ANSERINI_CLASSPATH is unset; Pyserini will use package resources")

    pyserini_module = sys.modules.get("pyserini")
    package_file = getattr(pyserini_module, "__file__", None) if pyserini_module is not None else None
    if package_file:
        resource_dir = Path(package_file).resolve().parent / "resources" / "jars"
        resource_count = count_anserini_fatjars(str(resource_dir))
        if resource_count and resource_count > 0:
            add_result(results, "packaged-fatjar", "INFO", f"package resources contain {resource_count} matching fatjar(s)")
        else:
            add_result(results, "packaged-fatjar", "WARN", "package resources do not expose an anserini fatjar", "Lucene imports may fail in editable/source installs until Anserini resources are built or configured.")


def check_lucene(results: list[CheckResult], *, verbose: bool) -> None:
    import_module_check(results, "pyserini.search.lucene", "lucene-import", verbose=verbose)


def check_faiss(results: list[CheckResult], *, verbose: bool) -> None:
    faiss_module = import_module_check(results, "faiss", "faiss-import", verbose=verbose)
    if faiss_module is not None:
        gpu_capable = hasattr(faiss_module, "StandardGpuResources")
        add_result(results, "faiss-gpu-capability", "INFO", f"StandardGpuResources={gpu_capable}")
    import_module_check(results, "pyserini.search.faiss", "pyserini-faiss-import", verbose=verbose)


def check_server(results: list[CheckResult], *, verbose: bool) -> None:
    import_module_check(results, "pyserini.server.config", "server-config-import", verbose=verbose)
    import_module_check(results, "pyserini.server.rest.app", "rest-import", verbose=verbose)
    import_module_check(results, "pyserini.server.mcp.mcpyserini", "mcp-import", verbose=verbose)


def run_pip_check(results: list[CheckResult], *, verbose: bool) -> None:
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
    except Exception as exception:
        add_result(results, "pip-check", "WARN", sanitize_message(exception, verbose=verbose), "Run python -m pip check manually in the target environment.")
        return
    output = (completed.stdout or completed.stderr or "").strip()
    if completed.returncode == 0:
        add_result(results, "pip-check", "PASS", output or "No broken requirements found")
    else:
        add_result(results, "pip-check", "FAIL", sanitize_message(output, verbose=verbose), "Resolve dependency conflicts or create a fresh Python 3.12 environment.")


def print_text(results: list[CheckResult]) -> None:
    width = max(len(result.name) for result in results) if results else 10
    for result in results:
        line = f"[{result.status:<4}] {result.name:<{width}}  {result.detail}"
        print(line)
        if result.hint:
            print(f"       hint: {result.hint}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check a Pyserini runtime for Python, Java, PyJNIus, Lucene, Faiss, and server import readiness.",
    )
    parser.add_argument("--check-lucene", action="store_true", help="Import Java-backed Lucene search classes; starts/configures the JVM in this process.")
    parser.add_argument("--check-faiss", action="store_true", help="Import optional Faiss and Pyserini Faiss search modules.")
    parser.add_argument("--check-server", action="store_true", help="Import REST and MCP server modules without starting a server or binding ports.")
    parser.add_argument("--pip-check", action="store_true", help="Run python -m pip check as part of diagnostics.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    parser.add_argument("--verbose", action="store_true", help="Do not redact paths from exception messages.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results: list[CheckResult] = []

    check_python(results)
    check_java(results, verbose=args.verbose)
    check_distribution(results, verbose=args.verbose)
    check_pyjnius(results, verbose=args.verbose)
    check_core_dependencies(results, verbose=args.verbose)
    check_fatjar_hint(results)

    if args.pip_check:
        run_pip_check(results, verbose=args.verbose)
    if args.check_lucene:
        check_lucene(results, verbose=args.verbose)
    if args.check_faiss:
        check_faiss(results, verbose=args.verbose)
    if args.check_server:
        check_server(results, verbose=args.verbose)

    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2, sort_keys=True))
    else:
        print_text(results)

    return 1 if any(result.status == "FAIL" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Diagnostic helper for Stanza's CoreNLP client surface.

Safe default: import checks, Java discovery, classpath / CORENLP_HOME
resolution, and output/property validation. A live CoreNLP server is only
started when --start-server is explicitly provided.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

CORENLP_OUTPUT_VALS = ["conll", "conllu", "json", "serialized", "text", "xml", "inlinexml"]
CORENLP_LANGS = {
    "ar", "arabic", "chinese", "zh", "english", "en", "french", "fr",
    "de", "german", "hu", "hungarian", "it", "italian", "es", "spanish",
}
DEFAULT_ENDPOINT = "http://localhost:9000"
DEFAULT_OUTPUT_FORMAT = "serialized"
DEFAULT_SAMPLE_TEXT = "CoreNLP diagnostic smoke test."

IMPORT_TARGETS = [
    "stanza",
    "stanza.server",
    "stanza.server.client",
    "stanza.resources.installation",
    "stanza.server.tokensregex",
    "stanza.server.semgrex",
    "stanza.server.tsurgeon",
    "stanza.server.ssurgeon",
    "stanza.server.morphology",
]


def discover_repo_root(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / "README.md").exists() and (candidate / "stanza").is_dir():
            return candidate
    return None


REPO_ROOT = discover_repo_root(Path(__file__).resolve().parent)
if REPO_ROOT is not None:
    repo_root_text = str(REPO_ROOT)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def is_corenlp_lang(value: str) -> bool:
    return value.lower() in CORENLP_LANGS


def resolve_classpath(classpath: str | None = None) -> str | None:
    """Mirror stanza.server.client.resolve_classpath closely enough for diagnostics."""
    if classpath == "$CLASSPATH" or (classpath is None and os.getenv("CORENLP_HOME", None) == "$CLASSPATH"):
        return os.getenv("CLASSPATH")
    if classpath is None:
        classpath = os.getenv("CORENLP_HOME", os.path.join(str(Path.home()), "stanza_corenlp"))
        if not os.path.exists(classpath):
            raise FileNotFoundError(
                "Please install CoreNLP by running `stanza.install_corenlp()`. If you have installed it, please define "
                "$CORENLP_HOME to be location of your CoreNLP distribution or pass in a classpath parameter.  "
                f"$CORENLP_HOME={os.getenv('CORENLP_HOME')}"
            )
        classpath = os.path.join(classpath, "*")
    return classpath


def read_corenlp_props(props_path: str) -> dict[str, str]:
    props_dict: dict[str, str] = {}
    with open(props_path, encoding="utf-8") as props_file:
        entry_lines = [
            entry_line
            for entry_line in props_file.read().split("\n")
            if entry_line.strip() and not entry_line.startswith("#")
        ]
        for entry_line in entry_lines:
            key = entry_line.split("=", maxsplit=1)[0]
            key_len = len(key + "=")
            value = entry_line[key_len:]
            props_dict[key.strip()] = value
    return props_dict


def validate_corenlp_props(properties: Any = None, annotators: Any = None, output_format: str | None = None) -> None:
    """Basic CoreNLP property validation, matching the installed package behavior."""
    if output_format and output_format.lower() not in CORENLP_OUTPUT_VALS:
        raise ValueError(
            f"{output_format} not a valid CoreNLP outputFormat value! Choose from: {CORENLP_OUTPUT_VALS}"
        )
    if isinstance(properties, dict):
        if "outputFormat" in properties:
            output_value = properties["outputFormat"]
            if not isinstance(output_value, str) or output_value.lower() not in CORENLP_OUTPUT_VALS:
                raise ValueError(
                    f"{output_value} not a valid CoreNLP outputFormat value! Choose from: {CORENLP_OUTPUT_VALS}"
                )


def normalize_annotators(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    parts = [piece.strip() for piece in re.split(r"[,\s]+", raw.strip()) if piece.strip()]
    if not parts:
        raise ValueError("Annotators were provided but no non-empty values were found.")
    return parts


def parse_properties_source(args: argparse.Namespace) -> tuple[Any, Any, str]:
    if args.language and (args.properties_json or args.properties_file):
        raise ValueError("Use only one of --language, --properties-json, or --properties-file.")
    if args.properties_json and args.properties_file:
        raise ValueError("Use only one of --properties-json or --properties-file.")
    if args.properties_json:
        properties = json.loads(args.properties_json)
        if not isinstance(properties, dict):
            raise ValueError("--properties-json must decode to an object/dict.")
        return properties, properties, "json"
    if args.properties_file:
        props_path = Path(args.properties_file)
        if not props_path.exists():
            raise FileNotFoundError(f"Properties file not found: {props_path}")
        properties = read_corenlp_props(str(props_path))
        return str(props_path), properties, "file"
    if args.language:
        return args.language.strip(), None, "language"
    return None, None, "none"


def check_imports(results: list[CheckResult]) -> dict[str, Any]:
    loaded: dict[str, Any] = {}
    for module_name in IMPORT_TARGETS:
        try:
            loaded[module_name] = importlib.import_module(module_name)
            results.append(CheckResult(f"import {module_name}", True, "ok"))
        except Exception as exc:
            results.append(CheckResult(f"import {module_name}", False, f"{exc.__class__.__name__}: {exc}"))
    return loaded


def check_java(results: list[CheckResult]) -> str | None:
    java_path = shutil.which("java")
    if not java_path:
        results.append(CheckResult("java executable", False, "java was not found on PATH"))
        return None

    try:
        proc = subprocess.run([java_path, "-version"], capture_output=True, text=True, check=False)
        version_text = (proc.stderr or proc.stdout or "").strip().splitlines()
        version_line = version_text[0] if version_text else "java -version produced no output"
        if proc.returncode == 0:
            results.append(CheckResult("java executable", True, f"{java_path} | {version_line}"))
        else:
            results.append(CheckResult("java executable", False, f"{java_path} | exit {proc.returncode} | {version_line}"))
    except Exception as exc:
        results.append(CheckResult("java executable", False, f"{exc.__class__.__name__}: {exc}"))
    return java_path


def check_classpath(results: list[CheckResult], classpath_arg: str | None) -> str | None:
    env_home = os.getenv("CORENLP_HOME")
    env_classpath = os.getenv("CLASSPATH")
    try:
        resolved = resolve_classpath(classpath_arg)
        if resolved is None:
            results.append(
                CheckResult(
                    "classpath resolution",
                    False,
                    f"resolved to None; CORENLP_HOME={env_home!r}, CLASSPATH={env_classpath!r}",
                )
            )
            return None
        results.append(
            CheckResult(
                "classpath resolution",
                True,
                f"{resolved} (CORENLP_HOME={env_home!r}, CLASSPATH={env_classpath!r})",
            )
        )
        return resolved
    except Exception as exc:
        results.append(
            CheckResult(
                "classpath resolution",
                False,
                f"{exc.__class__.__name__}: {exc} (CORENLP_HOME={env_home!r}, CLASSPATH={env_classpath!r})",
            )
        )
        return None


def check_properties(results: list[CheckResult], runtime_properties: Any, validation_properties: Any, annotators: list[str] | None, output_format: str | None) -> None:
    try:
        validate_corenlp_props(properties=validation_properties, annotators=annotators, output_format=output_format)
        if isinstance(runtime_properties, str) and validation_properties is None:
            if not is_corenlp_lang(runtime_properties):
                raise ValueError(f"{runtime_properties} is not a supported CoreNLP language keyword.")
        detail = f"outputFormat={output_format!r}"
        if isinstance(validation_properties, dict) and "outputFormat" in validation_properties:
            detail += f", properties.outputFormat={validation_properties['outputFormat']!r}"
        if annotators:
            detail += f", annotators={','.join(annotators)}"
        results.append(CheckResult("property validation", True, detail))
    except Exception as exc:
        results.append(CheckResult("property validation", False, f"{exc.__class__.__name__}: {exc}"))


def ping_endpoint(results: list[CheckResult], endpoint: str, timeout_seconds: float) -> None:
    url = endpoint.rstrip("/")
    if not url.endswith("/ping"):
        url = f"{url}/ping"
    try:
        request = Request(url)
        with urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8", errors="replace").strip()
            detail = body or f"HTTP {getattr(response, 'status', '200')}"
            results.append(CheckResult(f"ping {url}", True, detail))
    except HTTPError as exc:
        results.append(CheckResult(f"ping {url}", False, f"HTTP {exc.code}: {exc.reason}"))
    except URLError as exc:
        results.append(CheckResult(f"ping {url}", False, f"URLError: {exc.reason}"))
    except Exception as exc:
        results.append(CheckResult(f"ping {url}", False, f"{exc.__class__.__name__}: {exc}"))


def start_server_smoke(
    results: list[CheckResult],
    loaded_modules: dict[str, Any],
    endpoint: str,
    runtime_properties: Any,
    annotators: list[str] | None,
    output_format: str | None,
    classpath_arg: str | None,
    memory: str,
    threads: int,
    timeout_ms: int,
    max_char_length: int,
    preload: bool,
    pretokenized: bool,
    sample_text: str,
    startup_wait_seconds: float,
) -> None:
    server_mod = loaded_modules.get("stanza.server")
    if server_mod is None:
        results.append(CheckResult("live server smoke", False, "stanza.server could not be imported"))
        return

    CoreNLPClient = getattr(server_mod, "CoreNLPClient", None)
    StartServer = getattr(server_mod, "StartServer", None)
    if CoreNLPClient is None or StartServer is None:
        results.append(CheckResult("live server smoke", False, "CoreNLPClient or StartServer is unavailable"))
        return

    parsed = urlparse(endpoint)
    if parsed.hostname not in {"localhost", "127.0.0.1"}:
        results.append(CheckResult("live server smoke", False, f"start-server requires a local endpoint, got {endpoint!r}"))
        return

    try:
        client = CoreNLPClient(
            start_server=StartServer.FORCE_START,
            endpoint=endpoint,
            timeout=timeout_ms,
            threads=threads,
            annotators=annotators,
            pretokenized=pretokenized,
            output_format=output_format,
            properties=runtime_properties,
            memory=memory,
            be_quiet=False,
            max_char_length=max_char_length,
            preload=preload,
            classpath=classpath_arg,
        )
    except Exception as exc:
        results.append(CheckResult("live server smoke", False, f"client setup failed: {exc.__class__.__name__}: {exc}"))
        return

    started = False
    try:
        client.start()
        deadline = time.monotonic() + startup_wait_seconds
        while time.monotonic() < deadline:
            try:
                if client.is_alive():
                    started = True
                    break
            except Exception:
                pass
            time.sleep(1)

        if not started:
            results.append(CheckResult("live server smoke", False, f"server did not answer /ping within {startup_wait_seconds} seconds"))
            return

        if sample_text:
            try:
                ann = client.annotate(sample_text, output_format=output_format)
                results.append(CheckResult("live annotate smoke", True, f"returned {type(ann).__name__}"))
            except Exception as exc:
                results.append(CheckResult("live annotate smoke", False, f"{exc.__class__.__name__}: {exc}"))
        else:
            results.append(CheckResult("live server smoke", True, "server answered /ping"))
    except Exception as exc:
        results.append(CheckResult("live server smoke", False, f"{exc.__class__.__name__}: {exc}"))
    finally:
        try:
            client.stop()
        except Exception:
            pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check Stanza CoreNLP client imports, Java, classpath, and optional endpoint health.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--classpath", default=None, help="Explicit CoreNLP classpath or $CLASSPATH")
    props_group = parser.add_mutually_exclusive_group()
    props_group.add_argument("--language", default=None, help="CoreNLP language keyword such as english, german, or en")
    props_group.add_argument("--properties-file", default=None, help="Path to a CoreNLP properties file")
    props_group.add_argument("--properties-json", default=None, help="Inline JSON object with CoreNLP properties")
    parser.add_argument("--annotators", default=None, help="Comma or whitespace separated annotator list")
    parser.add_argument("--output-format", default=DEFAULT_OUTPUT_FORMAT, help=f"CoreNLP outputFormat to validate ({', '.join(CORENLP_OUTPUT_VALS)})")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="CoreNLP endpoint to ping or start")
    parser.add_argument("--ping", action="store_true", help="Ping the endpoint without starting a server")
    parser.add_argument("--ping-timeout", type=float, default=5.0, help="Timeout in seconds for --ping")
    parser.add_argument("--start-server", action="store_true", help="Explicitly start a local CoreNLP server for a tiny smoke check")
    parser.add_argument("--sample-text", default=DEFAULT_SAMPLE_TEXT, help="Text to annotate when --start-server is used")
    parser.add_argument("--memory", default="2G", help="JVM memory setting for --start-server")
    parser.add_argument("--threads", type=int, default=1, help="Server thread count for --start-server")
    parser.add_argument("--timeout-ms", type=int, default=15000, help="CoreNLP server timeout parameter for --start-server")
    parser.add_argument("--max-char-length", type=int, default=20000, help="Maximum document length for --start-server")
    parser.add_argument("--preload", action=argparse.BooleanOptionalAction, default=False, help="Preload annotators when starting a server")
    parser.add_argument("--pretokenized", action="store_true", default=False, help="Tell CoreNLP the input is pretokenized")
    parser.add_argument("--startup-wait-seconds", type=float, default=10.0, help="How long to wait for a live server ping when --start-server is used")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    results: list[CheckResult] = []
    loaded_modules = check_imports(results)
    java_path = check_java(results)

    annotators = normalize_annotators(args.annotators)
    try:
        runtime_properties, validation_properties, _source = parse_properties_source(args)
    except Exception as exc:
        results.append(CheckResult("property source", False, f"{exc.__class__.__name__}: {exc}"))
        runtime_properties, validation_properties = None, None

    if annotators and validation_properties is not None and isinstance(validation_properties, dict):
        dict_annotators = validation_properties.get("annotators")
        if dict_annotators and isinstance(dict_annotators, str):
            dict_annotators_display = dict_annotators
        elif dict_annotators and isinstance(dict_annotators, list):
            dict_annotators_display = ",".join(dict_annotators)
        else:
            dict_annotators_display = None
        if dict_annotators_display and dict_annotators_display != ",".join(annotators):
            results.append(
                CheckResult(
                    "property note",
                    True,
                    f"explicit annotators override properties annotators ({dict_annotators_display!r} -> {','.join(annotators)!r})",
                )
            )

    if isinstance(validation_properties, dict) and "outputFormat" in validation_properties:
        dict_output = validation_properties["outputFormat"]
        if isinstance(dict_output, str) and dict_output.lower() != args.output_format.lower():
            results.append(
                CheckResult(
                    "property note",
                    True,
                    f"explicit --output-format overrides properties outputFormat ({dict_output!r} -> {args.output_format!r})",
                )
            )

    check_properties(results, runtime_properties, validation_properties, annotators, args.output_format)
    check_classpath(results, args.classpath)

    if args.ping:
        ping_endpoint(results, args.endpoint, args.ping_timeout)

    if args.start_server:
        start_server_smoke(
            results,
            loaded_modules,
            args.endpoint,
            runtime_properties,
            annotators,
            args.output_format,
            args.classpath,
            args.memory,
            args.threads,
            args.timeout_ms,
            args.max_char_length,
            args.preload,
            args.pretokenized,
            args.sample_text,
            args.startup_wait_seconds,
        )

    for result in results:
        prefix = "[ok]" if result.ok else "[fail]"
        print(f"{prefix} {result.name}: {result.detail}")

    failures = [result for result in results if not result.ok]
    print(f"summary: {len(results) - len(failures)} passed, {len(failures)} failed")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

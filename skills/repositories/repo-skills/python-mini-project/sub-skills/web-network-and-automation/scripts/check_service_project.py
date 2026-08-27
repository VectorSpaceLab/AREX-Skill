#!/usr/bin/env python3
"""Static checker for python-mini-project service and automation folders.

Safe by default: this script reads files and parses Python AST only. It does not
import project modules, start servers, open sockets, call HTTP APIs, send email,
scan ports, or execute repository code.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

IGNORE_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    ".ipynb_checkpoints",
}
GENERATED_DIR_NAMES = {"skills"}

CREDENTIAL_NAME_RE = re.compile(
    r"(api[_-]?key|token|secret|password|passwd|pwd|credential|auth|authorization|client[_-]?secret)",
    re.IGNORECASE,
)
PORT_NAME_RE = re.compile(r"(^|_)(port)(_|$)", re.IGNORECASE)
HOST_NAME_RE = re.compile(r"(^|_)(host|hostname)(_|$)", re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s'\"<>]+")
COMMAND_DANGER_RE = re.compile(
    r"\b(shutdown|reboot|poweroff|halt|rm\s+-rf|del\s+/|format\b)\b", re.IGNORECASE
)
NETWORK_COMMAND_RE = re.compile(r"\b(nslookup|ping|curl|wget|pg_dump)\b", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"(your|enter|placeholder|changeme|api key here|password)", re.IGNORECASE)

SEVERITY_ORDER = {"info": 0, "warning": 1, "danger": 2}


@dataclass
class Finding:
    severity: str
    kind: str
    message: str
    file: str
    line: int

    def as_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "kind": self.kind,
            "message": self.message,
            "file": self.file,
            "line": self.line,
        }


@dataclass
class FileReport:
    path: str
    parsed: bool
    error: Optional[str] = None
    imports: Set[str] = field(default_factory=set)
    frameworks: Set[str] = field(default_factory=set)
    ports: Set[str] = field(default_factory=set)
    hosts: Set[str] = field(default_factory=set)
    endpoints: Set[str] = field(default_factory=set)
    credential_needs: Set[str] = field(default_factory=set)
    generated_files: Set[str] = field(default_factory=set)
    findings: List[Finding] = field(default_factory=list)


class StaticVisitor(ast.NodeVisitor):
    """AST visitor that records service, network, credential, and host hazards."""

    def __init__(self, rel_file: str, text: str) -> None:
        self.rel_file = rel_file
        self.text = text
        self.report = FileReport(path=rel_file, parsed=True)
        self.function_depth = 0
        self.class_depth = 0
        self.main_guard_depth = 0
        self.local_functions: Set[str] = set()
        self.constants: Dict[str, Any] = {}

    def visit_Module(self, node: ast.Module) -> Any:  # noqa: ANN401 - ast visitor protocol
        for stmt in node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.local_functions.add(stmt.name)
            if isinstance(stmt, ast.ClassDef):
                self.local_functions.add(stmt.name)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> Any:  # noqa: ANN401
        for alias in node.names:
            self._record_import(alias.name, node.lineno)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:  # noqa: ANN401
        module = node.module or ""
        self._record_import(module, node.lineno)
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> Any:  # noqa: ANN401
        is_main = self._is_main_guard(node.test)
        if is_main:
            self.main_guard_depth += 1
        for stmt in node.body:
            self.visit(stmt)
        if is_main:
            self.main_guard_depth -= 1
        for stmt in node.orelse:
            self.visit(stmt)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:  # noqa: ANN401
        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:  # noqa: ANN401
        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:  # noqa: ANN401
        self.class_depth += 1
        self.generic_visit(node)
        self.class_depth -= 1

    def visit_Assign(self, node: ast.Assign) -> Any:  # noqa: ANN401
        value = literal_value(node.value)
        for target in node.targets:
            for name in extract_target_names(target):
                self._record_assignment(name, value, node.lineno)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:  # noqa: ANN401
        value = literal_value(node.value) if node.value is not None else None
        for name in extract_target_names(node.target):
            self._record_assignment(name, value, node.lineno)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> Any:  # noqa: ANN401
        if isinstance(node.value, str):
            self._record_string(node.value, node.lineno)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Any:  # noqa: ANN401
        func = call_name(node.func)
        lower = func.lower()
        top_level = self.function_depth == 0 and self.main_guard_depth == 0
        guarded_top_level = self.function_depth == 0 and self.main_guard_depth > 0

        if func in self.local_functions and top_level:
            severity = "danger" if "shutdown" in func.lower() else "warning"
            self.add_finding(
                severity,
                "top-level local call",
                f"Top-level call to local function {func}() executes project code during import/script load.",
                node.lineno,
            )

        self._record_framework_call(func, node)
        self._record_socket_call(func, lower, node, top_level, guarded_top_level)
        self._record_http_call(func, lower, node, top_level)
        self._record_email_call(func, lower, node, top_level)
        self._record_automation_call(func, lower, node, top_level)
        self._record_system_call(func, lower, node, top_level)
        self._record_database_call(func, lower, node, top_level)
        self._record_env_call(func, lower, node)
        self._record_interactive_call(func, lower, node, top_level)

        self.generic_visit(node)

    def _record_import(self, module: str, line: int) -> None:
        if not module:
            return
        base = module.split(".")[0]
        self.report.imports.add(module)
        if base == "flask":
            self.report.frameworks.add("Flask")
        elif base == "fastapi":
            self.report.frameworks.add("FastAPI")
        elif base == "uvicorn":
            self.report.frameworks.add("Uvicorn")
        elif base == "socket":
            self.add_finding("info", "socket import", "Imports socket; inspect bind/connect behavior before running.", line)
        elif base in {"requests", "httpx", "urllib", "feedparser", "wikipedia"}:
            self.add_finding("info", "network client import", f"Imports {module}; live runs may call external network resources.", line)
        elif base in {"smtplib", "imaplib"}:
            self.add_finding("warning", "email import", f"Imports {module}; email credentials or inbox/server access may be required.", line)
        elif base in {"pyautogui", "keyboard", "pywhatkit", "webbrowser", "speech_recognition", "pyttsx3", "spotipy"}:
            self.add_finding("warning", "desktop automation import", f"Imports {module}; runtime may control browser, keyboard, audio, or desktop state.", line)
        elif base in {"pexpect", "subprocess"}:
            self.add_finding("info", "subprocess import", f"Imports {module}; inspect command execution before running.", line)

    def _record_assignment(self, name: str, value: Any, line: int) -> None:
        if isinstance(value, (str, int, float, bool)) or value is None:
            self.constants[name] = value
        if PORT_NAME_RE.search(name) and isinstance(value, int):
            self.report.ports.add(f"{value} ({name} at {self.rel_file}:{line})")
        if HOST_NAME_RE.search(name) and isinstance(value, str):
            self.report.hosts.add(f"{value!r} ({name} at {self.rel_file}:{line})")
        if CREDENTIAL_NAME_RE.search(name):
            if isinstance(value, str) and PLACEHOLDER_RE.search(value):
                detail = f"{name} appears to contain a placeholder secret"
            elif value in ("", None):
                detail = f"{name} is an empty or unset credential field"
            else:
                detail = f"{name} is credential-like"
            self.report.credential_needs.add(f"{detail} ({self.rel_file}:{line})")
            self.add_finding("warning", "credential variable", detail, line)

    def _record_string(self, value: str, line: int) -> None:
        for url in URL_RE.findall(value):
            self.report.endpoints.add(f"{url} ({self.rel_file}:{line})")
            port_match = re.search(r":(\d{2,5})(?:/|$)", url)
            if port_match:
                self.report.ports.add(f"{port_match.group(1)} (URL at {self.rel_file}:{line})")
        if "bearer" in value.lower() or "authorization" in value.lower():
            self.report.credential_needs.add(f"authorization header/token string ({self.rel_file}:{line})")
        if COMMAND_DANGER_RE.search(value):
            self.add_finding("danger", "destructive command string", f"Destructive host command string detected: {shorten(value)}", line)
        elif NETWORK_COMMAND_RE.search(value):
            self.add_finding("warning", "network/system command string", f"Network/system command string detected: {shorten(value)}", line)

    def _record_framework_call(self, func: str, node: ast.Call) -> None:
        if func.endswith("Flask") or func == "Flask":
            self.report.frameworks.add("Flask")
        if func.endswith("FastAPI") or func == "FastAPI":
            self.report.frameworks.add("FastAPI")
        if func.endswith("Jinja2Templates"):
            self.add_finding("info", "template cwd", "Jinja2Templates path is usually cwd-relative; run from the app folder.", node.lineno)
        if func.endswith(".route") or func.endswith(".get") or func.endswith(".post"):
            route = first_string_arg(node)
            if route and route.startswith("/"):
                self.add_finding("info", "web route", f"Defines web route {route!r}.", node.lineno)
        if func.endswith("run") and (func == "app.run" or func.endswith(".run")):
            if "uvicorn" in func.lower() or func == "app.run" or func.endswith("app.run"):
                port = kw_value(node, "port")
                host = kw_value(node, "host")
                if isinstance(port, int):
                    self.report.ports.add(f"{port} ({func} at {self.rel_file}:{node.lineno})")
                if isinstance(host, str):
                    self.report.hosts.add(f"{host!r} ({func} at {self.rel_file}:{node.lineno})")
                severity = "danger" if self.function_depth == 0 and self.main_guard_depth == 0 else "warning"
                self.add_finding(severity, "server startup", f"Server startup call {func} detected.", node.lineno)

    def _record_socket_call(self, func: str, lower: str, node: ast.Call, top_level: bool, guarded_top_level: bool) -> None:
        if lower in {"socket.socket", "socket.create_connection"} or lower.endswith(".socket"):
            self.add_finding("info", "socket creation", f"Socket creation call {func} detected.", node.lineno)
        if lower.endswith(".bind"):
            for port in ports_from_call(node, self.constants):
                self.report.ports.add(f"{port} (socket bind at {self.rel_file}:{node.lineno})")
            severity = "danger" if top_level else "warning"
            self.add_finding(severity, "socket bind", "Socket bind can open a listening local port.", node.lineno)
        if lower.endswith(".listen"):
            severity = "danger" if top_level else "warning"
            self.add_finding(severity, "socket listen", "Socket listen starts accepting network connections.", node.lineno)
        if lower.endswith(".accept"):
            self.add_finding("warning", "socket accept", "Socket accept may block indefinitely; use timeouts in tests.", node.lineno)
        if lower == "socket.create_connection" or (lower.endswith(".connect") and "socket" in self.report.imports):
            for port in ports_from_call(node, self.constants):
                self.report.ports.add(f"{port} (socket connect at {self.rel_file}:{node.lineno})")
            self.add_finding("warning", "socket connect", "Socket connect attempts outbound/local network communication.", node.lineno)
        if guarded_top_level and (lower.endswith(".bind") or lower.endswith(".listen")):
            self.add_finding("info", "guarded socket server", "Socket server is guarded by __main__ but still long-running when executed.", node.lineno)

    def _record_http_call(self, func: str, lower: str, node: ast.Call, top_level: bool) -> None:
        http_funcs = {"requests.get", "requests.post", "requests.put", "requests.delete", "requests.patch", "requests.request", "httpx.get", "httpx.post", "urllib.request.urlopen"}
        if lower in http_funcs or lower.endswith(".urlopen"):
            url = first_string_arg(node)
            if url:
                self.report.endpoints.add(f"{url} ({self.rel_file}:{node.lineno})")
            severity = "danger" if top_level else "warning"
            self.add_finding(severity, "http request", f"HTTP client call {func} detected; mock or use a fixture by default.", node.lineno)
        if lower == "feedparser.parse" or lower.endswith(".parse") and "feedparser" in self.report.imports:
            severity = "danger" if top_level else "warning"
            self.add_finding(severity, "rss/network parse", "feedparser.parse may fetch remote RSS data for URL inputs.", node.lineno)
        if "wikipedia.summary" in lower:
            self.add_finding("warning", "external api", "Wikipedia summary call uses external network service.", node.lineno)

    def _record_email_call(self, func: str, lower: str, node: ast.Call, top_level: bool) -> None:
        if lower in {"smtplib.smtp", "smtplib.smtp_ssl"} or lower.endswith("smtp") or lower.endswith("smtp_ssl"):
            host = first_string_arg(node)
            if host:
                self.report.endpoints.add(f"SMTP {host} ({self.rel_file}:{node.lineno})")
            self.report.credential_needs.add(f"SMTP account/password ({self.rel_file}:{node.lineno})")
            severity = "danger" if top_level else "warning"
            self.add_finding(severity, "smtp client", "SMTP client creation can send real email after login/sendmail.", node.lineno)
        if lower.endswith(".starttls"):
            self.add_finding("info", "smtp tls", "SMTP STARTTLS call detected.", node.lineno)
        if lower.endswith(".login"):
            self.report.credential_needs.add(f"login credentials ({self.rel_file}:{node.lineno})")
            severity = "danger" if top_level else "warning"
            self.add_finding(severity, "login call", f"Credentialed login call {func} detected.", node.lineno)
        if lower.endswith(".sendmail"):
            severity = "danger" if top_level else "warning"
            self.add_finding(severity, "email send", "sendmail call can send real email.", node.lineno)
        if lower == "imaplib.imap4_ssl" or lower.endswith("imap4_ssl"):
            host = first_string_arg(node)
            if host:
                self.report.endpoints.add(f"IMAP {host} ({self.rel_file}:{node.lineno})")
            self.report.credential_needs.add(f"IMAP account/password ({self.rel_file}:{node.lineno})")
            severity = "danger" if top_level else "warning"
            self.add_finding(severity, "imap client", "IMAP SSL connection can access a real inbox.", node.lineno)

    def _record_automation_call(self, func: str, lower: str, node: ast.Call, top_level: bool) -> None:
        if lower.startswith("pywhatkit."):
            self.report.credential_needs.add(f"WhatsApp/browser session or external media/browser state ({self.rel_file}:{node.lineno})")
            severity = "danger" if any(token in lower for token in ["sendwhat", "image"]) else "warning"
            self.add_finding(severity, "messaging/browser automation", f"pywhatkit call {func} can open browser or send messages.", node.lineno)
        if lower.startswith("pyautogui.") or lower.startswith("pyg."):
            severity = "danger" if any(token in lower for token in ["typewrite", "press", "click", "hotkey", "write"]) else "warning"
            self.add_finding(severity, "gui automation", f"GUI automation call {func} can affect the focused application.", node.lineno)
        if lower.startswith("keyboard.") or lower.startswith("kbd."):
            self.add_finding("warning", "keyboard hook", f"Keyboard library call {func} requires desktop input focus/permissions.", node.lineno)
        if lower == "webbrowser.open" or lower.endswith(".open") and "webbrowser" in self.report.imports:
            self.add_finding("warning", "browser automation", "webbrowser.open can launch or navigate a browser.", node.lineno)
        if lower.startswith("pyttsx3.init") or lower.endswith("microphone") or "recognize_google" in lower:
            self.add_finding("warning", "audio/speech automation", f"Audio/speech call {func} needs desktop hardware or external speech service.", node.lineno)
        if "spotifyoauth" in lower:
            self.report.credential_needs.add(f"Spotify OAuth credentials ({self.rel_file}:{node.lineno})")
            self.add_finding("warning", "oauth client", "Spotify OAuth client detected.", node.lineno)

    def _record_system_call(self, func: str, lower: str, node: ast.Call, top_level: bool) -> None:
        if lower in {"os.system", "os.popen", "subprocess.call", "subprocess.run", "subprocess.popen", "pexpect.spawn"}:
            command = first_string_arg(node) or ""
            if command:
                if COMMAND_DANGER_RE.search(command):
                    self.add_finding("danger", "destructive host command", f"Host command may be destructive: {shorten(command)}", node.lineno)
                elif NETWORK_COMMAND_RE.search(command):
                    self.add_finding("warning", "network/system command", f"Command may access network/system resources: {shorten(command)}", node.lineno)
                else:
                    severity = "warning" if top_level else "info"
                    self.add_finding(severity, "system command", f"System command execution: {shorten(command)}", node.lineno)
            else:
                severity = "warning" if top_level else "info"
                self.add_finding(severity, "system command", f"Dynamic command execution via {func}; inspect arguments.", node.lineno)
            if lower == "pexpect.spawn" and command and "pg_dump" in command:
                self.report.credential_needs.add(f"PostgreSQL credentials for pg_dump ({self.rel_file}:{node.lineno})")
                self.report.generated_files.add(f"SQL dump file in cwd ({self.rel_file}:{node.lineno})")
        if lower == "os.startfile":
            self.add_finding("warning", "windows-only launch", "os.startfile is Windows-only and opens local applications/files.", node.lineno)
        if lower == "os.chdir":
            target = first_string_arg(node)
            msg = "os.chdir changes process cwd; relative file outputs may move unexpectedly."
            if target and ("C:" in target or "Desktop" in target):
                msg = "os.chdir targets a Windows/Desktop path; platform-specific file output likely."
            self.add_finding("warning", "cwd mutation", msg, node.lineno)

    def _record_database_call(self, func: str, lower: str, node: ast.Call, top_level: bool) -> None:
        if lower == "sqlite3.connect" or lower.endswith("create_engine"):
            db = first_string_arg(node)
            if db:
                self.report.generated_files.add(f"database {db!r} ({self.rel_file}:{node.lineno})")
            severity = "warning" if top_level else "info"
            self.add_finding(severity, "database access", f"Database connection/create call {func} may create or mutate local DB files.", node.lineno)
        if lower.endswith("create_all"):
            self.add_finding("warning", "database schema creation", "create_all can create database tables, often at import time.", node.lineno)

    def _record_env_call(self, func: str, lower: str, node: ast.Call) -> None:
        if lower in {"os.environ.get", "os.getenv"}:
            key = first_string_arg(node)
            if key:
                self.report.credential_needs.add(f"environment variable {key} ({self.rel_file}:{node.lineno})")

    def _record_interactive_call(self, func: str, lower: str, node: ast.Call, top_level: bool) -> None:
        if lower == "input":
            severity = "warning" if top_level else "info"
            self.add_finding(severity, "interactive input", "input() requires an interactive terminal; avoid in automated checks.", node.lineno)
        if lower in {"open", "pathlib.path.open"}:
            mode = open_mode(node)
            if mode and any(ch in mode for ch in "wax+"):
                path_arg = first_string_arg(node)
                target = path_arg or "dynamic path"
                self.report.generated_files.add(f"write/open {target!r} mode {mode!r} ({self.rel_file}:{node.lineno})")
                self.add_finding("warning", "file write", f"File open in write/append mode for {target!r}.", node.lineno)

    def add_finding(self, severity: str, kind: str, message: str, line: int) -> None:
        self.report.findings.append(Finding(severity, kind, message, self.rel_file, line))

    @staticmethod
    def _is_main_guard(test: ast.AST) -> bool:
        if not isinstance(test, ast.Compare):
            return False
        if not isinstance(test.left, ast.Name) or test.left.id != "__name__":
            return False
        if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
            return False
        if len(test.comparators) != 1:
            return False
        comp = literal_value(test.comparators[0])
        return comp == "__main__"


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return call_name(node.func)
    return ""


def extract_target_names(node: ast.AST) -> Iterable[str]:
    if isinstance(node, ast.Name):
        yield node.id
    elif isinstance(node, ast.Attribute):
        yield node.attr
    elif isinstance(node, (ast.Tuple, ast.List)):
        for elt in node.elts:
            yield from extract_target_names(elt)


def literal_value(node: Optional[ast.AST]) -> Any:
    if node is None:
        return None
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts: List[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            else:
                parts.append("{...}")
        return "".join(parts)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = literal_value(node.operand)
        if isinstance(value, (int, float)):
            return -value
    return None


def first_string_arg(node: ast.Call) -> Optional[str]:
    if node.args:
        value = literal_value(node.args[0])
        if isinstance(value, str):
            return value
    return None


def kw_value(node: ast.Call, name: str) -> Any:
    for kw in node.keywords:
        if kw.arg == name:
            return literal_value(kw.value)
    return None


def open_mode(node: ast.Call) -> Optional[str]:
    if len(node.args) >= 2:
        mode = literal_value(node.args[1])
        if isinstance(mode, str):
            return mode
    return kw_value(node, "mode") if isinstance(kw_value(node, "mode"), str) else None


def ports_from_call(node: ast.Call, constants: Dict[str, Any]) -> Set[int]:
    ports: Set[int] = set()

    def walk(value: ast.AST) -> None:
        lit = literal_value(value)
        if isinstance(lit, int) and 0 < lit < 65536:
            ports.add(lit)
            return
        if isinstance(value, ast.Name):
            const = constants.get(value.id)
            if isinstance(const, int) and 0 < const < 65536:
                ports.add(const)
        elif isinstance(value, (ast.Tuple, ast.List)):
            for elt in value.elts:
                walk(elt)
        elif isinstance(value, ast.Dict):
            for elt in list(value.keys) + list(value.values):
                if elt is not None:
                    walk(elt)

    for arg in node.args:
        walk(arg)
    for kw in node.keywords:
        walk(kw.value)
    return ports


def shorten(text: str, width: int = 100) -> str:
    compact = " ".join(str(text).split())
    if len(compact) <= width:
        return compact
    return compact[: width - 3] + "..."


def read_text_best_effort(path: Path) -> Tuple[Optional[str], Optional[str]]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        return None, str(exc)
    for encoding in ("utf-8-sig", "utf-16", "utf-16le", "latin-1"):
        try:
            return data.decode(encoding), None
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), None


def should_skip(path: Path, include_generated: bool) -> bool:
    names = set(path.parts)
    if names & IGNORE_DIR_NAMES:
        return True
    if not include_generated and names & GENERATED_DIR_NAMES:
        return True
    return False


def iter_python_files(target: Path, include_generated: bool) -> Iterable[Path]:
    if target.is_file():
        if target.suffix == ".py":
            yield target
        return
    for root, dirs, files in os.walk(target):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if not should_skip(root_path / d, include_generated)]
        for name in files:
            path = root_path / name
            if path.suffix == ".py" and not should_skip(path, include_generated):
                yield path


def collect_requirement_clues(target: Path, include_generated: bool) -> List[Dict[str, Any]]:
    clues: List[Dict[str, Any]] = []
    roots = [target] if target.is_dir() else [target.parent]
    for root in roots:
        for filename in ("requirements.txt", "pyproject.toml"):
            for path in root.rglob(filename):
                if should_skip(path, include_generated):
                    continue
                text, error = read_text_best_effort(path)
                item: Dict[str, Any] = {"path": str(path), "kind": filename}
                if error:
                    item["error"] = error
                elif text is not None:
                    deps = parse_dependency_lines(filename, text)
                    item["dependencies"] = deps[:80]
                    if len(deps) > 80:
                        item["truncated_dependency_count"] = len(deps) - 80
                    if "\x00" in text:
                        item["warning"] = "file contains null bytes; check encoding before pip install"
                clues.append(item)
    return clues


def parse_dependency_lines(filename: str, text: str) -> List[str]:
    deps: List[str] = []
    if filename == "requirements.txt":
        for line in text.splitlines():
            clean = line.strip().replace("\x00", "")
            if clean and not clean.startswith("#"):
                deps.append(clean)
    else:
        in_dependencies = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("dependencies") and "[" in stripped:
                in_dependencies = True
                continue
            if in_dependencies:
                if stripped.startswith("]"):
                    break
                dep = stripped.strip(",").strip('"').strip("'")
                if dep:
                    deps.append(dep)
    return deps


def relative_display(path: Path, base: Path) -> str:
    try:
        rel = path.relative_to(base)
    except ValueError:
        return str(path)
    text = str(rel)
    return text if text else "."


def analyze_file(path: Path, base: Path) -> FileReport:
    rel = relative_display(path, base)
    text, error = read_text_best_effort(path)
    if error or text is None:
        return FileReport(path=rel, parsed=False, error=error or "unreadable")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        return FileReport(path=rel, parsed=False, error=f"SyntaxError: {exc.msg} at line {exc.lineno}")
    visitor = StaticVisitor(rel, text)
    visitor.visit(tree)
    return visitor.report


def merge_reports(target: Path, base: Path, file_reports: List[FileReport], requirement_clues: List[Dict[str, Any]]) -> Dict[str, Any]:
    frameworks: Set[str] = set()
    imports: Set[str] = set()
    ports: Set[str] = set()
    hosts: Set[str] = set()
    endpoints: Set[str] = set()
    credentials: Set[str] = set()
    generated_files: Set[str] = set()
    findings: List[Dict[str, Any]] = []
    parse_errors: List[Dict[str, Any]] = []

    for report in file_reports:
        if not report.parsed:
            parse_errors.append({"file": report.path, "error": report.error})
            continue
        frameworks.update(report.frameworks)
        imports.update(report.imports)
        ports.update(report.ports)
        hosts.update(report.hosts)
        endpoints.update(report.endpoints)
        credentials.update(report.credential_needs)
        generated_files.update(report.generated_files)
        findings.extend(f.as_dict() for f in report.findings)

    highest = "none"
    for finding in findings:
        sev = finding["severity"]
        if highest == "none" or SEVERITY_ORDER[sev] > SEVERITY_ORDER.get(highest, -1):
            highest = sev

    target_display = relative_display(target, base)
    return {
        "target": target_display or ".",
        "files_scanned": len(file_reports),
        "parse_errors": parse_errors,
        "frameworks": sorted(frameworks),
        "imports": sorted(imports),
        "ports": sorted(ports),
        "hosts": sorted(hosts),
        "endpoints": sorted(endpoints),
        "credential_needs": sorted(credentials),
        "generated_files_or_side_effects": sorted(generated_files),
        "requirement_clues": requirement_clues,
        "highest_severity": highest,
        "findings": sorted(findings, key=lambda f: (SEVERITY_ORDER[f["severity"]], f["file"], f["line"], f["kind"]), reverse=True),
    }


def analyze_target(target: Path, include_generated: bool) -> Dict[str, Any]:
    target = target.resolve()
    base = target.parent if target.is_dir() else target.parent
    files = sorted(iter_python_files(target, include_generated))
    file_reports = [analyze_file(path, base) for path in files]
    requirement_clues = collect_requirement_clues(target, include_generated)
    return merge_reports(target, base, file_reports, requirement_clues)


def print_text_report(results: List[Dict[str, Any]], max_findings: int) -> None:
    print("Static service/automation scan (no imports, no network calls, no project code execution)")
    for result in results:
        print("\n" + "=" * 78)
        print(f"Target: {result['target']}")
        print(f"Files scanned: {result['files_scanned']} | Highest severity: {result['highest_severity']}")
        if result["parse_errors"]:
            print("Parse/read errors:")
            for item in result["parse_errors"]:
                print(f"  - {item['file']}: {item['error']}")
        print_list("Frameworks", result["frameworks"])
        print_list("Ports/bindings", result["ports"])
        print_list("Hosts", result["hosts"])
        print_list("Endpoints", result["endpoints"], limit=12)
        print_list("Credential/config needs", result["credential_needs"], limit=16)
        print_list("Generated files or side effects", result["generated_files_or_side_effects"], limit=16)
        if result["requirement_clues"]:
            print("Requirement clues:")
            for clue in result["requirement_clues"][:8]:
                deps = ", ".join(clue.get("dependencies", [])[:12])
                more = " ..." if clue.get("truncated_dependency_count") else ""
                warn = f" [{clue['warning']}]" if clue.get("warning") else ""
                err = f" ERROR: {clue['error']}" if clue.get("error") else ""
                print(f"  - {clue['path']}: {deps}{more}{warn}{err}")
        findings = result["findings"]
        if not findings:
            print("Findings: none")
        else:
            print(f"Findings (showing up to {max_findings}):")
            for finding in findings[:max_findings]:
                print(
                    f"  - [{finding['severity']}] {finding['kind']} "
                    f"{finding['file']}:{finding['line']} — {finding['message']}"
                )
            if len(findings) > max_findings:
                print(f"  ... {len(findings) - max_findings} more findings; use --json for full detail")


def print_list(title: str, values: Sequence[str], limit: int = 10) -> None:
    if not values:
        print(f"{title}: none detected")
        return
    print(f"{title}:")
    for value in values[:limit]:
        print(f"  - {value}")
    if len(values) > limit:
        print(f"  ... {len(values) - limit} more")


def should_fail(results: List[Dict[str, Any]], threshold: str) -> bool:
    if threshold == "none":
        return False
    min_level = SEVERITY_ORDER[threshold]
    for result in results:
        highest = result.get("highest_severity", "none")
        if highest != "none" and SEVERITY_ORDER[highest] >= min_level:
            return True
    return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Statically detect Flask/FastAPI/socket/email/HTTP/automation/host hazards "
            "in python-mini-project service folders without executing project code."
        )
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Project folder(s) or Python file(s) to scan. Pass repo-relative or absolute paths.",
    )
    parser.add_argument("--json", action="store_true", help="Emit full JSON instead of the text summary.")
    parser.add_argument(
        "--max-findings",
        type=int,
        default=40,
        help="Maximum findings per target in text mode (default: 40). JSON always includes all findings.",
    )
    parser.add_argument(
        "--include-generated",
        action="store_true",
        help="Include generated skills/ artifacts if the scan target contains a skills directory. Default skips them.",
    )
    parser.add_argument(
        "--fail-on",
        choices=["none", "info", "warning", "danger"],
        default="none",
        help="Exit nonzero if any target has at least this severity. Default: none.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    results: List[Dict[str, Any]] = []
    for raw in args.paths:
        path = Path(raw)
        if not path.exists():
            results.append(
                {
                    "target": raw,
                    "files_scanned": 0,
                    "parse_errors": [{"file": raw, "error": "path does not exist"}],
                    "frameworks": [],
                    "imports": [],
                    "ports": [],
                    "hosts": [],
                    "endpoints": [],
                    "credential_needs": [],
                    "generated_files_or_side_effects": [],
                    "requirement_clues": [],
                    "highest_severity": "danger",
                    "findings": [
                        {
                            "severity": "danger",
                            "kind": "missing path",
                            "message": "Scan path does not exist.",
                            "file": raw,
                            "line": 0,
                        }
                    ],
                }
            )
            continue
        results.append(analyze_target(path, args.include_generated))

    if args.json:
        json.dump({"safe_default": True, "executed_project_code": False, "results": results}, sys.stdout, indent=2)
        print()
    else:
        print_text_report(results, max(1, args.max_findings))

    return 1 if should_fail(results, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())

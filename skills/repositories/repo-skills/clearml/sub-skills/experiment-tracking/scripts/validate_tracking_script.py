#!/usr/bin/env python3
"""Statically review a Python file for likely ClearML tracking issues."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class Finding:
    severity: str
    line: int
    code: str
    message: str
    suggestion: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "line": self.line,
            "code": self.code,
            "message": self.message,
            "suggestion": self.suggestion,
        }


class ClearMLTrackingAnalyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.clearml_modules: set[str] = set()
        self.task_aliases: set[str] = set()
        self.task_types_aliases: set[str] = set()
        self.logger_aliases: set[str] = set()
        self.output_model_aliases: set[str] = set()
        self.input_model_aliases: set[str] = set()
        self.task_variables: set[str] = set()
        self.logger_variables: set[str] = set()
        self.output_model_variables: set[str] = set()
        self.findings: list[Finding] = []
        self.task_init_calls: list[ast.Call] = []
        self.task_create_calls: list[ast.Call] = []
        self.task_close_calls: list[ast.Call] = []
        self.task_flush_calls: list[ast.Call] = []
        self.set_offline_calls: list[ast.Call] = []
        self.import_offline_calls: list[ast.Call] = []
        self.connect_calls: list[ast.Call] = []
        self.connect_configuration_calls: list[ast.Call] = []
        self.upload_artifact_calls: list[ast.Call] = []
        self.register_artifact_calls: list[ast.Call] = []
        self.report_calls: list[ast.Call] = []
        self.logger_constructor_calls: list[ast.Call] = []
        self.current_logger_calls: list[ast.Call] = []
        self.framework_setup_calls: list[ast.Call] = []
        self.parser_parse_calls: list[ast.Call] = []
        self.open_calls: list[ast.Call] = []
        self.output_model_calls: list[ast.Call] = []
        self.output_model_update_calls: list[ast.Call] = []
        self.input_model_calls: list[ast.Call] = []
        self.task_current_calls: list[ast.Call] = []
        self.task_get_logger_calls: list[ast.Call] = []
        self.scope_stack: list[str] = []
        self.call_scopes: dict[int, tuple[str, ...]] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function_like(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function_like(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope_stack.append(f"class:{node.name}")
        self.generic_visit(node)
        self.scope_stack.pop()

    def _visit_function_like(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.scope_stack.append(f"function:{node.name}")
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == "clearml":
                self.clearml_modules.add(alias.asname or "clearml")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "clearml":
            for alias in node.names:
                local_name = alias.asname or alias.name
                if alias.name == "Task":
                    self.task_aliases.add(local_name)
                elif alias.name == "TaskTypes":
                    self.task_types_aliases.add(local_name)
                elif alias.name == "Logger":
                    self.logger_aliases.add(local_name)
                elif alias.name == "OutputModel":
                    self.output_model_aliases.add(local_name)
                elif alias.name == "InputModel":
                    self.input_model_aliases.add(local_name)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        self._record_assignment_targets(node.targets, node.value)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._record_assignment_targets([node.target], node.value)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        self.call_scopes[id(node)] = tuple(self.scope_stack)
        call_name = self._call_name(node.func)
        if self._is_task_call(call_name, "init"):
            self.task_init_calls.append(node)
        elif self._is_task_call(call_name, "create"):
            self.task_create_calls.append(node)
        elif self._is_task_call(call_name, "set_offline"):
            self.set_offline_calls.append(node)
        elif self._is_task_call(call_name, "import_offline_session"):
            self.import_offline_calls.append(node)
        elif self._is_task_call(call_name, "current_task"):
            self.task_current_calls.append(node)
        elif call_name.endswith(".close"):
            self.task_close_calls.append(node)
        elif call_name.endswith(".flush"):
            self.task_flush_calls.append(node)
        elif call_name.endswith(".connect"):
            self.connect_calls.append(node)
        elif call_name.endswith(".connect_configuration"):
            self.connect_configuration_calls.append(node)
        elif call_name.endswith(".upload_artifact"):
            self.upload_artifact_calls.append(node)
        elif call_name.endswith(".register_artifact"):
            self.register_artifact_calls.append(node)
        elif call_name.endswith(".get_logger"):
            self.task_get_logger_calls.append(node)
        elif self._is_logger_constructor(call_name):
            self.logger_constructor_calls.append(node)
        elif self._is_logger_call(call_name, "current_logger"):
            self.current_logger_calls.append(node)
        elif self._is_logger_report_call(call_name):
            self.report_calls.append(node)
        elif self._is_framework_setup_call(call_name):
            self.framework_setup_calls.append(node)
        elif call_name.endswith(".parse_args") or call_name.endswith(".parse_known_args"):
            self.parser_parse_calls.append(node)
        elif call_name == "open" or call_name.endswith(".open"):
            self.open_calls.append(node)
        elif self._is_output_model_constructor(call_name):
            self.output_model_calls.append(node)
        elif self._is_input_model_constructor(call_name):
            self.input_model_calls.append(node)
        elif call_name.endswith(".update_weights") or call_name.endswith(".update_labels"):
            self.output_model_update_calls.append(node)
        self.generic_visit(node)

    def analyze(self) -> list[Finding]:
        self._check_import_and_init()
        self._check_task_init_parameters()
        self._check_initialization_order()
        self._check_offline_mode()
        self._check_logger_usage()
        self._check_artifact_and_model_usage()
        self._check_config_usage()
        self._check_shutdown()
        return sorted(self.findings, key=lambda item: (item.line, item.severity, item.code))

    def _record_assignment_targets(self, targets: Iterable[ast.expr], value: ast.AST | None) -> None:
        if value is None:
            return
        call_value = value if isinstance(value, ast.Call) else None
        if call_value is None:
            return
        call_name = self._call_name(call_value.func)
        for target in targets:
            for target_name in self._target_names(target):
                if self._is_task_call(call_name, "init"):
                    self.task_variables.add(target_name)
                elif call_name.endswith(".get_logger") or self._is_logger_call(call_name, "current_logger"):
                    self.logger_variables.add(target_name)
                elif self._is_output_model_constructor(call_name):
                    self.output_model_variables.add(target_name)

    def _target_names(self, target: ast.AST) -> Iterable[str]:
        if isinstance(target, ast.Name):
            yield target.id
        elif isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                yield from self._target_names(element)

    def _call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            prefix = self._call_name(node.value)
            return f"{prefix}.{node.attr}" if prefix else node.attr
        if isinstance(node, ast.Call):
            return self._call_name(node.func)
        return ""

    def _is_task_call(self, call_name: str, method: str) -> bool:
        direct_names = {f"{alias}.{method}" for alias in self.task_aliases or {"Task"}}
        module_names = {f"{module}.Task.{method}" for module in self.clearml_modules or {"clearml"}}
        return call_name in direct_names or call_name in module_names

    def _is_logger_constructor(self, call_name: str) -> bool:
        direct_names = self.logger_aliases or {"Logger"}
        module_names = {f"{module}.Logger" for module in self.clearml_modules or {"clearml"}}
        return call_name in direct_names or call_name in module_names

    def _is_logger_call(self, call_name: str, method: str) -> bool:
        direct_names = {f"{alias}.{method}" for alias in self.logger_aliases or {"Logger"}}
        module_names = {f"{module}.Logger.{method}" for module in self.clearml_modules or {"clearml"}}
        return call_name in direct_names or call_name in module_names

    def _is_logger_report_call(self, call_name: str) -> bool:
        report_methods = (
            "report_scalar",
            "report_text",
            "report_image",
            "report_table",
            "report_plotly",
            "report_matplotlib_figure",
            "report_media",
            "report_single_value",
            "report_histogram",
            "report_line_plot",
            "report_scatter2d",
            "report_confusion_matrix",
            "report_surface",
        )
        return any(call_name.endswith(f".{method}") for method in report_methods)

    def _is_output_model_constructor(self, call_name: str) -> bool:
        direct_names = self.output_model_aliases or {"OutputModel"}
        module_names = {f"{module}.OutputModel" for module in self.clearml_modules or {"clearml"}}
        return call_name in direct_names or call_name in module_names

    def _is_input_model_constructor(self, call_name: str) -> bool:
        direct_names = self.input_model_aliases or {"InputModel"}
        module_names = {f"{module}.InputModel" for module in self.clearml_modules or {"clearml"}}
        return call_name in direct_names or call_name in module_names

    def _is_framework_setup_call(self, call_name: str) -> bool:
        setup_suffixes = (
            "SummaryWriter",
            "TensorBoard",
            "ModelCheckpoint",
            "CSVLogger",
            "WandbLogger",
            "plt.show",
            "pyplot.show",
            "savefig",
            "torch.save",
            "joblib.dump",
            "pickle.dump",
            "xgb.train",
            "lightgbm.train",
        )
        return any(call_name == suffix or call_name.endswith(f".{suffix}") for suffix in setup_suffixes)

    def _keyword(self, node: ast.Call, name: str) -> ast.keyword | None:
        for keyword in node.keywords:
            if keyword.arg == name:
                return keyword
        return None

    def _constant_bool(self, node: ast.AST | None) -> bool | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, bool):
            return node.value
        return None

    def _constant_str(self, node: ast.AST | None) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def _constant_int(self, node: ast.AST | None) -> int | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
            return node.value
        return None

    def _add(self, severity: str, line: int, code: str, message: str, suggestion: str) -> None:
        self.findings.append(Finding(severity, line, code, message, suggestion))

    def _scope_of(self, node: ast.Call) -> tuple[str, ...]:
        return self.call_scopes.get(id(node), ())

    def _first_task_init_line(self, scope: tuple[str, ...] | None = None) -> int | None:
        matching_calls = [
            task_init_call
            for task_init_call in self.task_init_calls
            if scope is None or self._scope_of(task_init_call) == scope
        ]
        if not matching_calls:
            return None
        return min(task_init_call.lineno for task_init_call in matching_calls)

    def _check_import_and_init(self) -> None:
        has_clearml_import = bool(
            self.clearml_modules
            or self.task_aliases
            or self.logger_aliases
            or self.output_model_aliases
            or self.input_model_aliases
        )
        if not has_clearml_import:
            self._add(
                "error",
                1,
                "missing-clearml-import",
                "No ClearML import was found.",
                "Add `from clearml import Task` and initialize tracking with `Task.init(...)`.",
            )
        if not self.task_init_calls:
            self._add(
                "error",
                1,
                "missing-task-init",
                "No `Task.init(...)` call was found.",
                "Create one main ClearML task near the start of executable code.",
            )
        if len(self.task_init_calls) > 1:
            for task_init_call in self.task_init_calls[1:]:
                self._add(
                    "warning",
                    task_init_call.lineno,
                    "multiple-task-init",
                    "Multiple `Task.init(...)` calls were found.",
                    "Keep one main execution task unless intentionally creating separate process/rank tasks.",
                )
        for task_create_call in self.task_create_calls:
            self._add(
                "info",
                task_create_call.lineno,
                "task-create-no-auto-logging",
                "`Task.create(...)` creates a task object but does not provide normal in-process experiment auto-logging.",
                "Use `Task.init(...)` for tracking the current running script; reserve `Task.create` for remote execution/task creation workflows.",
            )

    def _check_task_init_parameters(self) -> None:
        if not self.task_init_calls:
            return
        for task_init_call in self.task_init_calls:
            project_keyword = self._keyword(task_init_call, "project_name")
            task_keyword = self._keyword(task_init_call, "task_name")
            type_keyword = self._keyword(task_init_call, "task_type")
            reuse_keyword = self._keyword(task_init_call, "reuse_last_task_id")
            continue_keyword = self._keyword(task_init_call, "continue_last_task")
            output_keyword = self._keyword(task_init_call, "output_uri")
            frameworks_keyword = self._keyword(task_init_call, "auto_connect_frameworks")
            deferred_keyword = self._keyword(task_init_call, "deferred_init")
            if project_keyword is None and len(task_init_call.args) < 1:
                self._add(
                    "warning",
                    task_init_call.lineno,
                    "missing-project-name",
                    "`Task.init` does not specify `project_name`.",
                    "Pass a stable `project_name` so experiments route to the intended ClearML project.",
                )
            if task_keyword is None and len(task_init_call.args) < 2:
                self._add(
                    "warning",
                    task_init_call.lineno,
                    "missing-task-name",
                    "`Task.init` does not specify `task_name`.",
                    "Pass a descriptive `task_name` instead of relying on the script filename.",
                )
            if type_keyword is None:
                self._add(
                    "info",
                    task_init_call.lineno,
                    "default-task-type",
                    "`Task.init` does not specify `task_type`; ClearML defaults to training.",
                    "Set `task_type=TaskTypes.training`, `testing`, `inference`, or `data_processing` to document intent.",
                )
            if reuse_keyword is None:
                self._add(
                    "warning",
                    task_init_call.lineno,
                    "default-task-reuse",
                    "`Task.init` uses the default `reuse_last_task_id=True` behavior.",
                    "Use `reuse_last_task_id=False` for a new task per repeated local run, unless reuse is intentional.",
                )
            elif self._constant_bool(reuse_keyword.value) is True:
                self._add(
                    "warning",
                    reuse_keyword.value.lineno,
                    "explicit-task-reuse",
                    "`reuse_last_task_id=True` can overwrite a recent same-project/name development task.",
                    "Use `False` for independent runs, or document the reuse/continue policy.",
                )
            if continue_keyword is not None:
                continue_bool = self._constant_bool(continue_keyword.value)
                continue_str = self._constant_str(continue_keyword.value)
                continue_int = self._constant_int(continue_keyword.value)
                if continue_bool is True or continue_str or continue_int is not None:
                    self._add(
                        "info",
                        continue_keyword.value.lineno,
                        "continue-last-task",
                        "`continue_last_task` is enabled or set to a task/iteration value.",
                        "Verify the user wants to append to an existing task and offset metrics rather than create a fresh task.",
                    )
            if output_keyword is None and (self.upload_artifact_calls or self.output_model_calls or self.output_model_update_calls):
                self._add(
                    "warning",
                    task_init_call.lineno,
                    "missing-output-uri",
                    "The script uploads artifacts or models but `Task.init` does not specify `output_uri`.",
                    "Use `output_uri=True` for the default file server or an explicit configured storage URI.",
                )
            elif output_keyword is not None and self._constant_bool(output_keyword.value) is False:
                self._add(
                    "warning",
                    output_keyword.value.lineno,
                    "disabled-output-uri",
                    "`output_uri=False` disables default artifact/model upload destinations.",
                    "Use this only when uploads are intentionally disabled; otherwise choose `True` or a configured URI.",
                )
            if frameworks_keyword is not None and self._constant_bool(frameworks_keyword.value) is False:
                self._add(
                    "info",
                    frameworks_keyword.value.lineno,
                    "framework-auto-connect-disabled",
                    "`auto_connect_frameworks=False` disables supported framework auto-logging.",
                    "Add explicit `Logger` reports and `OutputModel` handling, or enable only the needed framework keys.",
                )
            if deferred_keyword is not None and self._constant_bool(deferred_keyword.value) is True:
                self._add(
                    "info",
                    deferred_keyword.value.lineno,
                    "deferred-init",
                    "`deferred_init=True` can miss very early auto-logged events.",
                    "Use default synchronous initialization unless startup latency is more important than early capture.",
                )

    def _check_initialization_order(self) -> None:
        if not self.task_init_calls:
            return
        for parser_call in self.parser_parse_calls:
            first_init_line = self._first_task_init_line(self._scope_of(parser_call))
            if first_init_line is not None and parser_call.lineno < first_init_line:
                self._add(
                    "info",
                    parser_call.lineno,
                    "parser-before-task-init",
                    "Argument parsing occurs before `Task.init` in the same executable scope, so automatic parser capture may miss values.",
                    "Initialize before parsing or explicitly call `task.connect(args, name=...)` after parsing.",
                )
        for setup_call in self.framework_setup_calls:
            first_init_line = self._first_task_init_line(self._scope_of(setup_call))
            if first_init_line is not None and setup_call.lineno < first_init_line:
                self._add(
                    "warning",
                    setup_call.lineno,
                    "framework-before-task-init",
                    "Framework logging, plotting, or checkpoint setup appears before `Task.init` in the same executable scope.",
                    "Move `Task.init` before TensorBoard writers, plotting, checkpoint callbacks, and model saves when auto-logging is desired.",
                )
        for report_call in self.report_calls:
            first_init_line = self._first_task_init_line(self._scope_of(report_call))
            if first_init_line is not None and report_call.lineno < first_init_line:
                self._add(
                    "error",
                    report_call.lineno,
                    "report-before-task-init",
                    "A `Logger.report_*` call appears before `Task.init` in the same executable scope.",
                    "Create the ClearML task before any manual reporting calls.",
                )

    def _check_offline_mode(self) -> None:
        if not self.set_offline_calls:
            return
        offline_enable_calls: list[ast.Call] = []
        offline_disable_calls: list[ast.Call] = []
        for set_offline_call in self.set_offline_calls:
            offline_value = None
            if set_offline_call.args:
                offline_value = self._constant_bool(set_offline_call.args[0])
            keyword = self._keyword(set_offline_call, "offline_mode")
            if keyword is not None:
                offline_value = self._constant_bool(keyword.value)
            if offline_value is True:
                offline_enable_calls.append(set_offline_call)
                first_init_line = self._first_task_init_line(self._scope_of(set_offline_call))
                if first_init_line is not None and set_offline_call.lineno > first_init_line:
                    self._add(
                        "error",
                        set_offline_call.lineno,
                        "offline-after-task-init",
                        "`Task.set_offline(True)` appears after `Task.init` in the same executable scope.",
                        "Call `Task.set_offline(True)` before `Task.init` so the run never contacts the backend.",
                    )
            elif offline_value is False:
                offline_disable_calls.append(set_offline_call)
        for task_create_call in self.task_create_calls:
            same_scope_enables = [
                offline_call
                for offline_call in offline_enable_calls
                if self._scope_of(offline_call) == self._scope_of(task_create_call)
            ]
            if same_scope_enables and task_create_call.lineno > min(call.lineno for call in same_scope_enables):
                self._add(
                    "error",
                    task_create_call.lineno,
                    "offline-task-create",
                    "Offline mode is enabled but the script uses `Task.create(...)` in the same executable scope.",
                    "Use `Task.init(...)` for offline experiment capture.",
                )
        if offline_disable_calls and not self.task_close_calls:
            self._add(
                "warning",
                min(call.lineno for call in offline_disable_calls),
                "offline-disable-without-close",
                "Offline mode is switched off but no `task.close()` call was found.",
                "Close the current task before calling `Task.set_offline(False)`.",
            )
        if offline_enable_calls and not self.import_offline_calls:
            self._add(
                "info",
                min(call.lineno for call in offline_enable_calls),
                "offline-import-not-shown",
                "Offline mode is used but `Task.import_offline_session(...)` was not found.",
                "Print or persist `task.get_offline_mode_folder()` and import the session later when credentials are available.",
            )

    def _check_logger_usage(self) -> None:
        for constructor_call in self.logger_constructor_calls:
            self._add(
                "warning",
                constructor_call.lineno,
                "logger-constructor",
                "Direct `Logger(...)` construction was found.",
                "Use `task.get_logger()` or `Task.current_task().get_logger()` after `Task.init`.",
            )
        for current_logger_call in self.current_logger_calls:
            if not self.task_init_calls or current_logger_call.lineno < min(call.lineno for call in self.task_init_calls):
                self._add(
                    "warning",
                    current_logger_call.lineno,
                    "current-logger-before-init",
                    "`Logger.current_logger()` is used before a visible `Task.init` call.",
                    "Initialize the task first, then use `task.get_logger()` or `Task.current_task().get_logger()`.",
                )
        for report_call in self.report_calls:
            call_name = self._call_name(report_call.func)
            if call_name.endswith(".report_scalar"):
                iteration_keyword = self._keyword(report_call, "iteration")
                if iteration_keyword is None and len(report_call.args) < 4:
                    self._add(
                        "warning",
                        report_call.lineno,
                        "scalar-missing-iteration",
                        "`report_scalar` does not appear to pass `iteration`.",
                        "Pass a deterministic step or epoch through `iteration=...`.",
                    )
            if call_name.endswith((".report_image", ".report_table", ".report_plotly", ".report_matplotlib_figure")):
                iteration_keyword = self._keyword(report_call, "iteration")
                if iteration_keyword is None:
                    self._add(
                        "info",
                        report_call.lineno,
                        "report-missing-iteration",
                        "A report call omits `iteration`, so ClearML may default or group reports unexpectedly.",
                        "Pass `iteration=step_or_epoch` for charts and debug samples that should align with training progress.",
                    )
            if call_name.endswith(".report_image") and len(report_call.args) >= 4:
                self._add(
                    "info",
                    report_call.lineno,
                    "report-image-positional",
                    "`report_image` uses four or more positional arguments, which is easy to misread.",
                    "Prefer named arguments such as `iteration=...`, `image=...`, or `local_path=...`.",
                )

    def _check_artifact_and_model_usage(self) -> None:
        for upload_call in self.upload_artifact_calls:
            wait_keyword = self._keyword(upload_call, "wait_on_upload")
            retries_keyword = self._keyword(upload_call, "retries")
            if wait_keyword is None:
                self._add(
                    "info",
                    upload_call.lineno,
                    "artifact-background-upload",
                    "`upload_artifact` defaults to background upload.",
                    "Use `wait_on_upload=True` for important artifacts in short-lived scripts.",
                )
            if retries_keyword is None:
                self._add(
                    "info",
                    upload_call.lineno,
                    "artifact-no-retries",
                    "`upload_artifact` does not specify retries.",
                    "Consider `retries=2` or higher for flaky storage backends.",
                )
        for register_call in self.register_artifact_calls:
            self._add(
                "info",
                register_call.lineno,
                "registered-artifact",
                "`register_artifact` dynamically synchronizes pandas DataFrames and overwrites same-name registrations.",
                "Use `upload_artifact` for one-time files, dictionaries, arrays, images, folders, or wildcards.",
            )
        for output_model_call in self.output_model_calls:
            task_keyword = self._keyword(output_model_call, "task")
            if task_keyword is None and not output_model_call.args:
                self._add(
                    "warning",
                    output_model_call.lineno,
                    "output-model-without-task",
                    "`OutputModel(...)` is created without a visible `task=` argument.",
                    "Pass `task=task` so model metadata is associated with the current experiment.",
                )
        if self.output_model_calls and not self.output_model_update_calls:
            self._add(
                "info",
                min(call.lineno for call in self.output_model_calls),
                "output-model-no-updates",
                "`OutputModel` is created but no visible `update_weights` or `update_labels` call was found.",
                "Add `update_weights(...)` for model files and `update_labels(...)` for class label mappings when relevant.",
            )

    def _check_config_usage(self) -> None:
        if self.open_calls and not self.connect_configuration_calls and self.task_init_calls:
            first_open_line = min(open_call.lineno for open_call in self.open_calls)
            self._add(
                "info",
                first_open_line,
                "config-open-without-connect-configuration",
                "The script opens files but no `task.connect_configuration(...)` call was found.",
                "If a YAML/JSON/config file controls training, connect it before reading so remote overrides can apply.",
            )
        for config_call in self.connect_configuration_calls:
            if config_call.lineno > min((open_call.lineno for open_call in self.open_calls), default=10**9):
                self._add(
                    "warning",
                    config_call.lineno,
                    "connect-configuration-after-open",
                    "`connect_configuration` appears after an earlier file open call.",
                    "Connect configuration files before reading them, then read the returned path.",
                )

    def _check_shutdown(self) -> None:
        if (self.upload_artifact_calls or self.report_calls or self.output_model_update_calls) and not self.task_flush_calls and not self.task_close_calls:
            relevant_line = max(
                [call.lineno for call in self.upload_artifact_calls + self.report_calls + self.output_model_update_calls],
                default=1,
            )
            self._add(
                "info",
                relevant_line,
                "no-flush-or-close",
                "The script reports/uploads data but no visible `flush` or `close` call was found.",
                "For short scripts, call `logger.flush(wait=True)`, `task.flush(wait_for_uploads=True)`, or `task.close()` before exit.",
            )


def analyze_source(path: Path) -> tuple[list[Finding], dict[str, Any]]:
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        source = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        finding = Finding(
            "error",
            exc.lineno or 1,
            "syntax-error",
            f"Python syntax error: {exc.msg}",
            "Fix syntax before reviewing ClearML instrumentation.",
        )
        return [finding], {"parse_ok": False}
    analyzer = ClearMLTrackingAnalyzer()
    analyzer.visit(tree)
    findings = analyzer.analyze()
    summary = {
        "parse_ok": True,
        "task_init_calls": len(analyzer.task_init_calls),
        "report_calls": len(analyzer.report_calls),
        "upload_artifact_calls": len(analyzer.upload_artifact_calls),
        "connect_calls": len(analyzer.connect_calls),
        "connect_configuration_calls": len(analyzer.connect_configuration_calls),
        "offline_mode_calls": len(analyzer.set_offline_calls),
        "output_model_calls": len(analyzer.output_model_calls),
    }
    return findings, summary


def format_text(path: Path, findings: list[Finding], summary: dict[str, Any]) -> str:
    lines = [f"ClearML tracking static review: {path}"]
    lines.append(
        "Summary: "
        + ", ".join(
            f"{name}={value}"
            for name, value in summary.items()
            if name != "parse_ok"
        )
    )
    if not findings:
        lines.append("No likely ClearML tracking issues found by static checks.")
        return "\n".join(lines)
    severity_order = {"error": 0, "warning": 1, "info": 2}
    sorted_findings = sorted(findings, key=lambda item: (severity_order.get(item.severity, 9), item.line, item.code))
    for finding in sorted_findings:
        lines.append(f"{finding.severity.upper()} line {finding.line} [{finding.code}]: {finding.message}")
        lines.append(f"  Suggestion: {finding.suggestion}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Statically check a Python file for likely ClearML Task/Logger instrumentation issues. "
            "The script parses AST only; it does not import or execute the target file and does not contact a server."
        )
    )
    parser.add_argument("python_file", type=Path, help="Python file to inspect")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--fail-on",
        choices=("none", "error", "warning", "info"),
        default="error",
        help="exit non-zero when findings at this severity or higher are present (default: error)",
    )
    return parser


def should_fail(findings: list[Finding], threshold: str) -> bool:
    if threshold == "none":
        return False
    severity_rank = {"error": 3, "warning": 2, "info": 1}
    return any(severity_rank.get(finding.severity, 0) >= severity_rank[threshold] for finding in findings)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    target_path = args.python_file
    if not target_path.is_file():
        message = f"Target file does not exist or is not a file: {target_path}"
        if args.json:
            print(json.dumps({"ok": False, "error": message}, indent=2, sort_keys=True))
        else:
            print(message, file=sys.stderr)
        return 2
    findings, summary = analyze_source(target_path)
    if args.json:
        payload = {
            "ok": not should_fail(findings, args.fail_on),
            "path": str(target_path),
            "summary": summary,
            "findings": [finding.as_dict() for finding in findings],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_text(target_path, findings, summary))
    return 1 if should_fail(findings, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())

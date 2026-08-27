#!/usr/bin/env python3
"""No-network validation checks for the SwanLab open-api-and-cli sub-skill.

The checks exercise public validation helpers, Click help paths, pagination
flags, and mocked 4xx/5xx behavior. They intentionally avoid constructing a
real network-backed Api instance.
"""

from __future__ import annotations

import contextlib
import importlib
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Iterator, TypeVar

import requests

T = TypeVar("T", bound=BaseException)


class CheckFailure(AssertionError):
    """Raised when a validation check fails."""


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def assert_raises(
    exc_type: type[T],
    func: Callable[..., Any],
    *args: Any,
    contains: str | None = None,
    **kwargs: Any,
) -> T:
    try:
        func(*args, **kwargs)
    except exc_type as exc:
        if contains is not None and contains not in str(exc):
            raise CheckFailure(f"expected error containing {contains!r}, got {exc!r}") from exc
        return exc
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise CheckFailure(f"expected {exc_type.__name__}, got {type(exc).__name__}: {exc}") from exc
    raise CheckFailure(f"expected {exc_type.__name__} from {getattr(func, '__name__', func)!r}")


@contextlib.contextmanager
def forbid_requests_network() -> Iterator[list[str]]:
    """Block requests-based network calls and record attempted URLs."""

    attempted: list[str] = []
    original_request = requests.sessions.Session.request

    def blocked_request(self: requests.Session, method: str, url: str, **kwargs: Any) -> Any:  # noqa: ARG001
        attempted.append(f"{method} {url}")
        raise CheckFailure(f"network access is forbidden during validation: {method} {url}")

    requests.sessions.Session.request = blocked_request
    try:
        yield attempted
    finally:
        requests.sessions.Session.request = original_request


class FakeResponse:
    def __init__(self, data: Any) -> None:
        self.data = data


class RaisingClient:
    """Client stub that simulates 4xx/5xx errors without network."""

    def get(self, path: str, **kwargs: Any) -> FakeResponse:  # noqa: ARG002
        raise requests.exceptions.HTTPError(f"500 mocked GET {path}")

    def post(self, path: str, **kwargs: Any) -> FakeResponse:  # noqa: ARG002
        raise requests.exceptions.HTTPError(f"500 mocked POST {path}")

    def put(self, path: str, **kwargs: Any) -> FakeResponse:  # noqa: ARG002
        raise requests.exceptions.HTTPError(f"500 mocked PUT {path}")

    def delete(self, path: str, **kwargs: Any) -> FakeResponse:  # noqa: ARG002
        raise requests.exceptions.HTTPError(f"500 mocked DELETE {path}")


class PagingClient:
    """Client stub for proving PaginatedQuery all=False/all=True behavior."""

    def __init__(self) -> None:
        self.pages_requested: list[int] = []

    def get(self, path: str, **kwargs: Any) -> FakeResponse:  # noqa: ARG002
        page = int(kwargs.get("params", {}).get("page", 1))
        self.pages_requested.append(page)
        return FakeResponse({"list": [{"page": page}], "total": 2, "pages": 2, "size": 1})


class DummyEntityMixin:
    def json(self) -> dict[str, Any]:
        return {}


def make_ctx(client: Any):
    from swanlab.api.base import ApiClientContext

    return ApiClientContext(
        client=client,
        web_host="web-host",
        api_host="api-host",
        username="alice",
        name="Alice",
    )


def check_path_and_project_validation(ctx: Any) -> None:
    from swanlab.api import Api
    from swanlab.api.base import BaseEntity
    from swanlab.api.utils import validate_api_path, validate_project_name, validate_visibility

    api = Api.__new__(Api)
    BaseEntity.__init__(api, ctx)

    validate_api_path("alice", segments=1, label="workspace")
    validate_api_path("alice/demo", segments=2, label="project")
    validate_api_path("alice/demo/run-1", segments=3, label="run")

    for bad in ("", " alice", "alice/", "alice//demo", "alice/demo/run/extra"):
        assert_raises(ValueError, validate_api_path, bad, segments=2, label="project", contains="path")

    assert_raises(ValueError, api.workspace, "alice/team")
    assert_raises(ValueError, api.project, "alice")
    assert_raises(ValueError, api.project, " alice/demo")
    assert_raises(ValueError, api.projects, "alice/demo")
    assert_raises(ValueError, api.run, "alice/demo")
    assert_raises(ValueError, api.runs, "alice/demo/run-1")

    validate_project_name("demo-1.0+cpu")
    for bad_name in ("", "x" * 101, "hello world", "alice/demo", "name@host", "中文项目"):
        assert_raises(ValueError, validate_project_name, bad_name)

    validate_visibility("PUBLIC")
    validate_visibility("PRIVATE")
    assert_raises(ValueError, validate_visibility, "SECRET", contains="Invalid visibility")


def check_filter_sort_metric_validation() -> None:
    from swanlab.api.typings.common import PaginatedQuery
    from swanlab.api.utils import (
        validate_filter,
        validate_group,
        validate_metric_keys,
        validate_metric_log_level,
        validate_metric_type,
        validate_sort,
        validate_update_active,
    )

    valid_filter = {"key": "state", "type": "STABLE", "op": "EQ", "value": ["RUNNING"]}
    valid_group = {"key": "cluster", "type": "STABLE"}
    valid_sort = {"key": "createdAt", "type": "STABLE", "order": "DESC"}

    validate_filter(valid_filter)
    validate_group(valid_group)
    validate_sort(valid_sort)
    active_filters = validate_update_active([valid_filter], validate_filter, label="filters")
    assert_true(active_filters == [{**valid_filter, "active": True}], "filters should be marked active")

    assert_raises(ValueError, validate_filter, {"key": "state"}, contains="Missing required")
    assert_raises(
        ValueError,
        validate_filter,
        {"key": "state", "type": "INVALID", "op": "EQ", "value": ["RUNNING"]},
        contains="Invalid type",
    )
    assert_raises(
        ValueError,
        validate_filter,
        {"key": "state", "type": "STABLE", "op": "LIKE", "value": ["RUNNING"]},
        contains="Invalid filter op",
    )
    assert_raises(
        ValueError,
        validate_filter,
        {"key": "state", "type": "STABLE", "op": "EQ", "value": "RUNNING"},
        contains="must be a list",
    )
    assert_raises(
        ValueError,
        validate_sort,
        {"key": "createdAt", "type": "STABLE", "order": "RANDOM"},
        contains="Invalid sort order",
    )
    assert_raises(ValueError, validate_group, {"key": "cluster", "type": "BAD"}, contains="Invalid type")

    validate_metric_type("SCALAR", key="loss")
    validate_metric_type("MEDIA", key="image")
    validate_metric_type("LOG")
    validate_metric_log_level("INFO")
    validate_metric_keys(["loss", "acc"])
    assert_raises(ValueError, validate_metric_type, "INVALID", key="loss", contains="Invalid metric_type")
    assert_raises(ValueError, validate_metric_type, "SCALAR", key="", contains="key is required")
    assert_raises(ValueError, validate_metric_log_level, "VERBOSE", contains="Invalid metric log level")
    assert_raises(ValueError, validate_metric_keys, [], contains="non-empty")
    assert_raises(ValueError, validate_metric_keys, ["loss", ""], contains="non-empty")

    q = PaginatedQuery(page=1, size=20, search="demo", sort="update", all=True)
    params = q.to_params(detail=True)
    assert_true(params == {"page": 1, "size": 20, "search": "demo", "sort": "update", "detail": True}, "all should not be sent as a query param")
    assert_raises(ValueError, PaginatedQuery, page=0, contains="page must be >= 1")
    assert_raises(ValueError, PaginatedQuery, size=42, contains="size must be one of")


def check_pagination_all_flags() -> None:
    from swanlab.api.base import BaseEntity
    from swanlab.api.typings.common import PaginatedQuery

    class DummyEntity(DummyEntityMixin, BaseEntity):
        pass

    one_page_client = PagingClient()
    one_page_entity = DummyEntity(make_ctx(one_page_client))
    one_page_info = {"total": 0, "pages": 0}
    one_page_items = list(
        one_page_entity._paginate("/items", PaginatedQuery(page=1, size=10, all=False), page_info=one_page_info)
    )
    assert_true(one_page_items == [{"page": 1}], "all=False should fetch exactly one page")
    assert_true(one_page_client.pages_requested == [1], "all=False should request page 1 only")

    all_pages_client = PagingClient()
    all_pages_entity = DummyEntity(make_ctx(all_pages_client))
    all_pages_info = {"total": 0, "pages": 0}
    all_pages_items = list(
        all_pages_entity._paginate("/items", PaginatedQuery(page=1, size=10, all=True), page_info=all_pages_info)
    )
    assert_true(all_pages_items == [{"page": 1}, {"page": 2}], "all=True should fetch both pages")
    assert_true(all_pages_client.pages_requested == [1, 2], "all=True should request sequential pages")


def check_credentials_without_network() -> None:
    from swanlab.api import Api
    from swanlab.exceptions import AuthenticationError

    assert_raises(AuthenticationError, Api._resolve_credentials, "", "api-host", contains="No API key")
    assert_raises(AuthenticationError, Api._resolve_credentials, "   ", "api-host", contains="No API key")
    assert_raises(ValueError, Api._resolve_credentials, "test-key", "   ", contains="Host cannot be empty")

    api_module = importlib.import_module("swanlab.api")
    original_create_settings = api_module.create_settings
    api_module.create_settings = lambda: SimpleNamespace(
        api_key=None,
        api_host="api-host",
        web_host="web-host",
    )
    try:
        assert_raises(AuthenticationError, Api._resolve_credentials, None, None, contains="No API key")
    finally:
        api_module.create_settings = original_create_settings


def check_4xx_5xx_behavior(ctx: Any) -> None:
    from swanlab.api.experiment import Experiment
    from swanlab.api.project import Project
    from swanlab.api.self_hosted import SelfHosted
    from swanlab.api.workspace import Workspace

    ws = Workspace(ctx, username="alice")
    assert_true(ws.name == "", "workspace 5xx should return empty name")

    project = Project(ctx, path="alice/demo")
    assert_true(project.name == "", "project 5xx should return empty name")
    assert_true(project.delete(commit=True) is False, "project delete 5xx should return False")

    run = Experiment(ctx, path="alice/demo/run-1")
    assert_true(run.name == "", "run 5xx should return empty name")
    assert_true(run.delete(commit=True) is False, "run delete 5xx should return False")

    sh = SelfHosted(ctx)
    assert_true(sh.enabled is False, "self-hosted 5xx should return disabled default")

    root_info = {"enabled": True, "expired": False, "root": True, "plan": "free", "seats": 10}
    root_sh = SelfHosted(ctx, data=root_info)
    assert_true(root_sh.create_user("bob", "secret").ok is False, "self-hosted create_user 5xx should be ok=False")


def check_self_hosted_validation(ctx: Any) -> None:  # noqa: ARG001
    from swanlab.api.self_hosted import SelfHosted

    ok_info = {"enabled": True, "expired": False, "root": True, "plan": "free", "seats": 10}
    expired_info = {**ok_info, "expired": True}
    non_root_info = {**ok_info, "root": False}

    SelfHosted.validate_expire(ok_info)
    SelfHosted.validate_root(ok_info)
    assert_raises(ValueError, SelfHosted.validate_expire, expired_info, contains="expired")
    assert_raises(ValueError, SelfHosted.validate_root, expired_info, contains="expired")
    assert_raises(ValueError, SelfHosted.validate_root, non_root_info, contains="root")
    assert_raises(ValueError, SelfHosted(make_ctx(RaisingClient()), data=ok_info).create_user, "", "secret")
    assert_raises(ValueError, SelfHosted(make_ctx(RaisingClient()), data=ok_info).create_user, "bob", "")


def check_filter_query_and_cli_help() -> None:
    from click import BadParameter
    from click.testing import CliRunner

    from swanlab.cli.api import api_cli
    from swanlab.cli.api.helper import validate_filter_query

    inline = validate_filter_query('[{"key":"state","type":"STABLE","op":"EQ","value":["RUNNING"]}]')
    assert_true(inline[0]["key"] == "state", "inline filter JSON should parse")

    with tempfile.TemporaryDirectory() as tmpdir:
        filter_file = Path(tmpdir) / "filter.json"
        filter_file.write_text('[{"key":"name","type":"STABLE","op":"CONTAIN","value":["demo"]}]')
        from_file = validate_filter_query(str(filter_file))
        assert_true(from_file[0]["op"] == "CONTAIN", "filter file should parse")

    assert_raises(BadParameter, validate_filter_query, "  ", contains="must not be empty")
    assert_raises(BadParameter, validate_filter_query, "not json", contains="neither a valid file path nor valid JSON")
    assert_raises(BadParameter, validate_filter_query, '{"key":"state"}', contains="JSON array")

    runner = CliRunner()
    for args in (
        ["--help"],
        ["project", "--help"],
        ["project", "create", "--help"],
        ["run", "--help"],
        ["run", "metrics", "--help"],
        ["run", "filter", "--help"],
        ["self-hosted", "--help"],
        ["self-hosted", "list-projects", "--help"],
        ["user", "info", "--help"],
        ["workspace", "info", "--help"],
    ):
        result = runner.invoke(api_cli, args)
        assert_true(result.exit_code == 0, f"CLI help failed for {args}: {result.output}")
        assert_true("Usage:" in result.output, f"CLI help missing Usage for {args}")

    missing_args = runner.invoke(api_cli, ["run", "metrics"])
    assert_true(missing_args.exit_code != 0, "missing CLI args should fail non-interactively")
    assert_true("Missing argument" in missing_args.output, "missing CLI args should report Click error")


def main() -> int:
    with forbid_requests_network() as attempted_network:
        # Import SwanLab modules only after the network guard is active.
        ctx = make_ctx(RaisingClient())
        check_path_and_project_validation(ctx)
        check_filter_sort_metric_validation()
        check_pagination_all_flags()
        check_credentials_without_network()
        check_4xx_5xx_behavior(ctx)
        check_self_hosted_validation(ctx)
        check_filter_query_and_cli_help()
        assert_true(attempted_network == [], f"unexpected network attempts: {attempted_network}")

    print("open-api-and-cli validation checks passed (no network).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Safe smoke checks for ai-data-science-team data access and EDA helpers.

This script is intentionally local-only:
- no LLM/model calls
- no external services
- no downloads
- no training
- no writes outside a temporary directory
"""

from __future__ import annotations

import contextlib
import inspect
import io
import json
import os
import sys
import tempfile
from pathlib import Path


def _fail(message: str, exc: BaseException | None = None) -> None:
    print(f"SMOKE FAILED: {message}", file=sys.stderr)
    if exc is not None:
        print(f"DETAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
    raise SystemExit(1)


def _call_tool_silently(tool_obj, *args, **kwargs):
    """Call a LangChain StructuredTool's underlying function without leaking temp paths."""
    func = getattr(tool_obj, "func", None)
    if func is None:
        _fail(f"{tool_obj!r} does not expose .func for direct smoke testing")
    with contextlib.redirect_stdout(io.StringIO()):
        return func(*args, **kwargs)


def main() -> None:
    try:
        import IPython  # noqa: F401 - package agent modules import IPython.display
        import pandas as pd
        from ai_data_science_team.agents import DataLoaderToolsAgent
        from ai_data_science_team.ds_agents import EDAToolsAgent
        from ai_data_science_team.tools.data_loader import (
            ALLOW_UNSAFE_PICKLE_ENV_VAR,
            auto_load_file,
            list_directory_contents,
            load_directory,
            load_file,
            load_pickle,
            search_files_by_pattern,
        )
        from ai_data_science_team.tools.dataframe import get_dataframe_summary
        from ai_data_science_team.tools.eda import describe_dataset, explain_data
    except Exception as exc:  # pragma: no cover - failure path is user-facing
        _fail(
            "required base imports failed; ensure ai-data-science-team, pandas, LangChain/LangGraph dependencies, and ipython are installed",
            exc,
        )

    checks: list[str] = []

    # Public class signatures can be inspected without constructing agents or calling models.
    loader_sig = str(inspect.signature(DataLoaderToolsAgent.__init__))
    eda_sig = str(inspect.signature(EDAToolsAgent.__init__))
    assert "model" in loader_sig and "log_tool_calls" in loader_sig
    assert "model" in eda_sig and "log_tool_calls" in eda_sig
    checks.append("agent signatures inspected without model calls")

    with tempfile.TemporaryDirectory(prefix="adst_data_access_") as tmpdir:
        tmp = Path(tmpdir)
        csv_path = tmp / "tiny.csv"
        csv_path.write_text("id,value,label\n1,10,A\n2,20,B\n3,,A\n", encoding="utf-8")

        content, listing = _call_tool_silently(
            list_directory_contents,
            directory_path=str(tmp),
            show_hidden=False,
        )
        assert any(row["filename"] == "tiny.csv" for row in listing), listing
        checks.append("directory listing returned fixture")

        content, matches = _call_tool_silently(
            search_files_by_pattern,
            directory_path=str(tmp),
            pattern="*.csv",
            recursive=False,
        )
        assert len(matches) == 1 and matches[0]["file_path"].endswith("tiny.csv"), matches
        checks.append("pattern search returned fixture")

        loaded = auto_load_file(str(csv_path), max_rows=10)
        assert isinstance(loaded, pd.DataFrame), loaded
        assert loaded.shape == (3, 3), loaded.shape
        checks.append("auto_load_file loaded tiny CSV")

        content, artifact = _call_tool_silently(load_file, file_path=str(csv_path))
        assert artifact["status"] == "ok", artifact
        df_from_tool = pd.DataFrame(artifact["data"])
        assert list(df_from_tool.columns) == ["id", "value", "label"], df_from_tool.columns
        checks.append("load_file tool returned DataFrame artifact")

        content, directory_artifacts = _call_tool_silently(
            load_directory,
            directory_path=str(tmp),
            file_type="csv",
            max_mb=1,
            max_rows=10,
        )
        assert directory_artifacts["tiny.csv"]["status"] == "ok", directory_artifacts
        checks.append("load_directory loaded bounded CSV directory")

        summaries = get_dataframe_summary(df_from_tool, n_sample=2, skip_stats=True)
        assert len(summaries) == 1 and "Shape: 3 rows x 3 columns" in summaries[0], summaries
        checks.append("get_dataframe_summary produced expected shape")

        explain_result = _call_tool_silently(
            explain_data,
            data_raw=df_from_tool.to_dict(),
            n_sample=2,
            skip_stats=True,
        )
        assert explain_result and "Shape: 3 rows x 3 columns" in str(explain_result), explain_result
        checks.append("explain_data direct tool call produced summary")

        content, describe_artifact = _call_tool_silently(
            describe_dataset,
            data_raw=df_from_tool.to_dict(),
        )
        describe_df = pd.DataFrame(describe_artifact["describe_df"])
        assert "stat" in describe_df.columns, describe_df.columns
        assert "count" in set(describe_df["stat"].astype(str)), describe_df
        checks.append("describe_dataset returned flattened describe artifact")

        pickle_path = tmp / "tiny.pkl"
        df_from_tool.to_pickle(pickle_path)
        previous_pickle_opt_in = os.environ.pop(ALLOW_UNSAFE_PICKLE_ENV_VAR, None)
        try:
            try:
                load_pickle(str(pickle_path))
            except ValueError as exc:
                assert "disabled" in str(exc).lower(), exc
            else:
                _fail("unsafe pickle load unexpectedly succeeded without opt-in")
        finally:
            if previous_pickle_opt_in is not None:
                os.environ[ALLOW_UNSAFE_PICKLE_ENV_VAR] = previous_pickle_opt_in
        checks.append("pickle loading refused by default")

    print(json.dumps({"status": "ok", "checks": checks}, indent=2))


if __name__ == "__main__":
    main()

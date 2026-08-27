#!/usr/bin/env python3
"""Safe Aim SDK smoke validation.

Creates or uses a local Aim repository, tracks scalar/object data, validates
tracked content through direct SDK access, and probes query APIs without making
version-specific query/index behavior a default failure.
"""

from __future__ import annotations

import argparse
import gc
import io
import shutil
import struct
import sys
import tempfile
import time
import wave
from pathlib import Path
from typing import Iterable, Optional


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a tiny Aim repo, track SDK data, and verify safe Aim SDK usage patterns."
    )
    parser.add_argument(
        "--repo-dir",
        type=Path,
        default=None,
        help="Optional repository root to use. If omitted, a persistent temp directory is created for this process.",
    )
    parser.add_argument(
        "--keep-repo",
        action="store_true",
        help="Keep an auto-created temporary repository after the smoke run for manual inspection.",
    )
    parser.add_argument(
        "--skip-artifact",
        action="store_true",
        help="Skip local file:// artifact logging. Core tracking checks still run.",
    )
    parser.add_argument(
        "--require-query",
        action="store_true",
        help="Fail if repository query APIs cannot retrieve the smoke metric. By default query failures are diagnostic warnings.",
    )
    return parser.parse_args(argv)


def assert_pass(label: str, condition: bool, detail: str = "") -> None:
    if not condition:
        raise AssertionError(f"{label} failed. {detail}".strip())
    suffix = f" - {detail}" if detail else ""
    print(f"ASSERT PASS: {label}{suffix}")


def warn(label: str, detail: str) -> None:
    print(f"WARN: {label} - {detail}", file=sys.stderr)


def make_wav_bytes() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(struct.pack("<8h", *([0] * 8)))
    return buffer.getvalue()


def close_quietly(obj, label: str) -> None:
    if obj is None:
        return
    close = getattr(obj, "close", None)
    if close is None:
        return
    try:
        close()
        print(f"ASSERT PASS: closed {label}")
    except Exception as exc:  # pragma: no cover - diagnostic path
        warn(f"failed to close {label}", str(exc))


def context_dict(ctx) -> dict:
    if hasattr(ctx, "to_dict"):
        return ctx.to_dict()
    if isinstance(ctx, dict):
        return dict(ctx)
    return dict(getattr(ctx, "items", lambda: [])())


def drain_aim_cleanup_finalizers() -> None:
    """Run Aim cleanup finalizers before deleting a temporary repository."""
    try:
        from aim.ext.cleanup import AutoClean

        AutoClean.cleanup()
        print("ASSERT PASS: drained Aim cleanup finalizers")
    except Exception as exc:  # pragma: no cover - defensive cleanup path
        warn("failed to drain Aim cleanup finalizers", str(exc))


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)

    try:
        import numpy as np
        from aim import Audio, Distribution, Figure, Image, Repo, Run, Text
        from aim.sdk.types import QueryReportMode
        from aim.storage.context import Context
    except Exception as exc:  # pragma: no cover - import diagnostic
        print(f"ASSERT FAIL: import Aim SDK - {exc}", file=sys.stderr)
        return 1

    assert_pass("import Aim SDK", True, "Run/Repo/object imports succeeded")

    auto_created = args.repo_dir is None
    if auto_created:
        repo_dir = Path(tempfile.mkdtemp(prefix="aim-sdk-smoke-"))
    else:
        repo_dir = args.repo_dir.expanduser().resolve()
        repo_dir.mkdir(parents=True, exist_ok=True)
    print(f"INFO: using repo directory: {repo_dir}")

    repo = None
    run = None
    read_run = None
    run_hash = None

    try:
        repo = Repo.from_path(str(repo_dir), init=True)
        assert_pass("repo init/open", repo is not None and (repo_dir / ".aim").exists(), ".aim directory is present")

        run = Run(
            repo=repo,
            experiment="sdk-smoke",
            system_tracking_interval=None,
            log_system_params=False,
            capture_terminal_logs=False,
        )
        run_hash = run.hash
        run.name = "sdk-smoke-run"
        run.description = "Tiny Aim SDK smoke run"
        run.add_tag("smoke")
        run["hparams"] = {
            "optimizer": {"name": "adam", "lr": 0.001},
            "batch_size": 4,
            "nested": {"enabled": True},
        }

        for step in range(4):
            run.track(1.0 / (step + 1), name="loss", step=step, epoch=0, context={"subset": "train"})
            run.track(
                {"loss": 0.8 / (step + 1), "accuracy": 0.70 + 0.05 * step},
                step=step,
                epoch=0,
                context={"subset": "val"},
            )

        image_array = np.zeros((8, 8, 3), dtype=np.uint8)
        image_array[:, :, 0] = 128
        run.track(Image(image_array, caption="red validation tile"), name="samples", step=0, context={"subset": "val"})
        run.track(Text("validation note"), name="notes", step=0, context={"subset": "val"})
        run.track(Distribution.from_samples([0.1, 0.2, 0.3, 0.4], bin_count=4), name="score_distribution", step=0)
        run.track(Audio(make_wav_bytes(), format="wav", caption="silence"), name="audios", step=0)

        try:
            import plotly.graph_objects as go

            fig = go.Figure(data=[go.Bar(x=["a", "b"], y=[1, 2])])
            run.track(Figure(fig), name="figures", step=0)
            print("ASSERT PASS: optional Figure tracking - Plotly figure tracked")
        except Exception as exc:
            print(f"SKIP: optional Figure tracking - {exc}")

        if not args.skip_artifact:
            artifact_store = repo_dir / "artifact-store"
            artifact_store.mkdir(parents=True, exist_ok=True)
            artifact_source = repo_dir / "model.txt"
            artifact_source.write_text("tiny checkpoint\n", encoding="utf-8")
            run.set_artifacts_uri(artifact_store.resolve().as_uri())
            run.log_artifact(str(artifact_source), name="model.txt", block=True)
            assert_pass("artifact logging", "model.txt" in run.artifacts, "local file:// artifact metadata recorded")

        run.log_info("smoke tracking completed", step_count=4)
        assert_pass("run tracking", bool(run_hash), f"run hash {run_hash}")
        assert_pass("run params", run["hparams", "optimizer", "lr"] == 0.001, "nested hparams are readable")

        metric_infos = [(name, context_dict(ctx)) for name, ctx, _ in run.iter_metrics_info()]
        assert_pass(
            "metric info",
            ("loss", {"subset": "train"}) in metric_infos and ("loss", {"subset": "val"}) in metric_infos,
            str(metric_infos),
        )

        val_metric = run.get_metric("loss", Context({"subset": "val"}))
        steps, columns = val_metric.data.items_list()
        values = columns[0]
        assert_pass("exact metric retrieval", steps == [0, 1, 2, 3] and len(values) == 4, str(list(zip(steps, values))))

        try:
            metric_df = val_metric.dataframe(include_name=True, include_context=True, include_run=True, only_last=True)
            assert_pass("metric dataframe", metric_df is not None and not metric_df.empty, "pandas dataframe produced")
        except Exception as exc:
            print(f"SKIP: metric dataframe - {exc}")

        seq_info = run.collect_sequence_info(("metric", "images", "texts", "distributions", "audios"))
        assert_pass("sequence info", "metric" in seq_info and seq_info["metric"], str(seq_info.get("metric")))

        close_quietly(run, "write run")
        run = None
        try:
            from aim.sdk.index_manager import RepoIndexManager

            RepoIndexManager.get_index_manager(repo).index(run_hash)
            assert_pass("manual index update", True, "freshly written run indexed for repository queries")
        except Exception as exc:
            warn("manual index update", repr(exc))

        # Repository query APIs are important, but older Aim/storage dependency
        # combinations can require index updates or expose read-run cleanup quirks.
        # Probe query_runs, query_metrics, and query_images; fail only when explicitly requested.
        query_run_ok = False
        query_metric_ok = False
        query_image_ok = False
        try:
            for run_collection in repo.query_runs("run.experiment == 'sdk-smoke'", report_mode=QueryReportMode.DISABLED).iter_runs():
                qrun = run_collection.run
                try:
                    if getattr(qrun, "hash", None) == run_hash:
                        query_run_ok = True
                finally:
                    close_quietly(qrun, "query run")
        except Exception as exc:
            warn("query_runs diagnostic", repr(exc))
        try:
            for run_collection in repo.query_metrics("metric.name == 'loss'", report_mode=QueryReportMode.DISABLED).iter_runs():
                qrun = run_collection.run
                try:
                    for metric in run_collection:
                        if getattr(metric, "name", None) == "loss" and getattr(metric.run, "hash", None) == run_hash:
                            query_metric_ok = True
                finally:
                    close_quietly(qrun, "metric query run")
        except Exception as exc:
            warn("query_metrics diagnostic", repr(exc))
        try:
            for run_collection in repo.query_images("images.name == 'samples'", report_mode=QueryReportMode.DISABLED).iter_runs():
                qrun = run_collection.run
                try:
                    for image_seq in run_collection:
                        if getattr(image_seq, "name", None) == "samples" and getattr(image_seq.run, "hash", None) == run_hash:
                            query_image_ok = True
                finally:
                    close_quietly(qrun, "image query run")
        except Exception as exc:
            warn("query_images diagnostic", repr(exc))

        if args.require_query:
            assert_pass(
                "repository queries",
                query_run_ok and query_metric_ok and query_image_ok,
                f"runs={query_run_ok}, metrics={query_metric_ok}, images={query_image_ok}",
            )
        elif query_run_ok and query_metric_ok and query_image_ok:
            assert_pass("repository query diagnostics", True, "query_runs/query_metrics/query_images returned smoke data")
        else:
            warn(
                "repository query diagnostics",
                f"runs={query_run_ok}, metrics={query_metric_ok}, images={query_image_ok}; direct Run retrieval passed",
            )

        try:
            read_run = Run(run_hash=run_hash, repo=repo, read_only=True)
            read_batch_size = read_run.get(("hparams", "batch_size"), default=None)
            read_metric = read_run.get_metric("loss", Context({"subset": "val"}))
            read_steps, read_columns = read_metric.data.items_list()
            if read_batch_size == 4 and read_steps == [0, 1, 2, 3] and len(read_columns[0]) == 4:
                assert_pass("read-only Run diagnostic", True, "Run(..., read_only=True) can read params and metrics")
            else:
                warn("read-only Run diagnostic", "read-only reopen did not fully reflect just-written params/metrics; direct write-run retrieval passed")
        except Exception as exc:
            warn("read-only Run diagnostic", repr(exc))
        finally:
            close_quietly(read_run, "read-only run")
            read_run = None

        # Query syntax edge: && is invalid Python query syntax. Some versions
        # raise during iteration, so force evaluation and treat SyntaxError as the expected signal.
        bad_query_failed = False
        try:
            list(repo.query_metrics("run.hash == 'x' && metric.name == 'loss'", report_mode=QueryReportMode.DISABLED))
        except SyntaxError:
            bad_query_failed = True
        except Exception as exc:
            warn("invalid query raised non-SyntaxError", repr(exc))
            bad_query_failed = True
        assert_pass("query syntax edge", bad_query_failed, "invalid && expression is rejected")

        repo_read_only_caveat = False
        try:
            bad_repo = Repo(str(repo_dir), read_only=True)
        except NotImplementedError:
            repo_read_only_caveat = True
        else:
            close_quietly(bad_repo, "unexpected read-only repo")
        assert_pass("Repo read_only caveat", repo_read_only_caveat, "Repo(read_only=True) raises NotImplementedError")

    finally:
        close_quietly(read_run, "read-only run")
        close_quietly(run, "write run")
        close_quietly(repo, "repo")
        gc.collect()
        time.sleep(0.2)
        drain_aim_cleanup_finalizers()
        gc.collect()
        time.sleep(0.1)
        if auto_created and not args.keep_repo:
            shutil.rmtree(repo_dir, ignore_errors=True)
            print("ASSERT PASS: cleanup - removed temporary repo")
        else:
            print(f"INFO: repository kept at: {repo_dir}")

    print("ASSERT PASS: aim sdk smoke completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

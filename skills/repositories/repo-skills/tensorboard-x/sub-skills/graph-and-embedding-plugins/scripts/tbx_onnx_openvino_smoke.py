#!/usr/bin/env python3
"""Local ONNX/OpenVINO tensorboardX smoke check.

This script performs no network access. It validates a local OpenVINO XML graph
and, when provided, a local ONNX model path.
"""

from __future__ import annotations

import argparse
import contextlib
import pathlib
import tempfile
from textwrap import dedent


def _make_minimal_openvino_xml(path: pathlib.Path) -> None:
    path.write_text(
        dedent(
            """\
            <?xml version="1.0" ?>
            <net batch="1" name="tiny" version="6">
              <layers>
                <layer id="0" name="input" precision="FP32" type="Input">
                  <output>
                    <port id="0"><dim>1</dim><dim>1</dim><dim>1</dim><dim>1</dim></port>
                  </output>
                </layer>
                <layer id="1" name="relu" precision="FP32" type="ReLU">
                  <input>
                    <port id="0"><dim>1</dim><dim>1</dim><dim>1</dim><dim>1</dim></port>
                  </input>
                  <output>
                    <port id="1"><dim>1</dim><dim>1</dim><dim>1</dim><dim>1</dim></port>
                  </output>
                </layer>
              </layers>
              <edges>
                <edge from-layer="0" from-port="0" to-layer="1" to-port="0"/>
              </edges>
            </net>
            """
        ),
        encoding="utf-8",
    )


def _import_writer():
    try:
        from tensorboardX import SummaryWriter
    except Exception as exc:  # pragma: no cover - environment guard
        print(f"SKIP: tensorboardX SummaryWriter is unavailable ({exc})")
        return None
    return SummaryWriter


def _run_openvino(logdir: pathlib.Path) -> None:
    SummaryWriter = _import_writer()
    if SummaryWriter is None:
        return

    xml_path = logdir / "tiny_openvino.xml"
    _make_minimal_openvino_xml(xml_path)
    with SummaryWriter(str(logdir)) as writer:
        writer.add_openvino_graph(str(xml_path))

    if not list(logdir.glob("events.out.tfevents.*")):
        raise RuntimeError("OpenVINO smoke completed but no event file was created")
    print("OK: add_openvino_graph parsed a local XML file")


def _run_onnx(onnx_path: pathlib.Path, logdir: pathlib.Path) -> None:
    SummaryWriter = _import_writer()
    if SummaryWriter is None:
        return

    try:
        import onnx  # noqa: F401
    except Exception as exc:
        print(f"SKIP: ONNX is not installed, so the optional ONNX smoke was skipped ({exc})")
        return

    with SummaryWriter(str(logdir)) as writer:
        writer.add_onnx_graph(str(onnx_path))

    if not list(logdir.glob("events.out.tfevents.*")):
        raise RuntimeError("ONNX smoke completed but no event file was created")
    print("OK: add_onnx_graph accepted a local ONNX file")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local tensorboardX ONNX/OpenVINO smoke checks.")
    parser.add_argument("--onnx-path", type=pathlib.Path, help="Optional local ONNX file to test.")
    parser.add_argument("--logdir", type=pathlib.Path, help="Optional output log directory to keep after the run.")
    args = parser.parse_args(argv)

    if args.logdir is not None:
        args.logdir.mkdir(parents=True, exist_ok=True)
        openvino_dir = args.logdir / "openvino"
        openvino_dir.mkdir(parents=True, exist_ok=True)
        _run_openvino(openvino_dir)
        if args.onnx_path is not None:
            onnx_dir = args.logdir / "onnx"
            onnx_dir.mkdir(parents=True, exist_ok=True)
            _run_onnx(args.onnx_path, onnx_dir)
        else:
            print("SKIP: --onnx-path was not provided, so the optional ONNX smoke was skipped")
    else:
        with tempfile.TemporaryDirectory(prefix="tbx-onnx-openvino-") as tmp:
            root = pathlib.Path(tmp)
            openvino_dir = root / "openvino"
            openvino_dir.mkdir(parents=True, exist_ok=True)
            _run_openvino(openvino_dir)
            if args.onnx_path is not None:
                onnx_dir = root / "onnx"
                onnx_dir.mkdir(parents=True, exist_ok=True)
                _run_onnx(args.onnx_path, onnx_dir)
            else:
                print("SKIP: --onnx-path was not provided, so the optional ONNX smoke was skipped")
    return 0


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        raise SystemExit(main())
    raise SystemExit(130)

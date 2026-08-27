#!/usr/bin/env python3
"""Lightweight smoke checks for SwanLab media and custom charts.

The script keeps the happy path tiny and skips optional branches when the
relevant extras are missing.
"""

from __future__ import annotations

import json
import sys
import tempfile
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Callable

from swanlab import vendor
from swanlab.sdk.internal.run.transforms.audio import Audio
from swanlab.sdk.internal.run.transforms.echarts import ECharts
from swanlab.sdk.internal.run.transforms.html import Html
from swanlab.sdk.internal.run.transforms.image import Image
from swanlab.sdk.internal.run.transforms.molecule import Molecule
from swanlab.sdk.internal.run.transforms.object3d import Object3D
from swanlab.sdk.internal.run.transforms.text import Text
from swanlab.sdk.internal.run.transforms.video import Video

GIF_BYTES = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00"
    b"!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


def optional_vendor(name: str) -> Any:
    try:
        return getattr(vendor, name)
    except (ImportError, AttributeError):
        return None


def expect_raises(exc_type: type[BaseException], func: Callable[[], Any], needle: str | None = None) -> None:
    try:
        func()
    except exc_type as exc:
        if needle is not None and needle not in str(exc):
            raise AssertionError(f"Expected {exc_type.__name__} containing {needle!r}, got {exc!r}") from exc
        return
    except Exception as exc:  # pragma: no cover - defensive
        raise AssertionError(f"Expected {exc_type.__name__}, got {type(exc).__name__}: {exc}") from exc
    raise AssertionError(f"Expected {exc_type.__name__} to be raised")


def check_text(tmpdir: Path) -> None:
    text = Text("hello world", caption="greeting")
    assert text.content == "hello world"
    assert text.caption == "greeting"

    nested = Text(text)
    assert nested.content == "hello world"
    assert nested.caption == "greeting"

    item = text.transform(step=1, path=tmpdir)
    assert item.filename.endswith(".txt")
    assert (tmpdir / item.filename).read_text(encoding="utf-8") == "hello world"
    print("OK: Text")


def check_html(tmpdir: Path) -> None:
    html = Html("<h1>Hello</h1>", caption="page")
    assert html.content == "<h1>Hello</h1>"
    assert html.caption == "page"

    nested = Html(html)
    assert nested.content == "<h1>Hello</h1>"
    assert nested.caption == "page"

    file_path = tmpdir / "page.html"
    file_path.write_text("<p>from file</p>", encoding="utf-8")
    assert Html(file_path).content == "<p>from file</p>"
    assert Html(StringIO("<p>stream</p>")).content == "<p>stream</p>"
    assert Html(BytesIO(b"<p>bytes</p>")).content == "<p>bytes</p>"

    long_content = "<body>" + ("x" * 5000) + "</body>.html"
    assert Html(long_content).content == long_content

    expect_raises(FileNotFoundError, lambda: Html(tmpdir / "missing.html"), "HTML file not found")
    expect_raises(TypeError, lambda: Html(12345), "Unsupported HTML data type")

    item = html.transform(step=2, path=tmpdir)
    assert item.filename.endswith(".html")
    assert item.caption == "page"
    print("OK: Html")


def check_video(tmpdir: Path) -> None:
    if optional_vendor("moviepy") is None:
        print("SKIP: moviepy unavailable; current GIF-only Video smoke does not need it.")

    video = Video(GIF_BYTES, caption="clip")
    assert video.format == "gif"
    assert video.caption == "clip"
    nested = Video(video)
    assert nested.format == "gif"
    assert nested.caption == "clip"
    assert nested.buffer.getvalue() == GIF_BYTES

    item = video.transform(step=3, path=tmpdir)
    assert item.filename.endswith(".gif")
    assert (tmpdir / item.filename).read_bytes() == GIF_BYTES

    expect_raises(TypeError, lambda: Video(b"not-a-video"), "Cannot detect video format")
    expect_raises(TypeError, lambda: Video(12345), "Unsupported type")

    wrong_ext = tmpdir / "clip.mp4"
    wrong_ext.write_bytes(b"\x00" * 16)
    expect_raises(TypeError, lambda: Video(str(wrong_ext)), "Unsupported file extension")

    bad_magic = tmpdir / "fake.gif"
    bad_magic.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 16)
    expect_raises(TypeError, lambda: Video(str(bad_magic)), "magic number")

    expect_raises(ValueError, lambda: Video(str(tmpdir / "missing.gif")), "Failed to open file")
    print("OK: Video")


def check_custom_charts(tmpdir: Path) -> None:
    try:
        import pyecharts.charts as pyecharts_charts
        from swanlab.sdk.internal.run.transforms.echarts.components import Table as SwanTable
    except ImportError:
        print("SKIP: pyecharts unavailable; custom chart smoke skipped.")
        return

    bar = pyecharts_charts.Bar().add_xaxis(["a", "b"]).add_yaxis("series", [1, 2])
    wrapped = ECharts(bar, caption="bar")
    assert wrapped.caption == "bar"
    assert callable(getattr(bar, "dump_options", None))
    item = wrapped.transform(step=4, path=tmpdir)
    assert item.filename.endswith(".json")
    assert json.loads((tmpdir / item.filename).read_text(encoding="utf-8"))

    table = SwanTable().add(["name", "value"], [["alpha", 1], ["beta", 2]])
    table_json = json.loads(table.dump_options())
    assert table_json["colDefs"][0]["field"] == "name"
    assert table_json["rowData"][0]["name"] == "alpha"

    table_item = ECharts(table).transform(step=5, path=tmpdir)
    assert table_item.filename.endswith(".json")

    expect_raises(TypeError, lambda: ECharts(object()), "dump_options")
    print("OK: ECharts/Table")

    sklearn_mod = optional_vendor("sklearn")
    if sklearn_mod is None:
        print("SKIP: sklearn unavailable; plot helper smoke skipped.")
        return

    from swanlab.sdk.internal.run.transforms import plot as plot_mod

    roc = plot_mod.roc_curve([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8], title=True)
    pr = plot_mod.pr_curve([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8], title=True)
    cm = plot_mod.confusion_matrix([0, 1, 0, 1], [0, 1, 1, 1], ["neg", "pos"], title=True)
    for chart in (roc, pr, cm):
        assert callable(getattr(chart, "dump_options", None))

    print("OK: plot helpers")


def check_image(tmpdir: Path) -> None:
    np = optional_vendor("np")
    pil = optional_vendor("PIL")
    if np is None or pil is None:
        print("SKIP: numpy/Pillow unavailable; image smoke skipped.")
        return

    arr = np.zeros((8, 8, 3), dtype=np.uint8)
    image = Image(arr, caption="blank", size=4)
    item = image.transform(step=6, path=tmpdir)
    assert item.filename.endswith(".png")
    assert item.caption == "blank"

    pil_image = pil.Image.fromarray(arr)
    assert Image(pil_image).transform(step=7, path=tmpdir).filename.endswith(".png")

    expect_raises(TypeError, lambda: Image(object()), "Unsupported image type")

    broken = tmpdir / "broken.png"
    broken.write_bytes(b"not-an-image")
    expect_raises(ValueError, lambda: Image(str(broken)), "Failed to open image file")
    print("OK: Image")


def check_audio(tmpdir: Path) -> None:
    np = optional_vendor("np")
    soundfile = optional_vendor("soundfile")
    if np is None or soundfile is None:
        print("SKIP: numpy/soundfile unavailable; audio smoke skipped.")
        return

    silence = np.zeros((1, 16), dtype=np.float32)
    audio = Audio(silence, sample_rate=16000, caption="silence")
    item = audio.transform(step=8, path=tmpdir)
    assert item.filename.endswith(".wav")
    assert item.caption == "silence"

    expect_raises(TypeError, lambda: Audio(np.zeros((3, 16), dtype=np.float32)), "1 or 2 channels")
    expect_raises(TypeError, lambda: Audio(np.zeros((1, 16), dtype=np.int8)), "Invalid numpy array dtype")
    expect_raises(TypeError, lambda: Audio(12345), "Unsupported audio type")
    print("OK: Audio")


def check_molecule(tmpdir: Path) -> None:
    if optional_vendor("rdkit") is None:
        print("SKIP: rdkit unavailable; molecule smoke skipped.")
        return

    mol = Molecule("O", caption="water")
    item = mol.transform(step=9, path=tmpdir)
    assert item.filename.endswith(".pdb")
    assert item.caption == "water"

    expect_raises(ValueError, lambda: Molecule("INVALID_SMILES_STRING!!!"), "Could not parse SMILES")

    unsupported = tmpdir / "test.xyz"
    unsupported.write_text("data", encoding="utf-8")
    expect_raises(ValueError, lambda: Molecule(str(unsupported)), "Unsupported file type")

    expect_raises(TypeError, lambda: Molecule(12345), "Unsupported input type")
    print("OK: Molecule")


def check_object3d(tmpdir: Path) -> None:
    np = optional_vendor("np")
    if np is None:
        print("SKIP: numpy unavailable; object3d smoke skipped.")
        return

    cloud = Object3D(np.zeros((8, 3), dtype=np.float64), caption="cloud")
    item = cloud.transform(step=10, path=tmpdir)
    assert item.filename.endswith(".swanlab.pts.json")
    assert item.caption == "cloud"

    expect_raises(TypeError, lambda: Object3D(object()), "Unsupported input type")
    expect_raises(ValueError, lambda: Object3D(np.array([1, 2, 3])), "Unsupported array shape")
    expect_raises(ValueError, lambda: Object3D({"boxes": []}), "must contain 'points' key")
    expect_raises(FileNotFoundError, lambda: Object3D(str(tmpdir / "missing.glb")), "File not found")
    print("OK: Object3D")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        check_text(tmpdir)
        check_html(tmpdir)
        check_video(tmpdir)
        check_custom_charts(tmpdir)
        check_image(tmpdir)
        check_audio(tmpdir)
        check_molecule(tmpdir)
        check_object3d(tmpdir)

    print("OK: lightweight media smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

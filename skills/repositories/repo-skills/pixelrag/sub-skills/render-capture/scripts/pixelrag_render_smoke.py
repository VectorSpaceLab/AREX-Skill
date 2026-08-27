#!/usr/bin/env python3
"""Local-only PixelRAG render smoke helper.

Default mode prints the fixture and command plan without launching a browser.
Use --run to render a tiny local HTML file with pixelrag_render.render_file and
assert that tiles.json plus at least one tile image are produced.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

HTML = """<!doctype html>
<html><head><meta charset='utf-8'><title>PixelRAG smoke</title></head>
<body><h1>PixelRAG render smoke</h1>{paras}</body></html>"""


def make_fixture(root: Path) -> Path:
    html = root / "pixelrag_render_smoke.html"
    html.write_text(
        HTML.format(paras="\n".join(f"<p>line {i}</p>" for i in range(80))),
        encoding="utf-8",
    )
    return html


def run_render(workdir: Path, keep: bool) -> int:
    from pixelrag_render import render_file

    html = make_fixture(workdir)
    out = workdir / "tiles"
    dirs = render_file(html, out, tile_height=1000, viewport_width=875)
    if not dirs:
        raise SystemExit("render_file returned no tile directories")
    tile_dir = Path(dirs[0])
    manifest = tile_dir / "tiles.json"
    if not manifest.exists():
        raise SystemExit(f"missing tiles.json in {tile_dir}")
    tiles = sorted(tile_dir.glob("tile_*.*"))
    if not tiles:
        raise SystemExit(f"no tile images found in {tile_dir}")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    print(f"PASS rendered {len(tiles)} tile(s) in {tile_dir}")
    print(f"manifest keys: {sorted(data)}")
    if keep:
        print(f"kept workdir: {workdir}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="actually render the local HTML fixture")
    parser.add_argument("--workdir", type=Path, help="directory for fixture/output; defaults to a temp dir")
    parser.add_argument("--keep", action="store_true", help="do not delete the temp workdir")
    args = parser.parse_args()

    if not args.run:
        print("Dry run: would create a local HTML fixture and call pixelrag_render.render_file(...).")
        print("Run with --run to execute the smoke test. No external URLs are fetched.")
        return 0

    if args.workdir:
        args.workdir.mkdir(parents=True, exist_ok=True)
        return run_render(args.workdir, keep=True)

    tmp = Path(tempfile.mkdtemp(prefix="pixelrag-render-smoke-"))
    try:
        return run_render(tmp, keep=args.keep)
    finally:
        if not args.keep:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

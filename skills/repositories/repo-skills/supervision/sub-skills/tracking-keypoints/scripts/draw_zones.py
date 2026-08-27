#!/usr/bin/env python3
"""Interactively draw polygon-zone coordinates on an image or first video frame.

This helper is intentionally standalone: it uses only the Python standard
library plus an installed `supervision` runtime and its dependencies. It opens a
local GUI window, so it requires a display-capable desktop/session and an
OpenCV-compatible backend for image/video loading and drawing. Native OpenCV is
recommended for broad video support; Supervision's fallback backend may work for
simple image cases but can behave differently.

Controls:
    left click: add a vertex to the current polygon
    Return / keypad Enter: close the current polygon
    Escape: clear the unfinished polygon
    s: save polygons as JSON and exit
    q: quit without saving
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

KEY_ENTER = {"Return", "KP_Enter"}
KEY_ESCAPE = "Escape"
KEY_QUIT = "q"
KEY_SAVE = "s"
WINDOW_NAME = "Draw Zones"


class ZoneDrawingSession:
    """Manage interactive polygon drawing state for one source frame."""

    def __init__(
        self,
        image: Any,
        window: Any,
        sv_module: Any,
        cv2_module: Any,
        thickness: int,
    ) -> None:
        self.original_image = image.copy()
        self.image = image.copy()
        self.window = window
        self.sv = sv_module
        self.cv2 = cv2_module
        self.thickness = thickness
        self.polygons: list[list[tuple[int, int]]] = [[]]
        self.current_mouse_position: tuple[int, int] | None = None

    def mouse_event(self, x: int, y: int, event_type: str) -> None:
        """Record mouse movement and append left-click vertices."""
        if event_type == "move":
            self.current_mouse_position = (x, y)
        elif event_type == "down":
            self.polygons[-1].append((x, y))

    def redraw(self) -> None:
        """Redraw finished polygons plus the unfinished preview segment."""
        self.image[:] = self.original_image.copy()
        for index, polygon in enumerate(self.polygons):
            is_finished = index < len(self.polygons) - 1
            color = self._polygon_color(index=index, is_finished=is_finished)
            self._draw_polygon(polygon=polygon, color=color, closed=is_finished)

        current_polygon = self.polygons[-1]
        if current_polygon and self.current_mouse_position is not None:
            self.cv2.line(
                img=self.image,
                pt1=current_polygon[-1],
                pt2=self.current_mouse_position,
                color=self.sv.Color.WHITE.as_bgr(),
                thickness=self.thickness,
            )
        self.window.show(self.image)

    def close_current_polygon(self) -> None:
        """Finish the active polygon when it has at least three vertices."""
        if len(self.polygons[-1]) < 3:
            print("Need at least three vertices before closing a polygon.")
            return
        self.polygons.append([])
        self.current_mouse_position = None

    def clear_current_polygon(self) -> None:
        """Discard the unfinished polygon without changing finished polygons."""
        self.polygons[-1] = []
        self.current_mouse_position = None

    def save(self, target_path: Path, indent: int | None) -> None:
        """Write finished polygons as JSON coordinate lists."""
        polygons = [polygon for polygon in self.polygons if len(polygon) >= 3]
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with target_path.open("w", encoding="utf-8") as output_file:
            json.dump(polygons, output_file, indent=indent)
            output_file.write("\n")
        print(f"Saved {len(polygons)} polygon(s) to {target_path}")

    def run(self, target_path: Path, indent: int | None) -> bool:
        """Run the GUI loop and return True only when polygons were saved."""
        self.window.set_mouse_callback(self.mouse_event)
        self.window.show(self.image)
        saved = False
        try:
            while self.window.is_open:
                key = self.window.wait_key(20)
                if key in KEY_ENTER:
                    self.close_current_polygon()
                elif key == KEY_ESCAPE:
                    self.clear_current_polygon()
                elif key == KEY_SAVE:
                    self.save(target_path=target_path, indent=indent)
                    saved = True
                    break
                elif key == KEY_QUIT:
                    break
                self.redraw()
        finally:
            self.window.close()
        return saved

    def _polygon_color(self, index: int, is_finished: bool) -> tuple[int, int, int]:
        """Choose a BGR color for a finished polygon or current preview."""
        if not is_finished:
            return self.sv.Color.WHITE.as_bgr()
        return self.sv.ColorPalette.DEFAULT.by_idx(index).as_bgr()

    def _draw_polygon(
        self,
        polygon: Sequence[tuple[int, int]],
        color: tuple[int, int, int],
        closed: bool,
    ) -> None:
        """Draw polygon edges into the mutable session image."""
        if len(polygon) < 2:
            return
        for start, end in zip(polygon[:-1], polygon[1:]):
            self.cv2.line(
                img=self.image,
                pt1=start,
                pt2=end,
                color=color,
                thickness=self.thickness,
            )
        if closed:
            self.cv2.line(
                img=self.image,
                pt1=polygon[-1],
                pt2=polygon[0],
                color=color,
                thickness=self.thickness,
            )


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser without importing supervision."""
    parser = argparse.ArgumentParser(
        description=(
            "Interactively draw polygon zones on an image or the first frame of "
            "a video and save JSON coordinates. Requires a GUI display and a "
            "supervision/OpenCV-compatible image backend."
        ),
        epilog=(
            "Controls: left-click adds vertices; Return/KP_Enter closes the "
            "current polygon; Escape clears it; s saves; q quits without saving."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Path to a local image or video file. Videos use the first decoded frame.",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Path where polygon JSON should be written.",
    )
    parser.add_argument(
        "--window-name",
        default=WINDOW_NAME,
        help="Title for the interactive drawing window.",
    )
    parser.add_argument(
        "--thickness",
        type=int,
        default=2,
        help="Line thickness in pixels.",
    )
    parser.add_argument(
        "--json-indent",
        type=int,
        default=2,
        help="Indentation for the saved JSON file. Use a negative value for compact JSON.",
    )
    parser.add_argument(
        "--stretch-window",
        action="store_true",
        help="Stretch the displayed image to the window instead of preserving aspect ratio.",
    )
    return parser


def load_runtime_modules() -> tuple[Any, Any]:
    """Import supervision and its OpenCV-compatible backend after parsing args."""
    try:
        import supervision as sv
        from supervision import _cv2 as cv2
    except Exception as exc:  # pragma: no cover - depends on user runtime
        message = (
            "Unable to import supervision and its OpenCV-compatible backend. "
            "Install supervision in the active environment before running this helper."
        )
        raise RuntimeError(message) from exc
    return sv, cv2


def resolve_source(source_path: Path, sv_module: Any, cv2_module: Any) -> Any:
    """Load a local image or the first frame of a local video file."""
    if not source_path.exists():
        raise FileNotFoundError(f"Source file does not exist: {source_path}")

    image = cv2_module.imread(str(source_path))
    if image is not None:
        return image

    try:
        frame_generator = sv_module.get_video_frames_generator(
            source_path=str(source_path),
        )
        return next(frame_generator)
    except StopIteration as exc:
        raise RuntimeError(f"No frames could be decoded from: {source_path}") from exc
    except Exception as exc:
        message = (
            f"Could not load {source_path} as an image or decode its first video frame. "
            "Check the file path, codec support, and OpenCV/fallback backend."
        )
        raise RuntimeError(message) from exc


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments, open the drawing window, and save polygons on request."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.thickness <= 0:
        parser.error("--thickness must be a positive integer")
    if args.json_indent < 0:
        indent: int | None = None
    else:
        indent = args.json_indent

    try:
        sv_module, cv2_module = load_runtime_modules()
        image = resolve_source(
            source_path=args.source,
            sv_module=sv_module,
            cv2_module=cv2_module,
        )
        window = sv_module.ImageWindow(
            args.window_name,
            keep_aspect_ratio=not args.stretch_window,
        )
        session = ZoneDrawingSession(
            image=image,
            window=window,
            sv_module=sv_module,
            cv2_module=cv2_module,
            thickness=args.thickness,
        )
        saved = session.run(target_path=args.output, indent=indent)
    except Exception as exc:  # pragma: no cover - depends on GUI/runtime
        print(f"draw_zones.py: {exc}", file=sys.stderr)
        print(
            "This helper requires a GUI-capable session and a working "
            "supervision/OpenCV-compatible image backend.",
            file=sys.stderr,
        )
        return 2

    return 0 if saved else 1


if __name__ == "__main__":
    raise SystemExit(main())

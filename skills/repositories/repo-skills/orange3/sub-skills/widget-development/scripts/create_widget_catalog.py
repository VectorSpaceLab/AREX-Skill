#!/usr/bin/env python3
"""Create a widget catalog from an installed Orange package.

This is a self-contained adaptation of Orange's repository catalog helper for
agent/runtime use. It discovers widgets through Orange Canvas entry points,
optionally renders 50x50 PNG icons, and writes a JSON catalog. It discovers
from the installed Orange package and does not read repository files.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from copy import copy
from pathlib import Path
from typing import Iterable, Optional


def _import_qt_for_graphics(include_help: bool, include_icons: bool):
    """Import Qt modules lazily and before QApplication is created."""
    webengine_error = None
    if include_help:
        try:
            # QWebEngineWidgets must be imported before QCoreApplication exists.
            import AnyQt.QtWebEngineWidgets  # noqa: F401  pylint: disable=unused-import,import-outside-toplevel
        except Exception as exc:  # pragma: no cover - depends on optional QtWebEngine install
            webengine_error = exc

    if include_help or include_icons:
        # Rendering icons and initializing HelpManager are non-interactive.
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from AnyQt.QtCore import QRectF, Qt, QTimer  # pylint: disable=import-outside-toplevel
        from AnyQt.QtGui import QImage, QPainter  # pylint: disable=import-outside-toplevel
        from AnyQt.QtWidgets import (  # pylint: disable=import-outside-toplevel
            QApplication,
            QGraphicsScene,
            QGraphicsView,
            QHBoxLayout,
            QWidget,
        )
        from orangecanvas.canvas.items import NodeItem  # pylint: disable=import-outside-toplevel
    else:
        QRectF = Qt = QTimer = QImage = QPainter = QApplication = None
        QGraphicsScene = QGraphicsView = QHBoxLayout = QWidget = NodeItem = None

    return {
        "webengine_error": webengine_error,
        "QRectF": QRectF,
        "Qt": Qt,
        "QTimer": QTimer,
        "QImage": QImage,
        "QPainter": QPainter,
        "QApplication": QApplication,
        "QGraphicsScene": QGraphicsScene,
        "QGraphicsView": QGraphicsView,
        "QHBoxLayout": QHBoxLayout,
        "QWidget": QWidget,
        "NodeItem": NodeItem,
    }


def _ensure_app(qt):
    QApplication = qt["QApplication"]
    Qt = qt["Qt"]
    if QApplication is None:
        return None
    app = QApplication.instance()
    if app is None:
        for attr in (
            "AA_EnableHighDpiScaling",
            "AA_UseHighDpiPixmaps",
            "AA_ShareOpenGLContexts",
        ):
            if hasattr(Qt, attr):
                QApplication.setAttribute(getattr(Qt, attr))
        app = QApplication([])
    return app


def discover_registry():
    """Return a populated Orange widget registry."""
    from Orange.canvas.config import Config as OConfig  # pylint: disable=import-outside-toplevel
    from orangecanvas.registry import WidgetRegistry  # pylint: disable=import-outside-toplevel

    registry = WidgetRegistry()
    discovery = OConfig.widget_discovery(registry)
    discovery.run(OConfig.widgets_entry_points())

    # Orange's original catalog helper normalizes category.widgets from the
    # registry internals after discovery. Keep the behavior because registry
    # categories can otherwise appear empty when iterated by catalog tooling.
    for category, widgets in getattr(registry, "_categories_dict", {}).values():
        category.widgets = widgets
    return registry


def iter_categories(registry, categories: Optional[Iterable[str]] = None):
    wanted = None if categories is None else {name.strip() for name in categories if name.strip()}
    for category in registry.categories():
        if wanted is None or category.name in wanted:
            yield category


def signal_to_dict(signal):
    return {
        "name": getattr(signal, "name", None),
        "type": getattr(getattr(signal, "type", None), "__name__", str(getattr(signal, "type", ""))),
        "default": bool(getattr(signal, "default", False)),
        "explicit": bool(getattr(signal, "explicit", False)),
        "dynamic": bool(getattr(signal, "dynamic", False)),
    }


class IconRenderer:
    def __init__(self, qt):
        self.qt = qt
        self.widget = IconWidget(qt)

    def render(self, widget_description, category_description, filename: Path):
        desc = copy(widget_description)
        desc.inputs = []
        desc.outputs = []
        self.widget.set_widget(desc, category_description)
        self.widget.render_as_png(filename)


class IconWidget:  # constructed dynamically with Qt classes from _import_qt_for_graphics
    def __init__(self, qt):
        self.qt = qt
        QWidget = qt["QWidget"]
        QHBoxLayout = qt["QHBoxLayout"]
        QGraphicsView = qt["QGraphicsView"]
        QGraphicsScene = qt["QGraphicsScene"]

        class _Widget(QWidget):
            pass

        self.widget = _Widget()
        self.widget.setLayout(QHBoxLayout())
        self.widget.layout().setContentsMargins(0, 0, 0, 0)
        self.widget.setFixedSize(50, 50)
        view = QGraphicsView()
        self.widget.layout().addWidget(view)
        self.scene = QGraphicsScene(view)
        view.setScene(self.scene)

    def set_widget(self, widget_description, category_description):
        NodeItem = self.qt["NodeItem"]
        self.scene.clear()
        node = NodeItem(widget_description)
        if category_description is not None:
            node.setWidgetCategory(category_description)
        self.scene.addItem(node)

    def render_as_png(self, filename: Path):
        QImage = self.qt["QImage"]
        QPainter = self.qt["QPainter"]
        QRectF = self.qt["QRectF"]
        Qt = self.qt["Qt"]
        filename.parent.mkdir(parents=True, exist_ok=True)
        img = QImage(50, 50, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing, True)
        self.scene.render(painter, QRectF(0, 0, 50, 50), QRectF(-25, -25, 50, 50))
        painter.end()
        if not img.save(str(filename)):
            raise RuntimeError(f"failed to save icon: {filename}")


class WidgetCatalog:
    def __init__(
        self,
        output_dir: Path,
        *,
        image_url_prefix: str = "",
        categories: Optional[list[str]] = None,
        include_icons: bool = True,
        include_help: bool = True,
        help_timeout_ms: int = 5000,
    ):
        self.output_dir = output_dir
        self.image_url_prefix = image_url_prefix or ""
        self.categories = categories
        self.include_icons = include_icons
        self.include_help = include_help
        self.help_timeout_ms = help_timeout_ms

        self.qt = _import_qt_for_graphics(include_help=include_help, include_icons=include_icons)
        if self.qt["webengine_error"] is not None:
            print(
                "warning: Qt WebEngine is unavailable; help URLs will be omitted "
                f"({self.qt['webengine_error']})",
                file=sys.stderr,
            )
            self.include_help = False

        self.app = _ensure_app(self.qt)
        self.registry = discover_registry()
        self.help_manager = self._init_help_manager() if self.include_help else None
        self.icon_renderer = IconRenderer(self.qt) if self.include_icons else None

    def _init_help_manager(self):
        from orangecanvas.help import HelpManager  # pylint: disable=import-outside-toplevel

        manager = HelpManager()
        manager.set_registry(self.registry)
        if self.app is not None:
            self.qt["QTimer"].singleShot(self.help_timeout_ms, self.app.quit)
            self.app.exec()
        return manager

    def create(self, *, indent: int = 2):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        result = []
        for category in iter_categories(self.registry, self.categories):
            widgets = []
            result.append({"category": category.name, "widgets": widgets})
            for widget in getattr(category, "widgets", []):
                icon = self._render_icon(widget, category) if self.include_icons else None
                widgets.append({
                    "text": getattr(widget, "name", None),
                    "qualified_name": getattr(widget, "qualified_name", None),
                    "project_name": getattr(widget, "project_name", None),
                    "description": getattr(widget, "description", None),
                    "doc": self._get_help(widget),
                    "img": icon,
                    "keyword": getattr(widget, "keywords", None),
                    "inputs": [signal_to_dict(sig) for sig in getattr(widget, "inputs", [])],
                    "outputs": [signal_to_dict(sig) for sig in getattr(widget, "outputs", [])],
                })
        output = self.output_dir / "widgets.json"
        output.write_text(json.dumps(result, indent=indent, sort_keys=False), encoding="utf-8")
        return output

    def _render_icon(self, widget, category):
        assert self.icon_renderer is not None
        qualified_name = getattr(widget, "qualified_name", None) or getattr(widget, "name", "widget")
        safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in qualified_name)
        filename = Path("icons") / f"{safe_name}.png"
        self.icon_renderer.render(widget, category, self.output_dir / filename)
        return self.image_url_prefix + str(filename).replace(os.sep, "/")

    def _get_help(self, widget):
        if self.help_manager is None:
            return None
        query = {"id": getattr(widget, "qualified_name", None)}
        try:
            return self.help_manager.search(query).url()
        except Exception:  # help entries are optional
            return None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Create widgets.json and optional icon PNGs from Orange Canvas widget discovery."
    )
    parser.add_argument("--output", "-o", type=Path, help="directory where widgets.json is written")
    parser.add_argument("--url-prefix", default="", help="prefix prepended to icon paths in widgets.json")
    parser.add_argument("--categories", help="comma-separated category-name filter, e.g. Data,Transform")
    parser.add_argument("--no-icons", action="store_true", help="do not render widget icon PNGs")
    parser.add_argument("--no-help", action="store_true", help="do not initialize HelpManager or WebEngine")
    parser.add_argument("--list-categories", action="store_true", help="print discovered categories and exit")
    parser.add_argument("--help-timeout-ms", type=int, default=5000, help="Qt event-loop timeout for help URL lookup")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation")
    args = parser.parse_args(argv)
    if not args.list_categories and args.output is None:
        parser.error("--output is required unless --list-categories is used")
    return args


def main(argv=None):
    args = parse_args(argv)
    categories = args.categories.split(",") if args.categories else None

    if args.list_categories:
        registry = discover_registry()
        for category in iter_categories(registry, categories):
            print(f"{category.name}\t{len(getattr(category, 'widgets', []))}")
        return 0

    catalog = WidgetCatalog(
        args.output,
        image_url_prefix=args.url_prefix,
        categories=categories,
        include_icons=not args.no_icons,
        include_help=not args.no_help,
        help_timeout_ms=args.help_timeout_ms,
    )
    output = catalog.create(indent=args.indent)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

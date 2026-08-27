#!/usr/bin/env python3
"""Show how to embed Folium maps in a small Flask app.

The script keeps the app construction local and only starts the server when
--serve is passed. That makes it safe to inspect with --help or import for
reference without launching a web server.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

import folium


def build_app() -> Any:
    try:
        from flask import Flask, render_template_string
    except ImportError as exc:  # pragma: no cover - exercised only when serving
        raise SystemExit(
            "This example needs Flask. Install it with 'python -m pip install flask'."
        ) from exc

    app = Flask(__name__)

    @app.route("/")
    def fullscreen():
        m = folium.Map()
        return m.get_root().render()

    @app.route("/iframe")
    def iframe():
        m = folium.Map()
        m.get_root().width = "800px"
        m.get_root().height = "600px"
        iframe_html = m.get_root()._repr_html_()
        return render_template_string(
            """
            <!DOCTYPE html>
            <html>
              <head><title>Folium iframe demo</title></head>
              <body>
                <h1>Using an iframe</h1>
                {{ iframe|safe }}
              </body>
            </html>
            """,
            iframe=iframe_html,
        )

    @app.route("/components")
    def components():
        m = folium.Map(width=800, height=600)
        m.get_root().render()
        header = m.get_root().header.render()
        body_html = m.get_root().html.render()
        script = m.get_root().script.render()
        return render_template_string(
            """
            <!DOCTYPE html>
            <html>
              <head>
                {{ header|safe }}
              </head>
              <body>
                <h1>Using components</h1>
                {{ body_html|safe }}
                <script>
                  {{ script|safe }}
                </script>
              </body>
            </html>
            """,
            header=header,
            body_html=body_html,
            script=script,
        )

    return app


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Show how to embed Folium maps in a Flask app.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the Flask development server.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind when serving.")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind when serving.")
    parser.add_argument("--debug", action="store_true", help="Run Flask in debug mode.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.serve:
        print("Flask is optional for this example. Re-run with --serve to start the demo server.")
        print("Routes: /, /iframe, /components")
        return 0

    app = build_app()
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

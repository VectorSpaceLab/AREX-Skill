#!/usr/bin/env python3
"""Write a deterministic Sweetviz override INI template.

The helper imports only the Python standard library. It does not import
Sweetviz, open browsers, contact networks, or read credentials. Existing output
files are not overwritten unless --overwrite is supplied.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


LAYOUT_CHOICES = ("widescreen", "vertical")
VERBOSITY_CHOICES = ("full", "progress_only", "off")


def positive_float(text: str) -> str:
    try:
        value = float(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected a floating-point number, got {text!r}") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError("scale values must be positive")
    return text


def escape_ini_percent(text: str) -> str:
    """ConfigParser interpolation requires %% for literal percent signs."""
    return text if "%%" in text else text.replace("%", "%%")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write a Sweetviz 2.3.3 override INI template with safe, common defaults."
    )
    parser.add_argument("--output", required=True, help="INI file to create.")
    parser.add_argument(
        "--html-layout",
        choices=LAYOUT_CHOICES,
        default="widescreen",
        help="Default show_html layout. Default: widescreen.",
    )
    parser.add_argument(
        "--html-scale",
        type=positive_float,
        default="1.0",
        help="Default show_html scale. Default: 1.0.",
    )
    parser.add_argument(
        "--notebook-layout",
        choices=LAYOUT_CHOICES,
        default="vertical",
        help="Default show_notebook layout. Default: vertical.",
    )
    parser.add_argument(
        "--notebook-scale",
        type=positive_float,
        default="1.0",
        help="Default show_notebook scale. Default: 1.0.",
    )
    parser.add_argument(
        "--notebook-width",
        default="100%",
        help="Default notebook iframe width. Percent signs are escaped for INI output. Default: 100%%.",
    )
    parser.add_argument(
        "--notebook-height",
        default="750",
        help="Default notebook iframe height, such as 750 or Full. Default: 750.",
    )
    parser.add_argument(
        "--verbosity",
        choices=VERBOSITY_CHOICES,
        default="full",
        help="Default report construction verbosity. Default: full.",
    )
    parser.add_argument(
        "--use-cjk-font",
        action="store_true",
        help="Set [General] use_cjk_font = 1 for CJK-compatible plot fonts.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the output file if it already exists.",
    )
    return parser


def render_ini(args: argparse.Namespace) -> str:
    notebook_width = escape_ini_percent(str(args.notebook_width))
    cjk = "1" if args.use_cjk_font else "0"
    return f"""; Sweetviz override INI template.
; Load before constructing a report, for example:
;   import sweetviz as sv
;   sv.config_parser.read("sweetviz_override.ini")
;
; Public sv.analyze() and sv.compare() do not accept a verbosity keyword in
; Sweetviz 2.3.3; set [General] default_verbosity here instead.

[General]
default_verbosity = {args.verbosity}
use_cjk_font = {cjk}
association_min_to_bold = 0.1

[Output_Defaults]
html_layout = {args.html_layout}
html_scale = {args.html_scale}
notebook_layout = {args.notebook_layout}
notebook_scale = {args.notebook_scale}
notebook_width = {notebook_width}
notebook_height = {args.notebook_height}

[Type_Detection]
; Numeric columns with this many or fewer distinct non-null values infer as categorical.
max_numeric_distinct_to_be_categorical = 10
; Text columns infer as categorical only if both text thresholds are satisfied.
max_text_distinct_to_be_categorical = 101
max_text_fraction_distinct_to_be_categorical = 0.33

[Processing]
; pairwise_analysis='auto' warns and returns early above this analyzed feature count.
association_auto_threshold = 200

[Layout]
show_logo = 1
full_page_padding_widescreen = 160
full_page_padding_vertical = 300
character_width_estimate = 6
summary_text_max_width = 618
pair_spacing = 84
col_spacing = 15
summary_top = 150
summary_spacing = 0
summary_height_per_element = 162
summary_vertical_detail_pos = 157
summary_vertical_padding = 8
cat_detail_graph_y = 75
cat_detail_breakdown_y_offset = 9
cat_detail_col_1_max_x = 217
cat_detail_col_x_padding_after_name = 30
cat_detail_col_target_extra_spacing = 15
cat_detail_col_spacing = 81
num_detail_max_listed_values = 15
detail_text_max_width = 800

[comet_ml_defaults]
; Layout defaults only. Comet.ml upload still requires optional comet_ml and credentials.
html_layout = vertical
html_scale = 0.9
"""


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output = Path(args.output)

    if output.exists() and not args.overwrite:
        print(f"ERROR: refusing to overwrite existing file: {output}", file=sys.stderr)
        print("Pass --overwrite to replace it.", file=sys.stderr)
        return 1
    if output.exists() and output.is_dir():
        print(f"ERROR: output path is a directory: {output}", file=sys.stderr)
        return 1

    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_ini(args), encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: could not write override INI: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote Sweetviz override INI: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

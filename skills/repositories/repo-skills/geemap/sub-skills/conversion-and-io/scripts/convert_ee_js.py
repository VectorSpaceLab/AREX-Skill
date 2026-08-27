#!/usr/bin/env python3
"""Safe CLI wrapper for geemap Earth Engine JS/Python/notebook conversion.

The wrapper adapts geemap's conversion helpers but requires explicit input and
output paths. It does not write under a home directory and does not execute
notebooks unless --execute is explicitly supplied.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile
from typing import Iterable


def _path_arg(value: str) -> Path:
    return Path(value).expanduser()


def _load_conversion():
    """Import geemap.conversion with a current-directory package fallback."""
    first_error: ModuleNotFoundError | None = None
    try:
        from geemap import conversion

        return conversion
    except ModuleNotFoundError as exc:
        first_error = exc

    cwd = Path.cwd().resolve()
    if (cwd / "geemap" / "__init__.py").exists():
        sys.path.insert(0, str(cwd))
        try:
            from geemap import conversion

            return conversion
        except ModuleNotFoundError as exc:
            first_error = exc

    missing = getattr(first_error, "name", None) or "unknown"
    raise SystemExit(
        "Cannot import geemap.conversion. Run this script in an environment "
        "where geemap and its required dependencies are installed. "
        f"Missing import: {missing}"
    ) from first_error


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert Earth Engine JavaScript files to Python, Python files to "
            "Jupyter notebooks, or JavaScript directly to notebooks using geemap."
        )
    )
    parser.add_argument(
        "--mode",
        choices=["js-to-py", "py-to-ipynb", "js-to-ipynb", "copy-js-examples"],
        required=True,
        help="Conversion mode. copy-js-examples only requires --output.",
    )
    parser.add_argument(
        "--input",
        type=_path_arg,
        help="Input file or directory. Required except for copy-js-examples.",
    )
    parser.add_argument(
        "--output",
        type=_path_arg,
        required=True,
        help="Output file or directory. Directories are required for directory inputs.",
    )
    parser.add_argument(
        "--template",
        type=_path_arg,
        help="Optional notebook template file for py-to-ipynb/js-to-ipynb.",
    )
    parser.add_argument(
        "--copy-template-to",
        type=_path_arg,
        help="Copy geemap's packaged notebook template to this path before conversion.",
    )
    parser.add_argument(
        "--download-template",
        action="store_true",
        help="When used with --copy-template-to, download the latest template from GitHub.",
    )
    parser.add_argument(
        "--map-var",
        default="m",
        help="Python map variable used when rewriting JavaScript Map.* calls.",
    )
    parser.add_argument(
        "--import-geemap",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Write import geemap and create the map variable in JS-to-Python output.",
    )
    parser.add_argument(
        "--use-qgis",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Write from ee_plugin import Map for QGIS plugin workflows.",
    )
    parser.add_argument(
        "--show-map",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Append the map variable at the end of generated Python scripts.",
    )
    parser.add_argument(
        "--github-username",
        help="Optional username for notebook badge URL rewriting in py-to-ipynb.",
    )
    parser.add_argument(
        "--github-repo",
        help="Optional repository name for notebook badge URL rewriting in py-to-ipynb.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help=(
            "Execute generated notebooks in place after conversion. This may contact "
            "Earth Engine and run arbitrary notebook code."
        ),
    )
    return parser


def _require_input(input_path: Path | None, mode: str) -> Path:
    if input_path is None:
        raise SystemExit(f"--input is required for mode {mode}")
    if not input_path.exists():
        raise SystemExit(f"Input does not exist: {input_path}")
    return input_path.resolve()


def _prepare_output(input_path: Path, output_path: Path, mode: str) -> Path:
    output_path = output_path.resolve()
    if input_path.is_dir():
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path

    if mode == "js-to-py" and output_path.suffix.lower() != ".py":
        raise SystemExit("For a single JS input, --output must be a .py file")
    if mode in {"py-to-ipynb", "js-to-ipynb"} and output_path.suffix.lower() != ".ipynb":
        raise SystemExit("For a single file notebook conversion, --output must be a .ipynb file")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def _notebook_files(path: Path) -> Iterable[Path]:
    if path.is_file() and path.suffix.lower() == ".ipynb":
        yield path
    elif path.is_dir():
        yield from sorted(path.rglob("*.ipynb"))


def _resolve_template(args: argparse.Namespace):
    conversion = _load_conversion()

    if args.copy_template_to is not None:
        copied = conversion.get_nb_template(
            download_latest=args.download_template,
            out_file=args.copy_template_to.resolve(),
        )
        return copied
    if args.template is not None:
        template = args.template.resolve()
        if not template.exists():
            raise SystemExit(f"Template does not exist: {template}")
        return template
    return None


def _copy_js_examples(output_path: Path) -> None:
    conversion = _load_conversion()

    output_path = output_path.resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    copied_to = conversion.get_js_examples(out_dir=output_path)
    print(f"Copied geemap JavaScript examples to: {copied_to}")


def _js_to_py(args: argparse.Namespace) -> Path:
    conversion = _load_conversion()

    if args.use_qgis and args.import_geemap:
        raise SystemExit("Choose either --use-qgis or --import-geemap, not both")

    input_path = _require_input(args.input, args.mode)
    output_path = _prepare_output(input_path, args.output, args.mode)

    if input_path.is_dir():
        conversion.js_to_python_dir(
            str(input_path),
            str(output_path),
            use_qgis=args.use_qgis,
            import_geemap=args.import_geemap,
            Map=args.map_var,
        )
    else:
        conversion.js_to_python(
            str(input_path),
            out_file=str(output_path),
            use_qgis=args.use_qgis,
            show_map=args.show_map,
            import_geemap=args.import_geemap,
            Map=args.map_var,
        )
    return output_path


def _py_to_ipynb(args: argparse.Namespace) -> Path:
    conversion = _load_conversion()

    input_path = _require_input(args.input, args.mode)
    output_path = _prepare_output(input_path, args.output, args.mode)
    template = _resolve_template(args)

    if input_path.is_dir():
        conversion.py_to_ipynb_dir(
            str(input_path),
            template_file=str(template) if template is not None else None,
            out_dir=str(output_path),
            github_username=args.github_username,
            github_repo=args.github_repo,
            Map=args.map_var,
        )
    else:
        conversion.py_to_ipynb(
            str(input_path),
            template_file=str(template) if template is not None else None,
            out_file=str(output_path),
            github_username=args.github_username,
            github_repo=args.github_repo,
            Map=args.map_var,
        )
    return output_path


def _js_to_ipynb(args: argparse.Namespace) -> Path:
    conversion = _load_conversion()

    if args.use_qgis and args.import_geemap:
        raise SystemExit("Choose either --use-qgis or --import-geemap, not both")

    input_path = _require_input(args.input, args.mode)
    output_path = _prepare_output(input_path, args.output, args.mode)
    template = _resolve_template(args)

    with tempfile.TemporaryDirectory(prefix="geemap-js-to-ipynb-") as tmp:
        tmp_dir = Path(tmp)
        if input_path.is_dir():
            py_dir = tmp_dir / "py"
            py_dir.mkdir()
            conversion.js_to_python_dir(
                str(input_path),
                str(py_dir),
                use_qgis=args.use_qgis,
                import_geemap=args.import_geemap,
                Map=args.map_var,
            )
            conversion.py_to_ipynb_dir(
                str(py_dir),
                template_file=str(template) if template is not None else None,
                out_dir=str(output_path),
                github_username=args.github_username,
                github_repo=args.github_repo,
                Map=args.map_var,
            )
        else:
            py_file = tmp_dir / f"{input_path.stem}_geemap.py"
            conversion.js_to_python(
                str(input_path),
                out_file=str(py_file),
                use_qgis=args.use_qgis,
                show_map=args.show_map,
                import_geemap=args.import_geemap,
                Map=args.map_var,
            )
            conversion.py_to_ipynb(
                str(py_file),
                template_file=str(template) if template is not None else None,
                out_file=str(output_path),
                github_username=args.github_username,
                github_repo=args.github_repo,
                Map=args.map_var,
            )
    return output_path


def _execute_generated(path: Path) -> None:
    conversion = _load_conversion()

    notebooks = list(_notebook_files(path))
    if not notebooks:
        raise SystemExit(f"No notebooks found to execute under: {path}")
    for nb in notebooks:
        print(f"Executing notebook in place: {nb}")
        conversion.execute_notebook(str(nb))


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.mode == "copy-js-examples":
        _copy_js_examples(args.output)
        return 0

    if args.mode == "js-to-py":
        result = _js_to_py(args)
    elif args.mode == "py-to-ipynb":
        result = _py_to_ipynb(args)
    elif args.mode == "js-to-ipynb":
        result = _js_to_ipynb(args)
    else:  # pragma: no cover - argparse prevents this.
        parser.error(f"Unsupported mode: {args.mode}")

    print(f"Wrote conversion output under: {result}")
    if args.execute:
        _execute_generated(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

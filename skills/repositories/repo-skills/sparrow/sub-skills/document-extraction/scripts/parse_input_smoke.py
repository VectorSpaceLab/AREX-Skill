#!/usr/bin/env python3
"""No-model smoke checks for Sparrow Parse document input wiring.

The default run uses a fake inference backend and text-only fixture. It does not
load a real VLM, contact a service, download a model, or read a document. Use
--strict when this script is used as a CI gate.
"""

from __future__ import annotations

import argparse
import base64
import inspect
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ONE_PIXEL_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a safe no-model Sparrow Parse input smoke test.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--fixture",
        choices=["text", "image", "pdf-helper"],
        default="text",
        help="Fixture path to exercise. 'pdf-helper' uses PDF splitting without image conversion/poppler.",
    )
    parser.add_argument(
        "--query",
        default="retrieve data based on provided JSON schema. return response in JSON format, by strictly following this JSON schema: {\"smoke\":\"str\"}",
        help="Prepared text_input passed to VLLMExtractor.",
    )
    parser.add_argument("--invalid-json", action="store_true", help="Make the fake backend return malformed JSON to test diagnosis output.")
    parser.add_argument("--apply-annotation", action="store_true", help="Pass apply_annotation=True to run_inference where applicable.")
    parser.add_argument("--crop-size", type=int, default=None, help="Crop size for image fixture. Avoid for one-pixel default unless testing crop errors.")
    parser.add_argument("--debug", action="store_true", help="Pass debug=True to run_inference.")
    parser.add_argument("--check-module-main", action="store_true", help="Also run 'python -m sparrow_parse' and report its result.")
    parser.add_argument("--source-root", default=None, help="Optional package source root to prepend to PYTHONPATH before imports.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when imports or smoke checks fail.")
    parser.add_argument("--output", default="-", help="Output JSON file path, or '-' for stdout.")
    return parser.parse_args()


class FakeInference:
    """Minimal backend implementing the ModelInference.inference shape."""

    def __init__(self, invalid_json: bool = False) -> None:
        self.invalid_json = invalid_json
        self.calls: list[dict[str, Any]] = []

    def inference(self, input_data, apply_annotation=False, ocr_callback=None, mode=None):  # noqa: D401 - shape matches package
        file_value = input_data[0].get("file_path") if input_data else None
        if isinstance(file_value, list):
            file_count = len(file_value)
            missing = [path for path in file_value if not os.path.exists(path)]
        elif file_value is None:
            file_count = 0
            missing = []
        else:
            file_count = 1
            missing = [] if os.path.exists(file_value) else [file_value]

        self.calls.append(
            {
                "file_count": file_count,
                "missing_files": missing,
                "apply_annotation": bool(apply_annotation),
                "ocr_callback_supplied": ocr_callback is not None,
                "mode": mode,
            }
        )
        if missing:
            raise FileNotFoundError(f"Fake fixture missing files: {missing}")
        if self.invalid_json:
            return ["not valid json from fake backend"]
        return [json.dumps({"smoke": "ok", "file_count": file_count, "annotation": bool(apply_annotation)})]


def prepend_source_root(source_root: str | None) -> None:
    if not source_root:
        return
    root = str(Path(source_root).resolve())
    if root not in sys.path:
        sys.path.insert(0, root)


def import_contract() -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    report: dict[str, Any] = {}
    try:
        import sparrow_parse  # type: ignore

        report["sparrow_parse_version"] = getattr(sparrow_parse, "__version__", None)
        report["sparrow_parse_imported"] = True
    except Exception as exc:  # pragma: no cover - depends on environment
        errors.append(f"import sparrow_parse failed: {type(exc).__name__}: {exc}")
        return report, errors

    try:
        from sparrow_parse.extractors.vllm_extractor import VLLMExtractor  # type: ignore

        report["VLLMExtractor.run_inference"] = str(inspect.signature(VLLMExtractor.run_inference))
        report["VLLMExtractor"] = VLLMExtractor
    except Exception as exc:  # pragma: no cover - depends on environment
        errors.append(f"import VLLMExtractor failed: {type(exc).__name__}: {exc}")

    try:
        from sparrow_parse.vlmb.inference_factory import InferenceFactory  # type: ignore

        report["InferenceFactory.__init__"] = str(inspect.signature(InferenceFactory.__init__))
        report["InferenceFactory"] = InferenceFactory
    except Exception as exc:  # pragma: no cover - depends on environment
        errors.append(f"import InferenceFactory failed: {type(exc).__name__}: {exc}")

    return report, errors


def write_tiny_png(directory: Path) -> Path:
    path = directory / "sparrow_parse_smoke.png"
    path.write_bytes(base64.b64decode(ONE_PIXEL_PNG))
    return path


def run_fixture(args: argparse.Namespace, contract: dict[str, Any]) -> dict[str, Any]:
    if args.fixture == "pdf-helper":
        return run_pdf_helper_fixture(contract)

    extractor_cls = contract.get("VLLMExtractor")
    if extractor_cls is None:
        return {"ok": False, "error": "VLLMExtractor unavailable; cannot run fixture."}

    fake = FakeInference(invalid_json=args.invalid_json)
    with tempfile.TemporaryDirectory(prefix="sparrow-parse-smoke-") as tmp:
        tmp_path = Path(tmp)
        if args.fixture == "text":
            input_data = [{"file_path": None, "text_input": args.query}]
        else:
            image_path = write_tiny_png(tmp_path)
            input_data = [{"file_path": str(image_path), "text_input": args.query}]

        try:
            results, num_pages = extractor_cls().run_inference(
                fake,
                input_data,
                tables_only=False,
                generic_query=False,
                crop_size=args.crop_size,
                apply_annotation=args.apply_annotation,
                ocr_callback=None,
                debug_dir=None,
                debug=args.debug,
                mode=None,
            )
        except Exception as exc:
            return {"ok": False, "error": f"fixture execution failed: {type(exc).__name__}: {exc}", "fake_calls": fake.calls}

    json_parse_ok = False
    parsed_result: Any = None
    diagnosis = None
    if results:
        try:
            parsed_result = json.loads(results[0]) if isinstance(results[0], str) else results[0]
            json_parse_ok = True
        except json.JSONDecodeError as exc:
            diagnosis = f"Invalid JSON format in fake backend output at position {exc.pos}."

    expected_json_state = not args.invalid_json
    ok = bool(results) and (json_parse_ok == expected_json_state)
    return {
        "ok": ok,
        "fixture": args.fixture,
        "num_pages": num_pages,
        "results_count": len(results),
        "json_parse_ok": json_parse_ok,
        "parsed_result": parsed_result,
        "diagnosis": diagnosis,
        "fake_calls": fake.calls,
    }


def run_pdf_helper_fixture(contract: dict[str, Any]) -> dict[str, Any]:
    try:
        from pypdf import PdfWriter  # type: ignore
        from sparrow_parse.helpers.pdf_optimizer import PDFOptimizer  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        return {"ok": False, "error": f"pdf helper imports failed: {type(exc).__name__}: {exc}"}

    with tempfile.TemporaryDirectory(prefix="sparrow-parse-pdf-smoke-") as tmp:
        tmp_path = Path(tmp)
        pdf_path = tmp_path / "blank.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        with pdf_path.open("wb") as handle:
            writer.write(handle)
        try:
            num_pages, output_files, temp_dir = PDFOptimizer().split_pdf_to_pages(str(pdf_path), debug_dir=None, convert_to_images=False)
        except Exception as exc:
            return {"ok": False, "error": f"PDFOptimizer split failed: {type(exc).__name__}: {exc}"}
        finally:
            # The helper returns a temp_dir it created; remove it if still present.
            try:
                import shutil

                shutil.rmtree(locals().get("temp_dir", ""), ignore_errors=True)
            except Exception:
                pass
    return {"ok": num_pages == 1 and len(output_files) == 1, "fixture": "pdf-helper", "num_pages": num_pages, "output_files_count": len(output_files)}


def run_module_main(args: argparse.Namespace) -> dict[str, Any] | None:
    if not args.check_module_main:
        return None
    env = os.environ.copy()
    if args.source_root:
        current = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(Path(args.source_root).resolve()) + (os.pathsep + current if current else "")
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "sparrow_parse"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            env=env,
        )
        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    except Exception as exc:  # pragma: no cover - depends on environment
        return {"returncode": None, "error": f"python -m sparrow_parse failed: {type(exc).__name__}: {exc}"}


def sanitize_private_paths(value: Any) -> Any:
    """Redact common local path prefixes from emitted diagnostics."""
    if isinstance(value, dict):
        return {key: sanitize_private_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_private_paths(item) for item in value]
    if isinstance(value, str):
        redacted = value
        for prefix, token in [(str(Path.cwd()), "<cwd>"), (str(Path.home()), "<home>")]:
            if prefix:
                redacted = redacted.replace(prefix, token)
        return redacted
    return value


def emit(report: dict[str, Any], output_path: str) -> None:
    # Avoid serializing class objects stored in the internal contract report.
    cleaned = json.loads(json.dumps(report, default=lambda value: f"<{type(value).__name__}>"))
    cleaned = sanitize_private_paths(cleaned)
    text = json.dumps(cleaned, indent=2, ensure_ascii=False)
    if output_path == "-":
        print(text)
    else:
        Path(output_path).write_text(text + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    prepend_source_root(args.source_root)

    contract, import_errors = import_contract()
    fixture_report = {"ok": False, "error": "Skipped because imports failed."} if import_errors else run_fixture(args, contract)
    module_main = run_module_main(args)

    ok = not import_errors and bool(fixture_report.get("ok"))
    report: dict[str, Any] = {
        "ok": ok,
        "safe_no_model_invocation": True,
        "fixture": args.fixture,
        "strict": args.strict,
        "import_errors": import_errors,
        "contract": {k: v for k, v in contract.items() if not isinstance(v, type)},
        "fixture_report": fixture_report,
        "module_main": module_main,
        "notes": [
            "This smoke uses a fake backend; it does not prove any real VLM model can load.",
            "Use --strict to make failed imports or fixture checks return a non-zero exit code.",
        ],
    }
    emit(report, args.output)
    return 0 if ok or not args.strict else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Create a no-model LangExtract JSONL + HTML visualization round trip.

Purpose:
  Build a handcrafted AnnotatedDocument, save it as JSONL, reload it, convert it
  through langextract.data_lib, and generate interactive HTML. The script never
  calls lx.extract(), never contacts a model provider, and writes only under the
  caller-selected output directory.

Example:
  python save_and_visualize.py --output-dir ./lx-viz-demo
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import langextract as lx
from langextract import data_lib


def _interval_for(text: str, needle: str) -> lx.data.CharInterval:
    """Return the first character interval for an exact substring."""
    start = text.index(needle)
    return lx.data.CharInterval(start_pos=start, end_pos=start + len(needle))


def build_demo_document() -> lx.data.AnnotatedDocument:
    """Build a small annotated document with grounded and ungrounded rows."""
    text = "Patient Alice took 400 mg ibuprofen with water."
    return lx.data.AnnotatedDocument(
        document_id="visualization-demo-1",
        text=text,
        extractions=[
            lx.data.Extraction(
                extraction_class="patient",
                extraction_text="Alice",
                char_interval=_interval_for(text, "Alice"),
                alignment_status=lx.data.AlignmentStatus.MATCH_EXACT,
                attributes={"role": "patient"},
            ),
            lx.data.Extraction(
                extraction_class="dosage",
                extraction_text="400 mg",
                char_interval=_interval_for(text, "400 mg"),
                alignment_status=lx.data.AlignmentStatus.MATCH_EXACT,
                attributes={"unit": "mg"},
            ),
            lx.data.Extraction(
                extraction_class="medication",
                extraction_text="ibuprofen",
                char_interval=_interval_for(text, "ibuprofen"),
                alignment_status=lx.data.AlignmentStatus.MATCH_EXACT,
                attributes={"normalized": "ibuprofen"},
            ),
            # This deliberately has no char_interval to demonstrate that
            # ungrounded rows persist in JSONL but are not highlighted in HTML.
            lx.data.Extraction(
                extraction_class="note",
                extraction_text="taken with juice",
                char_interval=None,
                alignment_status=None,
                attributes={"grounded": "false"},
            ),
        ],
    )


def html_payload(html_content: Any) -> str:
    """Normalize lx.visualize() return values for file writing."""
    return html_content.data if hasattr(html_content, "data") else str(html_content)


def is_highlightable(extraction: lx.data.Extraction) -> bool:
    """Return True when an extraction has a usable visual span."""
    interval = extraction.char_interval
    return (
        interval is not None
        and interval.start_pos is not None
        and interval.end_pos is not None
        and interval.start_pos < interval.end_pos
    )


def positive_float(value: str) -> float:
    """argparse type for positive visualization speeds."""
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a handcrafted LangExtract AnnotatedDocument, save JSONL, "
            "reload it, and write interactive HTML without model calls."
        )
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory where JSONL, HTML, and summary files will be written.",
    )
    parser.add_argument(
        "--jsonl-name",
        default="annotated_documents.jsonl",
        help="JSONL filename to create inside --output-dir.",
    )
    parser.add_argument(
        "--html-name",
        default="visualization.html",
        help="HTML filename to create inside --output-dir.",
    )
    parser.add_argument(
        "--summary-name",
        default="roundtrip_summary.json",
        help="Summary JSON filename to create inside --output-dir.",
    )
    parser.add_argument(
        "--animation-speed",
        type=positive_float,
        default=0.75,
        help="Seconds between highlighted extractions when playback is active.",
    )
    parser.add_argument(
        "--no-legend",
        action="store_true",
        help="Disable the extraction-class legend in the generated HTML.",
    )
    parser.add_argument(
        "--no-gif-optimized",
        action="store_true",
        help="Disable the larger GIF-optimized visualization styling.",
    )
    parser.add_argument(
        "--visualize-from-jsonl-path",
        action="store_true",
        help=(
            "Pass the JSONL path directly to lx.visualize(). By design this "
            "visualizes the first document in the file. The default loads the "
            "file first and visualizes the reloaded AnnotatedDocument."
        ),
    )
    parser.add_argument(
        "--show-progress",
        action="store_true",
        help="Show LangExtract save/load progress bars. Default is quiet.",
    )
    return parser.parse_args()


def reject_path_like_filename(name: str, flag_name: str) -> None:
    """Keep writes constrained to the selected output directory."""
    candidate = Path(name)
    if candidate.is_absolute() or len(candidate.parts) != 1 or name in {"", ".", ".."}:
        raise SystemExit(f"{flag_name} must be a simple filename, got: {name!r}")


def main() -> int:
    args = parse_args()
    for flag_name, value in [
        ("--jsonl-name", args.jsonl_name),
        ("--html-name", args.html_name),
        ("--summary-name", args.summary_name),
    ]:
        reject_path_like_filename(value, flag_name)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = output_dir / args.jsonl_name
    html_path = output_dir / args.html_name
    summary_path = output_dir / args.summary_name

    original_doc = build_demo_document()
    lx.io.save_annotated_documents(
        [original_doc],
        output_dir=output_dir,
        output_name=args.jsonl_name,
        show_progress=args.show_progress,
    )

    reloaded_docs = list(
        lx.io.load_annotated_documents_jsonl(
            jsonl_path,
            show_progress=args.show_progress,
        )
    )
    if len(reloaded_docs) != 1:
        raise RuntimeError(f"expected one reloaded document, got {len(reloaded_docs)}")

    reloaded_doc = reloaded_docs[0]
    round_tripped_doc = data_lib.dict_to_annotated_document(
        data_lib.annotated_document_to_dict(reloaded_doc)
    )

    data_source: lx.data.AnnotatedDocument | Path
    data_source = jsonl_path if args.visualize_from_jsonl_path else round_tripped_doc
    html_content = lx.visualize(
        data_source,
        animation_speed=args.animation_speed,
        show_legend=not args.no_legend,
        gif_optimized=not args.no_gif_optimized,
    )
    html_path.write_text(html_payload(html_content), encoding="utf-8")

    total_extractions = len(round_tripped_doc.extractions or [])
    highlightable_count = sum(
        1 for extraction in (round_tripped_doc.extractions or []) if is_highlightable(extraction)
    )
    summary = {
        "document_id": round_tripped_doc.document_id,
        "jsonl_file": jsonl_path.name,
        "html_file": html_path.name,
        "total_extractions": total_extractions,
        "highlightable_extractions": highlightable_count,
        "ungrounded_extractions": total_extractions - highlightable_count,
        "visualized_from_jsonl_path": bool(args.visualize_from_jsonl_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"Wrote JSONL: {jsonl_path}")
    print(f"Wrote HTML: {html_path}")
    print(f"Wrote summary: {summary_path}")
    print(
        f"Highlightable extractions: {highlightable_count}/{total_extractions} "
        "(rows without char_interval are saved but not highlighted)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

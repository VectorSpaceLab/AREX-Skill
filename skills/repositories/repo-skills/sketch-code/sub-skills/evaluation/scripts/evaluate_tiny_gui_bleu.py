#!/usr/bin/env python3
"""Self-contained SketchCode-style GUI BLEU smoke/helper.

The helper mirrors the source-evidenced SketchCode Evaluator behavior that is
safe to bundle: whitespace normalization, comma spacing, button normalization,
prediction boundary-token trimming, single BLEU, and batch filename pairing.
It uses NLTK when available and falls back to exact normalized token matching
for smoke checks when NLTK is not installed.
"""

from __future__ import print_function

import argparse
import json
import sys
import warnings
from pathlib import Path

SMOKE_ORIGINAL = "container { row { button, btn-red } }"
SMOKE_PREDICTED = "<START> container { row { button, btn-green } } <END>"


def normalize_gui_text(gui_text):
    """Return SketchCode Evaluator.load_gui_doc-style tokens for GUI text."""
    gui = " ".join(gui_text.split())
    gui = gui.replace(",", " ,")
    tokens = gui.split()
    tokens = ["btn-orange" if token in ("btn-green", "btn-red") else token for token in tokens]
    tokens = ["btn-active" if token == "btn-inactive" else token for token in tokens]
    return tokens


def load_gui_doc(gui_path):
    return normalize_gui_text(Path(gui_path).read_text(encoding="utf-8"))


def trim_prediction(tokens):
    """Mirror Evaluator callers: generated_gui[1:-1]."""
    return list(tokens)[1:-1]


def try_import_bleu():
    try:
        from nltk.translate.bleu_score import corpus_bleu, sentence_bleu, SmoothingFunction
        return sentence_bleu, corpus_bleu, SmoothingFunction, None
    except Exception as exc:  # pragma: no cover - exact exception varies by env
        return None, None, None, exc


def nltk_kwargs(smoothing_cls, smooth):
    if not smooth or smoothing_cls is None:
        return {}
    return {"smoothing_function": smoothing_cls().method1}


def score_sentence(reference_tokens, hypothesis_tokens, smooth=False, require_nltk=False):
    sentence_bleu, _, smoothing_cls, import_error = try_import_bleu()
    if sentence_bleu is None:
        if require_nltk:
            raise RuntimeError("NLTK BLEU is required but unavailable: {}".format(import_error))
        return {
            "metric": "exact-match-fallback",
            "score": 1.0 if reference_tokens == hypothesis_tokens else 0.0,
            "warnings": ["NLTK unavailable; fallback is exact normalized-token match, not BLEU."],
        }

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        score = sentence_bleu([reference_tokens], hypothesis_tokens, **nltk_kwargs(smoothing_cls, smooth))
    return {
        "metric": "nltk-sentence-bleu" + ("-smoothed" if smooth else ""),
        "score": float(score),
        "warnings": [str(w.message) for w in caught],
    }


def score_corpus(actuals, predicted, smooth=False, require_nltk=False):
    _, corpus_bleu, smoothing_cls, import_error = try_import_bleu()
    if not actuals:
        return {
            "metric": "no-matched-pairs",
            "score": 0.0,
            "warnings": ["No matched original/predicted .gui pairs; fix filenames before interpreting BLEU."],
        }
    if corpus_bleu is None:
        if require_nltk:
            raise RuntimeError("NLTK BLEU is required but unavailable: {}".format(import_error))
        exact = sum(1 for refs, hyp in zip(actuals, predicted) if refs and refs[0] == hyp)
        return {
            "metric": "exact-match-fallback-average",
            "score": float(exact) / float(len(actuals)),
            "warnings": ["NLTK unavailable; fallback is average exact normalized-token match, not BLEU."],
        }

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        score = corpus_bleu(actuals, predicted, **nltk_kwargs(smoothing_cls, smooth))
    return {
        "metric": "nltk-corpus-bleu" + ("-smoothed" if smooth else ""),
        "score": float(score),
        "warnings": [str(w.message) for w in caught],
    }


def load_batch(original_dir, predicted_dir):
    original_dir = Path(original_dir)
    predicted_dir = Path(predicted_dir)
    predicted_files = sorted(
        [p for p in predicted_dir.iterdir() if p.is_file() and ".gui" in p.name],
        key=lambda p: p.name,
    )
    actuals = []
    predicted = []
    matched = []
    skipped = []

    for predicted_path in predicted_files:
        original_path = original_dir / predicted_path.name
        if not original_path.is_file():
            skipped.append(predicted_path.name)
            continue
        original_tokens = load_gui_doc(original_path)
        predicted_tokens = load_gui_doc(predicted_path)
        actuals.append([original_tokens])
        predicted.append(trim_prediction(predicted_tokens))
        matched.append(predicted_path.name)

    return actuals, predicted, matched, skipped, [p.name for p in predicted_files]


def infer_mode(args):
    if args.mode:
        return args.mode
    if args.original_gui_file or args.predicted_gui_file:
        return "single"
    if args.original_guis_dir or args.predicted_guis_dir:
        return "batch"
    return "smoke"


def require_pair(value_a, value_b, name_a, name_b):
    if not value_a or not value_b:
        raise SystemExit("Both {} and {} are required for this mode.".format(name_a, name_b))


def print_result(result, as_json=False):
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    print("metric: {}".format(result["metric"]))
    print("score: {}".format(result["score"]))
    for warning in result.get("warnings", []):
        print("warning: {}".format(warning), file=sys.stderr)


def add_tokens(result, reference_tokens=None, hypothesis_tokens=None):
    if reference_tokens is not None:
        result["reference_tokens"] = reference_tokens
    if hypothesis_tokens is not None:
        result["hypothesis_tokens"] = hypothesis_tokens
    return result


def run_smoke(args):
    reference_tokens = normalize_gui_text(SMOKE_ORIGINAL)
    predicted_tokens = normalize_gui_text(SMOKE_PREDICTED)
    hypothesis_tokens = trim_prediction(predicted_tokens)
    result = score_sentence(reference_tokens, hypothesis_tokens, args.smooth, args.require_nltk)
    result.update({
        "mode": "smoke",
        "raw_original": SMOKE_ORIGINAL,
        "raw_predicted": SMOKE_PREDICTED,
        "normalization_note": "btn-red and btn-green both normalize to btn-orange; predicted first/last tokens are trimmed.",
    })
    if args.show_tokens:
        add_tokens(result, reference_tokens, hypothesis_tokens)
        result["predicted_tokens_before_trim"] = predicted_tokens
    return result


def run_single(args):
    require_pair(args.original_gui_file, args.predicted_gui_file, "--original-gui-file", "--predicted-gui-file")
    reference_tokens = load_gui_doc(args.original_gui_file)
    predicted_tokens = load_gui_doc(args.predicted_gui_file)
    hypothesis_tokens = trim_prediction(predicted_tokens)
    result = score_sentence(reference_tokens, hypothesis_tokens, args.smooth, args.require_nltk)
    result.update({
        "mode": "single",
        "original_gui_file": str(args.original_gui_file),
        "predicted_gui_file": str(args.predicted_gui_file),
    })
    if args.show_tokens:
        add_tokens(result, reference_tokens, hypothesis_tokens)
        result["predicted_tokens_before_trim"] = predicted_tokens
    return result


def run_batch(args):
    require_pair(args.original_guis_dir, args.predicted_guis_dir, "--original-guis-dir", "--predicted-guis-dir")
    actuals, predicted, matched, skipped, considered = load_batch(args.original_guis_dir, args.predicted_guis_dir)
    result = score_corpus(actuals, predicted, args.smooth, args.require_nltk)
    result.update({
        "mode": "batch",
        "original_guis_dir": str(args.original_guis_dir),
        "predicted_guis_dir": str(args.predicted_guis_dir),
        "matched_count": len(matched),
        "considered_predicted_gui_names": considered,
        "matched_names": matched,
    })
    if args.show_skipped:
        result["skipped_predicted_without_original"] = skipped
    if args.show_tokens:
        result["reference_tokens_by_match"] = [refs[0] for refs in actuals]
        result["hypothesis_tokens_by_match"] = predicted
    return result


def build_parser():
    parser = argparse.ArgumentParser(
        description="SketchCode-style .gui BLEU smoke helper with NLTK BLEU or exact-match fallback."
    )
    parser.add_argument("--mode", choices=("smoke", "single", "batch"), help="Evaluation mode. Defaults to smoke unless file/folder args imply another mode.")
    parser.add_argument("--original-gui-file", type=Path, help="Original/reference .gui file for single-pair scoring.")
    parser.add_argument("--predicted-gui-file", type=Path, help="Predicted/generated .gui file for single-pair scoring.")
    parser.add_argument("--original-guis-dir", type=Path, help="Folder containing original/reference .gui files for batch scoring.")
    parser.add_argument("--predicted-guis-dir", type=Path, help="Folder containing predicted/generated .gui files for batch scoring.")
    parser.add_argument("--show-tokens", action="store_true", help="Include normalized reference/hypothesis token lists in output.")
    parser.add_argument("--show-skipped", action="store_true", help="In batch mode, include predicted .gui names skipped because originals were missing.")
    parser.add_argument("--smooth", action="store_true", help="Use NLTK SmoothingFunction.method1 for diagnostics. Original SketchCode scoring did not smooth.")
    parser.add_argument("--require-nltk", action="store_true", help="Fail instead of using exact-match fallback when NLTK is unavailable.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output.")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    mode = infer_mode(args)
    if mode == "smoke":
        result = run_smoke(args)
    elif mode == "single":
        result = run_single(args)
    elif mode == "batch":
        result = run_batch(args)
    else:  # pragma: no cover
        raise SystemExit("Unknown mode: {}".format(mode))
    print_result(result, as_json=args.json)


if __name__ == "__main__":
    main()

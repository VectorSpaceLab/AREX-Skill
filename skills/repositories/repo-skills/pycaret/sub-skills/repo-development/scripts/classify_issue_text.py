#!/usr/bin/env python3
"""Classify pasted PyCaret issue text against 4.0 maintainer signals.

This is a safe standalone helper for generated repo skills. It does not read
GitHub, does not mutate files, and should be treated as a first-pass triage
signal rather than a maintainer decision.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable


OUT_OF_SCOPE_PATTERNS = {
    "external experiment trackers": [r"\bmlflow\b", r"\bcomet\b", r"\bwandb\b", r"\bdagshub\b"],
    "distributed/parallel backends": [
        r"\bfugue\b",
        r"\bdask\b",
        r"\bdistributed\b",
        r"\bray[\s_/-]+tune\b",
        r"\bray\s*\[tune\]",
        r"\btune[_-]sklearn\b",
        r"\bparallel_backend\b",
    ],
    "legacy plotting/dashboard deps": [
        r"\byellowbrick\b",
        r"\bmljar\b",
        r"\bscikit[_-]plot\b",
        r"\bschemdraw\b",
        r"\bexplainerdashboard\b",
        r"\bdashboard\(\)",
        r"\.dashboard\b",
        r"\bgradio\b",
    ],
    "removed engine helper": [
        r"\bcreate_app\b",
        r"\bcreate_api\b",
        r"\bcreate_docker\b",
        r"\bcheck_fairness\b",
        r"\bcheck_drift\b",
        r"\beda\b",
        r"\bconvert_model\b",
        r"\bdeploy_model\b",
    ],
    "removed heavy analysis deps": [
        r"\bevidently\b",
        r"\bfairlearn\b",
        r"\bydata[_-]profiling\b",
        r"pandas[_-]profiling",
        r"\bm2cgen\b",
    ],
    "engine cloud deploy deps": [r"\bboto3\b", r"\baws[_\s-]*s3\b", r"deploy_model.*s3"],
    "sklearn acceleration add-ons": [r"scikit[_-]learn[_-]intelex", r"\bsklearnex\b", r"\bdaal4py\b"],
    "functional api/global state": [
        r"from\s+pycaret\.(classification|regression|clustering|anomaly)\s+import\s+\*",
        r"pycaret\.(classification|regression|clustering|anomaly)\.setup\s*\(",
        r"\bget_current_experiment\b",
        r"\bset_current_experiment\b",
        r"\b_CURRENT_EXPERIMENT\b",
    ],
}

FIXED_IN_4_HINTS = [
    r"scikit[-_ ]learn\s*(?:>=|=|version)?\s*1\.[5-9]",
    r"sklearn\s*1\.[5-9]",
    r"numpy\s*2",
    r"pandas\s*2\.[2-9]",
    r"python\s*3\.1[2-9]",
    r"distutils",
    r"np\.NaN",
    r"np\.product",
    r"_check_reg_targets",
    r"too many dependencies",
    r"takes forever to install",
    r"installation size",
]

KEPT_AREAS = [
    r"\bsetup\b",
    r"\bcompare_models\b",
    r"\bcreate_model\b",
    r"\btune_model\b",
    r"\bensemble_model\b",
    r"\bblend_models\b",
    r"\bstack_models\b",
    r"\bcalibrate_model\b",
    r"\bpredict_model\b",
    r"\bsave_model\b",
    r"\bload_model\b",
    r"\bfinalize_model\b",
    r"\bplot_model\b",
    r"\bevaluate_model\b",
    r"\binterpret_model\b",
    r"\bautoml\b",
    r"\bget_leaderboard\b",
    r"\bclassification\b",
    r"\bregression\b",
    r"\bclustering\b",
    r"\banomaly\b",
    r"\btime[_-]series\b",
]

STALE_CUTOFF = date(2023, 1, 1)


@dataclass(frozen=True)
class Hit:
    group: str
    pattern: str
    location: str


def _matches(patterns: Iterable[str], text: str) -> list[str]:
    return [p for p in patterns if re.search(p, text, flags=re.IGNORECASE)]


def _kill_hits(title: str, body: str) -> list[Hit]:
    hits: list[Hit] = []
    for group, patterns in OUT_OF_SCOPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, title, flags=re.IGNORECASE):
                hits.append(Hit(group, pattern, "title"))
            elif re.search(pattern, body, flags=re.IGNORECASE):
                hits.append(Hit(group, pattern, "body"))
    return hits


def _looks_like_env_dump(body: str) -> bool:
    return len(re.findall(r"^\s*[A-Za-z0-9_.-]+\s*==\s*[0-9]", body, re.MULTILINE)) >= 5


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None


def classify(title: str, body: str, updated: str | None = None, labels: str = "") -> tuple[str, list[str]]:
    title_l = title.lower()
    body_l = body.lower()
    text = f"{title_l}\n{body_l}"
    kill_hits = _kill_hits(title_l, body_l)
    title_kill = [h for h in kill_hits if h.location == "title"]
    body_kill = [h for h in kill_hits if h.location == "body"]
    fixed = _matches(FIXED_IN_4_HINTS, text)
    kept = _matches(KEPT_AREAS, text)
    updated_date = _parse_date(updated)
    label_set = {x.strip().lower() for x in labels.split(",") if x.strip()}

    reasons: list[str] = []
    if title_kill:
        groups = sorted({h.group for h in title_kill})
        reasons.append("title mentions killed/removed area(s): " + ", ".join(groups))
        reasons.extend(f"  pattern: {h.pattern}" for h in title_kill[:5])
        return "out_of_scope_or_requires_maintainer_override", reasons

    if body_kill and not _looks_like_env_dump(body_l):
        groups = sorted({h.group for h in body_kill})
        reasons.append("body mentions killed/removed area(s): " + ", ".join(groups))
        reasons.extend(f"  pattern: {h.pattern}" for h in body_kill[:5])
        return "out_of_scope_or_requires_maintainer_override", reasons

    if fixed:
        reasons.append("matches compatibility/dependency problems addressed by PyCaret 4 modernization")
        reasons.extend(f"  pattern: {p}" for p in fixed[:5])
        return "possibly_fixed_in_4_0", reasons

    if updated_date and updated_date < STALE_CUTOFF:
        reasons.append(f"last updated {updated_date.isoformat()}, before {STALE_CUTOFF.isoformat()}")
        return "stale_needs_reproduction_on_4_0", reasons

    if kept:
        reasons.append("mentions maintained PyCaret 4 area(s); triage as bug/enhancement")
        reasons.extend(f"  pattern: {p}" for p in kept[:5])
        if "bug" in label_set:
            return "still_relevant_bug_candidate", reasons
        return "still_relevant_candidate", reasons

    reasons.append("no strong kill-list, fixed-in-4, stale, or kept-area signal found")
    if "bug" in label_set:
        return "needs_manual_bug_triage", reasons
    return "needs_manual_triage", reasons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", default="", help="Issue title text.")
    parser.add_argument("--body", default="", help="Issue body/comment text. If omitted, stdin is read when piped.")
    parser.add_argument("--updated", default=None, help="Last updated date, e.g. 2022-11-05 or ISO timestamp.")
    parser.add_argument("--labels", default="", help="Comma-separated labels, e.g. bug,Approved.")
    args = parser.parse_args()

    body = args.body
    if not body:
        try:
            import sys

            if not sys.stdin.isatty():
                body = sys.stdin.read()
        except Exception:
            body = ""

    bucket, reasons = classify(args.title, body, args.updated, args.labels)
    print(f"bucket: {bucket}")
    print("reasons:")
    for reason in reasons:
        print(f"- {reason}")
    print("recommendation:")
    if bucket == "out_of_scope_or_requires_maintainer_override":
        print("- Check the kill list and ADRs. Do not implement unless the maintainer explicitly changes scope.")
    elif bucket == "possibly_fixed_in_4_0":
        print("- Ask for reproduction on the current PyCaret 4 release or close with release-note pointer if confirmed fixed.")
    elif bucket == "stale_needs_reproduction_on_4_0":
        print("- Ask whether the issue still reproduces on PyCaret 4; close after no response per maintainer policy.")
    else:
        print("- Read the full issue and comments, reproduce if it is a bug, then choose the relevant test matrix.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

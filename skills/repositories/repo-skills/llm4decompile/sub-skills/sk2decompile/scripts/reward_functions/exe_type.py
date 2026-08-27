"""
Reference reward function: Compilability + Placeholder Identifier Matching.

Structure-recovery reward example used by SK²Decompile.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile


def compute_score(solution_str, ground_truth, extra_info=None):
    type_score_value, _ = type_score(solution_str, ground_truth, extra_info)
    compileable_score_value = compileable_score(solution_str, ground_truth, extra_info)
    if compileable_score_value == 0.0:
        return 0.0
    return type_score_value + compileable_score_value


def type_score(solution_str, ground_truth, extra_info=None):
    patterns = [r"\bfunc\w*\b", r"\btype\w*\b", r"\bvar\w*\b", r"\bfield\w*\b"]

    def extract_terms(text):
        terms = set()
        for pattern in patterns:
            terms.update(re.findall(pattern, text))
        return terms

    solution_terms = extract_terms(solution_str)
    ground_truth_terms = extract_terms(ground_truth)
    intersection = solution_terms.intersection(ground_truth_terms)
    union = solution_terms.union(ground_truth_terms)
    jaccard_similarity = len(intersection) / len(union) if union else 0.0
    return jaccard_similarity, len(solution_terms) + len(ground_truth_terms)


def compileable_score(solution_str, ground_truth, extra_info=None):
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            source_file = os.path.join(tmpdir, "temp.c")
            object_file = os.path.join(tmpdir, "temp.o")
            header = extra_info.get("header", "") if extra_info else ""
            with open(source_file, "w", encoding="utf-8") as f:
                f.write(f"{header}\n\n{solution_str}")
            proc = subprocess.run(["gcc", "-c", source_file, "-o", object_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5, check=True)
            return 1.0 if proc.returncode == 0 else 0.0
        except Exception:
            return 0.0

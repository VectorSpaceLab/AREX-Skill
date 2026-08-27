"""
Reference reward function: Compilability + Word-level Jaccard Similarity.
"""

from __future__ import annotations

import os
import subprocess
import tempfile


def compute_score(solution_str, ground_truth, extra_info=None):
    sim_score = jaccard_similarity(solution_str, ground_truth)
    compile_score = compileable_score(solution_str, ground_truth, extra_info)
    if sim_score > 0.5:
        return sim_score + compile_score
    return 0


def jaccard_similarity(str1, str2):
    set1 = set(str1.lower().split())
    set2 = set(str2.lower().split())
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    if union == 0:
        return 0.0
    return intersection / union


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

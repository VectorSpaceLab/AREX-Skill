#!/usr/bin/env python3
"""Run an offline Memori search smoke using pre-scored candidates."""

from __future__ import annotations

import json

from memori.search import search_facts
from memori.search._types import FactCandidate


def main() -> None:
    candidates = [
        FactCandidate(
            id=1,
            content="The customer prefers blue packaging.",
            score=0.9,
            date_created="2026-01-01",
        ),
        FactCandidate(
            id=2,
            content="The deployment uses PostgreSQL.",
            score=0.2,
            date_created="2026-01-02",
        ),
    ]
    results = search_facts(query_text="favorite color blue", candidates=candidates, limit=1)
    top = results[0]
    print(
        json.dumps(
            {
                "status": "passed",
                "top_id": top.id,
                "top_content": top.content,
                "rank_score": top.rank_score,
            },
            indent=2,
            sort_keys=True,
            default=str,
        )
    )


if __name__ == "__main__":
    main()

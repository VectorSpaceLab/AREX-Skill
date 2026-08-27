#!/usr/bin/env python3
"""Safe Memori install/import/config smoke."""

from __future__ import annotations

import inspect
import json
from importlib import metadata


def main() -> None:
    import memori
    from memori import Config, Memori
    from memori.native import RustCoreAdapter
    from memori.search import search_facts

    cfg = Config()
    payload = {
        "package": "memori",
        "version": metadata.version("memori"),
        "requires_python": metadata.metadata("memori").get("Requires-Python"),
        "imports": [
            "memori",
            "memori.search",
            "memori.storage",
            "memori.llm",
            "memori.embeddings",
            "memori.native",
        ],
        "module": memori.__name__,
        "signatures": {
            "Memori": str(inspect.signature(Memori)),
            "Memori.provision": str(inspect.signature(Memori.provision)),
            "search_facts": str(inspect.signature(search_facts)),
        },
        "config_defaults": {
            "embeddings_model": cfg.embeddings.model,
            "recall_embeddings_limit": cfg.recall_embeddings_limit,
            "recall_facts_limit": cfg.recall_facts_limit,
            "recall_relevance_threshold": cfg.recall_relevance_threshold,
            "request_secs_timeout": cfg.request_secs_timeout,
            "request_num_backoff": cfg.request_num_backoff,
            "use_rust_core": cfg.use_rust_core,
            "version": cfg.version,
        },
        "native": {
            "RustCoreAdapter": RustCoreAdapter.__name__,
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()

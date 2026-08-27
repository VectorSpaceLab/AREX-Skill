# Native Verification Summary

This reference summarizes source-derived verification ideas without requiring future agents to open or run the original repository checkout. Use it to understand why the sub-skills cover the main behavior families.

## Safe Native Candidate Families

- Local mode behavior: dense/sparse queries, payload filters, fusion score thresholds, persistence, and exclusive path locks.
- Async local behavior: awaited collection creation, upsert, count, query, payload updates, aliases, and close lifecycle.
- Conversion behavior: REST-to-gRPC and gRPC-to-REST conversions for filters, query requests, sparse vectors, datetime values, payload schemas, and nested prefetches.
- Constructor validation: mutually exclusive `location`/`url`/`host`/`path`, prefix rules, URL parsing, and `check_compatibility=False` offline config checks.

## Service-Dependent Candidate Families

- Remote sync/async congruence across REST and gRPC.
- Upload helpers against a running Qdrant server, including `prefer_grpc=True` and rate-limit handling.
- Migration between local and remote clients or server-to-server clients.
- Snapshots, shard keys, cluster status, and distributed operations.

## Optional Or Expensive Candidate Families

- FastEmbed local inference and hybrid search can require optional packages and model downloads.
- Cloud inference requires a Qdrant Cloud cluster, API key, plan support, and model availability.
- Benchmark upload tests are not suitable as default verification because they are service-dependent and performance-oriented.

## How This Affects Runtime Use

- Prefer bundled smoke scripts for quick, deterministic checks.
- Run real server, Cloud, model-download, or benchmark checks only when the user explicitly provides the required environment and approves the cost.
- Treat skipped native families as coverage anchors for synthetic usability cases rather than runtime dependencies.

# Editing Troubleshooting

- Redaction not permanent: ensure `apply_redactions()`, full save, garbage collection, reopen, and search verification.
- Object orphaned: reacquire pages/annotations/widgets after edits.
- Widgets/links missing after merge: set `links`, `annots`, `widgets`, and `join_duplicates` intentionally.
- Embedded file extraction unsafe: sanitize stored filenames and use explicit extract dirs.
- Save conflict: cleanup/linearization/encryption changes are full-save workflows, not incremental-save workflows.

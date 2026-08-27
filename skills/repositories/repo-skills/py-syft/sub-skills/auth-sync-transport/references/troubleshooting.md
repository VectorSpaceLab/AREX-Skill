# Auth/sync troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Token/email mismatch | Token belongs to another Google account. | Validate expected email; regenerate token with the correct account. |
| Unsupported environment | Local script lacks `token_path` or explicit email. | Pass both; do not rely on Colab-only browser auth. |
| Peer not visible | Missing sync, stale cache, wrong account, or request still pending. | `load_peers(force_download=True)`, inspect state on both sides, then sync. |
| Dataset/job folders not created after approval | RDS callbacks have not run after peer loading. | Use RDS client and run `load_peers()` / `sync()` after approval. |
| Version mismatch | Peer package versions differ. | Align versions; use ignore/skip flags only with informed acceptance. |
| Cleanup requested | Could delete local or remote SyftBox state. | Ask for exact scope and backup before running cleanup. |

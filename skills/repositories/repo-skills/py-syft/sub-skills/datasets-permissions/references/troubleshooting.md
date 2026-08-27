# Dataset and permission troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Dataset not found | Peer not approved/synced, wrong datasite, or not shared. | Verify peer state, sync both sides, use explicit `datasite=`. |
| Resolver lacks context | Local call omitted `client`, `SYFTBOX_FOLDER`, or owner email. | Pass `client=client` for mock testing; remove it in submitted jobs. |
| Ambiguous owner | Several datasites have the same dataset name. | Pass `owner_email` or `datasite`. |
| Private data visible concern | User is inspecting mock files or owner-only private metadata. | Explain mock/private split; do not share private path. |
| Parent permissions ignored | Nearest `syft.pub.yaml` overrides parent. | Put fallback rules in the nearest file or remove unintended override. |

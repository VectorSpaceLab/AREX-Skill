# Dataset data formats

PySyft distinguishes public/mock and private collections:

- Mock files are shared with permitted data scientists for exploration.
- Private files stay owner-side and are used by owner-side jobs.
- Dataset metadata names the collection and records tags, summary, location, and readme when supplied.
- `private_metadata.yaml` records private metadata used when owner-side folders are restored.
- `syft://` paths can be resolved when `SYFTBOX_FOLDER` or an explicit SyftBox folder is known.

Do not copy private files into mock data to make local testing easier. Create tiny public mock fixtures instead.

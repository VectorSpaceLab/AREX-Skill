# Optional dataset integrations

- **MOABB**: install the `moabb` extra when using `MOABBDataset` or MOABB
  paradigms. Dataset fetches can be network- and cache-dependent; pin the
  dataset name/subject list and do not treat a successful import as a fetched
  dataset.
- **BIDS/OpenNeuro**: BIDS validation and OpenNeuro acquisition need their
  optional packages, a valid BIDS layout, network, and sufficient storage.
  Validate local layout before downloading anything.
- **TUH and Sleep Physionet**: corpus fetchers may be large, licensed, or slow.
  Confirm access and disk/cache locations, and start with a documented mock or
  one-recording fixture.
- **Hugging Face Hub**: Hub upload/download paths need the Hub extra and often a
  token. Never upload private EEG data by default; verify repository identity,
  visibility, file size, and cache location first.

If an optional package is absent, preserve the local `RawArray`/array workflow
and report which extra is missing. Do not silently substitute a different
recording or dataset name.

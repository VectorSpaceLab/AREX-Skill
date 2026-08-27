# Source Script Selection

The source repository has many useful diagnostics, but a public operating skill
must not depend on the source checkout. Apply these decisions:

- **Adapt** small deterministic registration, schema, or fixture checks into the
  bundled `scripts/` directory.
- **Reference-only** parity, rendering, policy rollout, external integration,
  and conversion recipes when they require source-local assets, optional native
  packages, a display/GPU, large data, or long runtime. Preserve prerequisites,
  command shape, and expected metrics in a reference; do not link to the source
  script.
- **Exclude** real-robot deployment, teleoperation device control, credentialed
  services, release/upload/download helpers, destructive asset conversion, and
  benchmark-scale sweeps.

For every adapted helper, accept an explicit repo root or package/task argument,
use safe bounded defaults, return non-zero on a genuine failed check, and report
missing optional dependencies clearly. Run `--help` and a no-side-effect import
check before using it in a usability case.

The skill's runtime script is a replacement, not a claim that the source repo
contains the replacement filename. Keep source-vs-bundled names distinct in
review notes.

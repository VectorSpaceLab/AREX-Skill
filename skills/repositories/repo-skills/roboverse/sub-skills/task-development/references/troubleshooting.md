# Task Development Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| Task id is unknown after install | Module was not discovered/imported, registry name differs, or entry-point/package root is missing | Import `roboverse_pack`, invoke the documented MetaSim package/Gym registration path, then list/resolve the canonical id. Verify `metasim.toml`/entry-point installation. |
| Constructor fails before subclass fields exist | A base environment probes observations or specs during initialization | Initialize required buffers/config fields before `super().__init__` when the base contract requires it, or make the probe independent of runtime buffers; add a constructor regression test. |
| Observation/reward has wrong shape | Scalar vs per-environment tensor, broadcasting, or missing batch dimension | Assert `(num_envs, ...)` shapes after reset/step; use explicit reductions and keep device/dtype. |
| Reward differs across implementations | Joint/body order, units, quaternion convention, clipping, timestep, or termination timing differs | Log terms independently, align state and ordering, and report max/mean deltas per backend. Do not tune until the discrepancy is localized. |
| Site/contact/sensor value is absent | State schema does not expose it or the backend lacks the query | Declare the extra/query explicitly and test supported handlers; fail clearly on unsupported backends. |
| Reset is nondeterministic | Global RNG, unseeded randomizer, stale buffer, or backend reset ordering | Use the environment seed path, reset every buffer, compare two same-seed resets, and add a seed-contract test. |
| Invalid robot/task silently no-ops | Boundary validation is missing | Raise a clear `ValueError`/`KeyError` listing supported values; never downgrade an unsupported path to a quiet no-op. |
| Simulator test fails during setup | Backend package, GPU, driver, assets, or display missing | Separate environment setup from task assertions. Mark the real backend blocker; run only general tests until the correct environment exists. |

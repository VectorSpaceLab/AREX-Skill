# Source artifact map

This runtime skill is self-contained. Original repository docs, examples, tests, and scripts were used as evidence, but future agents should use the bundled files listed here rather than relying on the original checkout.

| Source evidence category | Runtime replacement in this skill | Decision and rationale |
|---|---|---|
| README overview, installation section, FAQ, and 8-schools example | Root `SKILL.md`, `references/getting-started.md`, `sub-skills/mcmc-diagnostics/scripts/eight_schools_smoke.py`, MCMC references | Distilled install/backend/modeling guidance and adapted a tiny no-network MCMC smoke. |
| `docs/source/primitives.rst`, `handlers.rst`, `utilities.rst` | `sub-skills/modeling-primitives/references/*.md`, `scripts/model_trace_smoke.py` | Distilled primitive/handler/inspection workflow; adapted trace/condition/seed behavior into a bundled script. |
| `docs/source/distributions.rst` and distribution/transform tests | `sub-skills/distributions-transforms/references/*.md`, `scripts/distribution_transform_smoke.py` | Distilled constructor/shape/support/transform rules; adapted finite log-prob and transform round-trip checks. |
| `docs/source/mcmc.rst`, diagnostics docs, README MCMC narrative, MCMC tests/examples | `sub-skills/mcmc-diagnostics/references/*.md`, `scripts/eight_schools_smoke.py` | Distilled kernel choice, diagnostics, backend/chain configuration, and predictive/log-likelihood guidance. |
| `docs/source/svi.rst`, `autoguide.rst`, `funsor.rst`, optimizer docs, `examples/minipyro.py` | `sub-skills/svi-autoguides/references/*.md`, `scripts/svi_smoke.py` | Distilled SVI/ELBO/autoguide guidance and adapted a synthetic SVI smoke without version assertions or plotting. |
| `docs/source/contrib.rst`, `numpyro/contrib/*`, optional contrib examples/tests | `sub-skills/advanced-contrib/references/*.md`, `scripts/check_optional_dependencies.py` | Distilled optional workflow matrix and dependency checks; no optional examples bundled because they need extra packages, plotting, network data, or longer runs. |
| `examples/hmcecs.py` | `sub-skills/mcmc-diagnostics/references/mcmc-workflows.md` and troubleshooting | Reference-only: useful algorithm pattern, but the original script imports plotting and writes a PDF. |
| `examples/toy_mixture_model_discrete_enumeration.py` | `sub-skills/svi-autoguides/references/elbo-and-enumeration.md`, `sub-skills/advanced-contrib/references/advanced-contrib.md` | Reference-only: requires optional Funsor/Optax/plotting stack, but the enumeration pattern is preserved. |
| `examples/hsgp.py`, nested sampling and neural examples | `sub-skills/advanced-contrib/references/*.md` | Reference-only: optional dependencies and long-running/plotting/data side effects. |
| Maintainer scripts `scripts/update_headers.py`, `scripts/update_version.py` | No runtime replacement | Excluded: maintainer-only scripts mutate repository files and are not operating package workflows. |
| Benchmarks | No executable replacement; performance caveats in troubleshooting where relevant | Excluded/reference-only: benchmark-scale and not a routine user workflow. |

When a task needs a runnable check, prefer the bundled scripts under this skill tree. When a task needs a full-scale example, use the references to reconstruct a safe workflow in the user's own project rather than running original repository examples by default.

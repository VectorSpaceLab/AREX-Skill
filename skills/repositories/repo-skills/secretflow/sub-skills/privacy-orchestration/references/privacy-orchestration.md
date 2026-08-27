# Privacy and orchestration reference

This reference covers SecretFlow's privacy-oriented protocols and its runtime
orchestration modes.

## Deployment modes

| Mode | Best for | Run shape | Notes |
| --- | --- | --- | --- |
| Debug | Contributor debugging and local iteration | Run locally without a Ray cluster | Easiest way to inspect logs and breakpoints |
| Simulation | Single-organization experiments or demos | A Ray cluster with simulated parties | Good for quick validation of code flow |
| Production | Formal multi-institution execution | Each institution runs its own Ray cluster | The code path resembles simulation, but each side executes separately |
| Kuscia production | Orchestrated production with scheduling and network abstraction | Execute SecretFlow through Kuscia APIs | Best when task scheduling and port reuse matter |

## PSI protocol map

| Protocol family | When to choose it | Notes |
| --- | --- | --- |
| ECDH PSI | Small or straightforward set-intersection tasks | Good baseline protocol, easier to explain |
| KKRT PSI | Large-set PSI | Often the best choice when scale matters |
| BC22 / PCG PSI | Communication-efficient large-set PSI | Another large-set option with different efficiency tradeoffs |
| Unbalanced PSI | When one side is much larger or the offline/online split matters | Good for asymmetric workloads |
| DP PSI | When output privacy matters as well as input privacy | Built on top of the PSI family |

## Secure aggregation and comparison

| API / class | Purpose | Common use |
| --- | --- | --- |
| `PlainComparator` | Compare on a plain device or SPU in simple scenarios | Fastest sanity checks |
| `SPUComparator` | Compare using SPU-backed secure computation | Privacy-preserving comparisons |
| `PlainAggregator` | Aggregate on a plain device | Useful for local or simulation checks |
| `SecureAggregator` | Aggregate across participants with extra protection | Common for federated training workflows |
| `SPUAggregator` | Aggregate on SPU | Useful when the aggregate itself should remain protected |

## Kuscia helpers

| Helper | Purpose | Input shape |
| --- | --- | --- |
| `KusciaTaskConfig.from_json(...)` | Parse a Kuscia task request | A dictionary with task id, cluster definition, ports, and node eval data |
| `get_sf_cluster_config(...)` | Derive a SecretFlow cluster config from Kuscia config | A parsed `KusciaTaskConfig` |
| `convert_domain_data_to_individual_table(...)` | Convert domain data to a SecretFlow individual table | A Kuscia domain data protobuf plus optional table attrs |

The Kuscia path is most useful when the task already provides a structured
request and the caller wants SecretFlow to derive the runtime wiring from it.

## TEEU guidance

- Use simulation mode when you need a quick local proof of the TEEU code path.
- The workflow is still multi-party: each participant has to be represented in
  the cluster and the TEEU provider must be wired in explicitly.
- The simulation docs require a substantial amount of memory. Treat that as a
  deployment prerequisite rather than a model hyperparameter.
- `auth_manager_config` is part of the runtime contract when you move beyond a
  toy simulation.

## Workflow choice guide

- Choose debug when you are only learning the API or debugging a local branch.
- Choose simulation when you need a runnable demo without an actual production
  deployment.
- Choose production when each institution already has its own runtime.
- Choose Kuscia when orchestration, concurrency, or port reuse is the main
  reason for the deployment.

## Troubleshooting

### PSI input mismatch or co-location errors
- Check the party/device mapping before trying a different protocol.
- Confirm that the PSI inputs are co-located as the chosen protocol expects.

### Kuscia config parsing failures
- Parse the JSON request first and inspect the task id, cluster definition, and
  allocated ports.
- If the helper cannot derive the cluster config, the request shape is usually
  the problem rather than the PSI algorithm.

### TEEU simulation fails early
- Re-check the memory requirement.
- Confirm that the auth manager, party key pair, and ray cluster assumptions are
  all present.
- Treat TEEU as an advanced deployment path; keep it out of the minimum scope
  unless the user specifically asks for it.

### Production or simulation cluster does not connect
- The party addresses and ports must be reachable from each runtime node.
- In distributed settings, a wrong address is usually easier to fix than the
  protocol choice.

## Cross-links

- Root troubleshooting: `../../references/troubleshooting.md`
- Smoke helper: `../scripts/kuscia_config_smoke.py`

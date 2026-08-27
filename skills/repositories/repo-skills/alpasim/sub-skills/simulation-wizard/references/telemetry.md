# Prometheus telemetry

AlpaSim starts Prometheus support by default. The wizard allocates ports for
runtime workers, Prometheus, node exporter, process exporter, and DCGM exporter;
writes file-SD targets and scrape config under the run directory; and the
runtime later uses Prometheus data to produce `metrics_plot.png`.

Relevant overrides:

```bash
wizard.prometheus.start_prometheus=true
wizard.prometheus.scrape_interval=5s
wizard.prometheus.file_sd_dir=/shared/prometheus/alpasim
```

A normal run contains:

```text
prometheus/data/
prometheus/prometheus.yml
prometheus/targets/alpasim.json
prometheus/rules/alpasim-recording-rules.yml
prometheus/process-exporter.yml
prometheus/dcgm-counters.csv
metrics_plot.png
```

Local targets use service/container names in ordinary Compose and localhost
when host networking or Slurm is used. The central file-SD publication uses a
hostname/IP reachable by the external Prometheus. Each target is labeled with
run UUID/name, user, node, Slurm job, and component. Managed cleanup removes the
run's central JSON on normal exit; stale cleanup is conservative (at least five
hours old and all targets unreachable).

A central Prometheus can discover active runs with:

```yaml
scrape_configs:
  - job_name: alpasim
    file_sd_configs:
      - files: [/shared/prometheus/alpasim/*.json]
        refresh_interval: 10s
```

The repository's Prometheus/Grafana launcher uses Docker and may mount SSHFS;
it is reference-only, not a bundled autonomous script. For a local/mounted
file-SD path, run it manually only after reviewing mounts, network exposure,
and credentials. In Slurm/Enroot, the process exporter also publishes GPU
ownership labels useful for joining DCGM data.

Interpret the auto plot as diagnostics: high queue depth/RPC duration suggests
service saturation; low GPU use may be underload; >90% GPU use may be
saturation/throttling; high runtime idle time suggests waiting. These signals do
not replace rollout metrics or service logs.

# Scene caches and run results

## Scene access

Public catalogs are CSV metadata, not bundled artifacts. Hugging Face access to
`nvidia/PhysicalAI-Autonomous-Vehicles-NuRec` is gated: request dataset access,
create a read token, export `HF_TOKEN`, and choose a cache via `HF_HOME` if
needed. The wizard downloads selected USDZs into `scenes.scene_cache`, keeps
UUID-named files in `all-usdzs`, and creates deterministic symlinked scenesets
under `scenesets/`. A cached artifact avoids a new download; an absent artifact
causes a network/authentication operation even when `wizard.dry_run=true`.

The 26.01 and 26.04 public artifacts may have been replaced in place. If a
cached release is stale, remove or move only the configured scene cache after
confirming no other run needs it; never delete a shared cache casually. The
video-model path additionally requires ClipGT map parquet, front-wide JPEG seed,
and matching recorded calibration.

A local USDZ directory is the safest offline/testing path:

```bash
uv run alpasim_check_config deploy=local topology=1gpu driver=vavam \
  scenes.local_usdz_dir=./local-usdz wizard.log_dir=./runs/local-check
```

Each local USDZ must be a readable ZIP with `metadata.yaml` containing `uuid`
and usually `scene_id`; invalid archives are skipped and an empty valid set is
an error. The generated local catalog is in memory; writable scratch state uses
`scenes.scene_cache`.

## Output contract

A typical `wizard.log_dir` contains:

```text
run_metadata.yaml
wizard-config.yaml
wizard-config-loadable.yaml
generated-user-config-0.yaml
generated-network-config.yaml
generated-runtime-server.yaml  # SERVER only
driver-config.yaml
controller-config.yaml
trafficsim-config.yaml
eval-config.yaml
docker-compose.yaml
run.sh                         # deployment-dependent
rollouts/<scene-id>/<batch-id>/
  rollout.asl  rollout.rclog  metrics.parquet  _complete
  rollout_indexed/ ...
eval/ aggregate/ prometheus/ txt-logs/ controller/ driver/
```

`rollouts` hold per-run logs and marker files; `_complete` means a rollout
finished successfully. `eval` holds per-rollout metrics and videos. `aggregate`
holds combined parquet data, `metrics_results.txt`, `metrics_results.png`, and
violation-organized videos. `prometheus` holds local TSDB/config/targets/rules;
`txt-logs` contains wizard and service output. Focus on `rollouts` and
`aggregate` for results, `wizard-config.yaml` and `txt-logs` for setup errors.

The exact ASL format and metric interpretation belong to `evaluation-and-logs`.
Do not infer a successful simulation from the existence of a generated config;
inspect runtime exit status, `_complete`, and aggregate products.

## Resume and array behavior

A failed rollout can leave a directory without `_complete`; inspect the first
service error before retrying. On Slurm arrays, scene lists are sorted and
round-robin split across tasks. Use only the site's approved resume/requeue
workflow, preserve the original `wizard-config-loadable.yaml`, and enable
`runtime.enable_autoresume=true` only when the resume semantics are understood.
Do not hand-edit generated network addresses to repair a service failure.

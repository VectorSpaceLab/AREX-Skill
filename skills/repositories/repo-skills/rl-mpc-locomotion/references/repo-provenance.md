# Repository Provenance

Read this before deciding whether this skill is current for a checkout. If the
source commit, package version, submodule revisions, or public evidence paths
differ, run the repository-skill refresh workflow.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-22T00:00:00Z",
  "repository": {
    "name": "rl-mpc-locomotion",
    "remote_url": "https://github.com/silvery107/rl-mpc-locomotion",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "df944efacdd403c05600907a386d6fe400f6d067",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "rl_mpc_locomotion",
      "version": "1.0.0",
      "import_names": ["MPC_Controller", "RL_Environment", "mpc_osqp"]
    },
    {
      "name": "rsl-rl",
      "version": "1.0.2",
      "import_names": ["rsl_rl"]
    }
  ],
  "submodules": {
    "extern/rsl_rl": "2ad79cf0caa85b91721abfe358105f869a784121",
    "extern/pybind11": "ffa346860b306c9bbfb341aed9c14c067751feb8",
    "extern/eigen3": "02f420012a169ed9267a8a78083aaa588e713353",
    "extern/qpoases": "268b2f2659604df27c82aa6e32aeddb8c1d5cc7f"
  },
  "evidence": {
    "source_roots": ["MPC_Controller", "RL_Environment"],
    "docs": ["README.md", "docs/3-isaac_api_note.md", "docs/5-upgrade_isaac_gym.md", "docs/6-qp_solver.md", "docs/7-isaac_gym_env.md", "docs/9-useful_cmd.md"],
    "examples": ["RL_MPC_Locomotion.py", "test"],
    "tests": ["test"],
    "configs": ["environment.yml", "RL_Environment/cfg"],
    "assets": ["assets/a1_description", "assets/aliengo_description", "assets/go1_description", "assets/mini_cheetah"]
  }
}
```

## Refresh Check

- If the source `git rev-parse HEAD` differs from the recorded commit, treat
  this skill as potentially stale.
- If any declared submodule commit changes, refresh the native build and
  dependency references before using the compiled-extension guidance.
- If `setup.py`, `environment.yml`, public entry points, task configuration,
  robot URDFs, or controller/policy interfaces change, refresh the affected
  sub-skill.
- The source snapshot was clean before generated review files were created;
  generated skill and review artifacts are not source evidence.

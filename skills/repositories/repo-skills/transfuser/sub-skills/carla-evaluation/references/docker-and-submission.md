# Docker Packaging And Submission Boundary

## Purpose

Use this reference to review the TransFuser submission tree before an external
Docker build or Alpha upload. The bundled checker performs read-only local
preflight. It never invokes Docker, Alpha, a registry, CARLA, or the network.

## Source Packaging Model

The repository image builder stages a temporary context with:

```text
.tmp/
  PythonAPI/
  scenario_runner/
  leaderboard/
  team_code/
```

It copies CARLA's PythonAPI, renames matching Python 2 and Python 3 CARLA eggs
to stable leaderboard names, copies ScenarioRunner, leaderboard, and the
TransFuser team-code tree, then builds the master Dockerfile. The original
builder deletes `.tmp` afterward. Because those operations copy large trees,
rename files, invoke Docker, and delete staging state, they remain external and
are not reproduced by this skill.

The bundled preflight checks the inputs before that side-effecting process:

```bash
python scripts/check_submission_layout.py \
  --carla-root /path/to/CARLA_0.9.10.1 \
  --scenario-runner-root /path/to/scenario_runner \
  --leaderboard-root /path/to/leaderboard \
  --team-code-root /path/to/team_code_transfuser \
  --config-dir /path/to/team_code_transfuser/model_ckpt/transfuser
```

Use `--format json` for automation and `--require-local-server` only when the
same CARLA root must also host a local server. Exit status `0` means the checked
layout passed; it is not proof that an image builds or an agent runs.

## Required Layout

The checker expects:

- CARLA PythonAPI with a `carla` package and both Python 2 and Python 3 egg
  artifacts, because the repository staging script renames both classes.
- ScenarioRunner with its `srunner` package.
- Leaderboard with evaluator code, the master Dockerfile, and the container
  evaluation entrypoint.
- Team code with `submission_agent.py`, its model/config/data and fusion
  modules, `requirements.txt`, and a configuration directory inside the
  team-code tree.
- `args.txt` as a valid JSON object and at least one nonempty `.pth` file. More
  than one `.pth` file represents an ensemble; the submission agent loads all
  of them.

Keeping the config directory under team code matters because the source build
copies that one tree into `/workspace/team_code`. A checkpoint path elsewhere
on the host will not appear in the image unless the external packaging recipe
is intentionally changed.

## Legacy Image Constraints

The master image recipe is historically pinned around Ubuntu 16.04, CUDA 10.2,
cuDNN 7, Python 3.5 plus a Python 3.7 Conda environment, and older CUDA wheels.
The public training setup uses newer Torch/CUDA-era dependencies. Treat an
image build as a separate compatibility exercise; do not assume that a model
working in the training environment will load in the submission image.

Before building externally, verify:

1. The model's `args.txt` matches the copied code and checkpoint state dicts.
2. Required binary wheels exist for the image's Python/CUDA combination.
3. The selected track matches the agent sensor suite.
4. The CARLA egg architecture and Python version match the evaluator process.
5. The Docker build context contains no unrelated data or secrets.

## Container Runtime Boundary

A local container evaluation additionally requires a separately running CARLA
server, host networking or an equivalent explicit network plan, GPU access,
and a writable results mount. Those are privileged runtime choices. This skill
does not construct or execute the container command.

Do not use a container's successful import as evidence that the CARLA server,
sensor configuration, route execution, or checkpoint writing works. Validate
the resulting JSON with [result-schema.md](result-schema.md).

## Alpha Credential And Upload Boundary

Alpha authentication and benchmark submission are credentialed cloud actions.
They are never part of automated preflight.

- A human or authorized external process must create the account/team, install
  the CLI, authenticate, choose the benchmark split, and approve upload.
- Repository guidance maps split 2 to `MAP` and split 3 to `SENSORS`; confirm
  the current service contract before upload because cloud interfaces can
  change independently of this repository snapshot.
- Never place Alpha credentials, registry tokens, SSH keys, cloud profiles, or
  shell history in team code, model directories, Dockerfiles, staged contexts,
  result JSON, or diagnostic output.
- Treat image submission as a data egress operation: it uploads code, model
  weights, and image layers.

The layout checker warns about common secret-like filenames and symlinks that
escape the team-code root. Review warnings manually; filename checks cannot
prove that a context contains no secrets.

Use [troubleshooting.md](troubleshooting.md) for layout and compatibility
failures.

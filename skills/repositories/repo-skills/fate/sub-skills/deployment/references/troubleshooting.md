# Troubleshooting

Use this page when deployment checks fail and you need the next safe command.
It keeps the advice concrete: symptom, likely cause, next command, and when to stop.

## Quick symptom table

| Symptom | Likely cause | Next command | Stop condition |
| --- | --- | --- | --- |
| `fate_flow --help` or `pipeline --help` is missing, or `import fate` reports the wrong version | Wrong environment or mixed package set | `python -m pip show pyfate fate_client fate_flow fate_utils`<br>`python -c "import fate; print(fate.__version__)"` | Reinstall into the same environment before trying the deployment path again. |
| `fate_flow start` returns but `fate_flow status` is not healthy | Service home, database, or dependency mismatch | `fate_flow status`<br>`python -m fate.components --help`<br>`netstat -apln | grep 9360` | Do not loop restart commands; inspect the failing service or config first. |
| `bind: address already in use` or the port check shows a listener already there | An old deployment or another app already owns the port | `netstat -apln | grep -E '8080|9360|9380|9370|4670|4671'`<br>`ps -ef | grep -i 'fate_flow\|fateboard\|osx\|clustermanager\|nodemanager'` | Only clear ports you control; otherwise choose a fresh host/port set. |
| Docker commands are missing or Docker Compose is unavailable | Docker is not installed or not on PATH | `docker --version`<br>`docker-compose --version` | Use the PyPI or host-package path until Docker is available. |
| Docker Compose rollout keeps asking for a password or SSH fails with `Permission denied (publickey)` | Keyless SSH between the deployment machine and targets is not ready | `ssh -o BatchMode=yes user@host 'echo ok'` | Do not rerun the rollout until passwordless SSH works. |
| `permission denied while trying to connect to the Docker daemon socket` | The current user cannot access the Docker daemon | `id`<br>`docker ps` | Switch to a user with Docker access before trying Docker paths again. |
| `flow test toy` complains about max cores or never reaches success | Job-core settings do not fit the install | Rerun with the documented toy command and add `--task-cores 1` if the doc-reported core error appears | If the toy smoke still fails, move to service logs instead of changing more parameters blindly. |

## Log locations from the deployment guides

When the service is up but jobs still fail, check the path-specific logs documented by the guides:

- `.../fate_flow/logs/fate_flow`
- `.../eggroll/logs`
- `.../fateboard/logs`
- `.../osx/logs/broker/`
- `.../common/mysql/mysql-*/logs`

For Docker Compose bundles, keep using `docker-compose ps` to confirm container health and then inspect the logs inside the deployed bundle.

## High-level recovery pattern

1. Confirm the command exists in the current environment.
2. Check the port and process owning the deployment surface.
3. Check the path-specific log location.
4. Fix only the dependency that failed.
5. Re-run the service check once, then stop if the same error repeats.

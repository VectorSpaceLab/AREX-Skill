# Experimental Docker Deployment

Read this when a user asks about running Mycodo with Docker or diagnosing a containerized stack. Mycodo's Docker support is explicitly experimental: many parts work, many do not, and compatibility may change between releases.

## When Docker is appropriate

Use Docker only when the user accepts experimental behavior and has a host that can run Docker Engine/Compose. It has been documented on Raspberry Pi OS and Ubuntu Linux. Do not present Docker as the safest production path for a hardware-controller deployment; bare-metal Raspberry Pi OS remains the primary documented install route.

## Main constraints

- A Dockerized Mycodo instance cannot run at the same time as a local non-Docker install using the same ports. Stop local services only with explicit approval:

  ```bash
  sudo service mycodo stop
  sudo service mycodoflask stop
  sudo service nginx stop
  ```

- The compose file contains timezone settings such as `TZ=America/New_York` for daemon and Flask services; change them before building.
- Docker needs access to host devices and ports for hardware features. Treat GPIO/I2C/UART/1-Wire/Bluetooth/camera behavior as host-specific and unverified until tested on the target host.
- Pi Zero builds may need an alternate InfluxDB base image (`mendhak/arm32v6-influxdb`) instead of the default InfluxDB image.
- Grafana and Telegraf blocks are disabled by default and require compose edits plus rebuild.

## Setup outline

Do not run these commands without confirming the target host and Docker risks:

```bash
# Install Docker Engine using official OS-specific Docker instructions first.
sudo usermod -aG docker "$USER"
# Log out/in before using docker without sudo.

cd <Mycodo-release-dir>/docker
# edit docker-compose.yml timezone and optional Grafana/Telegraf blocks first
docker compose up --build -d
```

After a successful build, Mycodo is expected at `https://127.0.0.1/` or the host IP. Grafana, when enabled, is expected at `http://127.0.0.1:3000` with its default admin/admin credential until changed.

## Management commands

Run compose commands from the directory containing `docker-compose.yml`, typically `<Mycodo-release-dir>/docker`:

```bash
docker compose up -d
```

```bash
docker compose down
```

Cleanup can remove images but should preserve volumes only if Docker's defaults are respected:

```bash
docker compose down
docker system prune -a
```

Ask before cleanup; it can remove images and affect other Docker workloads.

## Grafana and Telegraf

To enable Grafana/Telegraf, uncomment the blocks in the compose file before rebuilding. The documented Grafana InfluxDB data source settings include:

- URL: `http://mycodo_influxdb:8086`
- Database: `mycodo_db`
- User: `mycodo`

Change default Grafana credentials immediately on any reachable host.

## Docker troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Web UI port is unavailable | local Mycodo/nginx or another service already uses 80/443 | inspect local services; stop only after approval |
| Build fails on old ARM board | image unsupported for Pi Zero/arm32 | check base image and architecture |
| Device features fail | containers lack device access/permissions or host interfaces | verify `/dev`, privileged settings, udev/group access, and hardware-specific docs |
| Measurements absent | InfluxDB container not healthy or wrong credentials | inspect container logs and `/ping` from inside network |
| Grafana cannot query | Grafana/Telegraf blocks not enabled or wrong data source | confirm compose blocks, service names, and database/user/password |

Because Docker is experimental, prefer collecting logs and reproducing minimal container health before changing control logic or filing broader bugs.

## Compose service and volume anchors

The compose stack includes `mycodo_influxdb`, `mycodo_nginx`, `mycodo_daemon`, and `mycodo_flask`. nginx maps host ports `80` and `443`; optional Grafana maps `3000`. The daemon/Flask containers use persistent named volumes for application state, virtualenv, databases, cameras, logs, SSL certs, custom Inputs, Outputs, Functions, Actions, Widgets, user scripts, CSS, JavaScript, and fonts. The daemon and Flask services use privileged/device-oriented mounts, so do not claim hardware isolation or safety without host-specific verification. Docker Pyro uses `PYRO:mycodo.pyro_server@mycodo_daemon:9080`.

## Verification limits

Docker compose files were inspected but no image build, container startup, named-volume recovery, Grafana/Telegraf setup, InfluxDB operation, privileged hardware access, or port binding was executed during skill production.

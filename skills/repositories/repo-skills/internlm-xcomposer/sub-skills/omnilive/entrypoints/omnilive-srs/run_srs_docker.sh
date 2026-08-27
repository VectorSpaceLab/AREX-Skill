#!/usr/bin/env bash
set -euo pipefail
CANDIDATE="${CANDIDATE:?Set CANDIDATE to the LAN IP visible to browser clients, not 127.0.0.1}"
exec docker run --rm --env CANDIDATE="$CANDIDATE"   -p 1935:1935 -p 8080:8080 -p 1985:1985 -p 8000:8000/udp   registry.cn-hangzhou.aliyuncs.com/ossrs/srs:5   objs/srs -c conf/rtc2rtmp.conf

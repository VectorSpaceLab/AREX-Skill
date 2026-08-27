#!/usr/bin/env bash
set -euo pipefail

# Purpose:
#   Copy the renewed round-robin certificate and key into the bucket path used
#   by the OpenFreeMap certificate publish hook.
#
# Expected certbot deploy-hook variables:
#   RENEWED_LINEAGE   path to the renewed certificate directory
#   RENEWED_DOMAINS   domain name used to build the bucket path
#
# Required local variable:
#   RCLONE_CONFIG     path to the rclone config file
#
# Example deploy-hook invocation:
#   RENEWED_LINEAGE=/etc/letsencrypt/live/ofm_roundrobin \
#   RENEWED_DOMAINS=roundrobin.example.com \
#   RCLONE_CONFIG=/data/ofm/config/rclone.conf \
#   ./rclone_write.sh

: "${RENEWED_LINEAGE:?RENEWED_LINEAGE must be set}"
: "${RENEWED_DOMAINS:?RENEWED_DOMAINS must be set}"
: "${RCLONE_CONFIG:?RCLONE_CONFIG must be set}"

export RCLONE_CONFIG

rclone copyto -v --copy-links "$RENEWED_LINEAGE/fullchain.pem" "remote:ofm-private/roundrobin/$RENEWED_DOMAINS/ofm_roundrobin.cert"
rclone copyto -v --copy-links "$RENEWED_LINEAGE/privkey.pem" "remote:ofm-private/roundrobin/$RENEWED_DOMAINS/ofm_roundrobin.key"

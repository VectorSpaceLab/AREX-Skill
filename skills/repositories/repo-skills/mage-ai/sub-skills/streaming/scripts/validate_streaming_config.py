#!/usr/bin/env python3
"""Validate the connector type in a streaming block config without connecting."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

SUPPORTED_SOURCES = {'activemq', 'amazon_sqs', 'azure_event_hub', 'google_cloud_pubsub', 'influxdb', 'kafka', 'nats', 'kinesis', 'rabbitmq', 'mongodb'}
SUPPORTED_SINKS = {'activemq', 'amazon_s3', 'azure_data_lake', 'bigquery', 'clickhouse', 'druid', 'duckdb', 'dummy', 'elasticsearch', 'google_cloud_pubsub', 'google_cloud_storage', 'influxdb', 'kafka', 'kinesis', 'mongodb', 'mssql', 'mysql', 'opensearch', 'oracledb', 'postgres', 'rabbitmq', 'redshift', 'snowflake', 'trino'}


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate Mage streaming config.')
    parser.add_argument('--config', required=True, help='Path to a YAML config file.')
    parser.add_argument('--role', choices=('source', 'sink'), required=True, help='Whether the config is for a source or sink block.')
    args = parser.parse_args()

    config_path = Path(args.config).expanduser().resolve()
    with config_path.open('r', encoding='utf-8') as handle:
        config = yaml.safe_load(handle) or {}

    connector_type = config.get('connector_type')
    supported = connector_type in (SUPPORTED_SOURCES if args.role == 'source' else SUPPORTED_SINKS)
    print(json.dumps({'config_path': str(config_path), 'role': args.role, 'connector_type': connector_type, 'supported': supported}, indent=2, sort_keys=True))
    return 0 if supported else 1


if __name__ == '__main__':
    raise SystemExit(main())

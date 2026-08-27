"""Safe provider inventory helper for the provider-integrations sub-skill.

This module is intentionally read-only by default:
- no network calls
- no credential access
- no writes unless a caller redirects stdout

It packages the verified 12-provider inventory that the provider-integrations
skill uses for quick review, drift checks, and docs generation.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Any, Sequence

EXPECTED_PROVIDER_COUNT = 12


@dataclass(frozen=True)
class ProviderRecord:
    provider: str
    strategy: str
    display_name: str
    api_base_url: str
    components: tuple[str, ...]
    capabilities: tuple[str, ...]
    coverage_counts: dict[str, int]
    delivery_model: str
    default_live_sync: str
    historical_sync: str
    notes: str = ""


PROVIDER_INVENTORY: tuple[ProviderRecord, ...] = (
    ProviderRecord(
        provider="apple",
        strategy="AppleStrategy",
        display_name="Apple Health",
        api_base_url="",
        components=("AppleWorkouts",),
        capabilities=("client_sdk", "file_import"),
        coverage_counts={"timeseries": 71, "workout_fields": 13, "sleep_fields": 9, "menstrual_cycle_fields": 0, "health_scores": 0},
        delivery_model="client_sdk + file_import",
        default_live_sync="None",
        historical_sync="unsupported",
        notes="HealthKit SDK and Apple XML import only; no cloud OAuth.",
    ),
    ProviderRecord(
        provider="samsung",
        strategy="SamsungStrategy",
        display_name="Samsung Health",
        api_base_url="",
        components=("SamsungWorkouts",),
        capabilities=("client_sdk",),
        coverage_counts={"timeseries": 33, "workout_fields": 13, "sleep_fields": 9, "menstrual_cycle_fields": 0, "health_scores": 0},
        delivery_model="client_sdk",
        default_live_sync="None",
        historical_sync="unsupported",
        notes="SDK-only provider; no cloud OAuth or webhook path.",
    ),
    ProviderRecord(
        provider="garmin",
        strategy="GarminStrategy",
        display_name="Garmin",
        api_base_url="https://apis.garmin.com",
        components=("GarminOAuth", "GarminWorkouts", "Garmin247Data", "GarminWebhookHandler"),
        capabilities=("webhook_stream", "webhook_callback"),
        coverage_counts={"timeseries": 29, "workout_fields": 9, "sleep_fields": 9, "menstrual_cycle_fields": 15, "health_scores": 3},
        delivery_model="webhook_stream + webhook_callback",
        default_live_sync="WEBHOOK",
        historical_sync="webhook_backfill (30-day cap)",
        notes="Historical sync uses the Garmin backfill task rather than the pull API.",
    ),
    ProviderRecord(
        provider="google",
        strategy="GoogleStrategy",
        display_name="Google Health",
        api_base_url="https://health.googleapis.com",
        components=("GoogleOAuth", "GoogleHealthApiWorkouts", "GoogleHealth247Data", "GoogleWebhookHandler", "GoogleWebhookService"),
        capabilities=("client_sdk", "rest_pull", "webhook_ping", "webhook_registration_api"),
        coverage_counts={"timeseries": 34, "workout_fields": 13, "sleep_fields": 9, "menstrual_cycle_fields": 0, "health_scores": 0},
        delivery_model="client_sdk + rest_pull + webhook_ping",
        default_live_sync="PULL",
        historical_sync="pull_api",
        notes="Hybrid provider: Health Connect SDK plus cloud REST rollups.",
    ),
    ProviderRecord(
        provider="polar",
        strategy="PolarStrategy",
        display_name="Polar",
        api_base_url="https://www.polaraccesslink.com",
        components=("PolarOAuth", "PolarWorkouts", "Polar247Data", "PolarWebhookHandler", "polar_webhook_service"),
        capabilities=("rest_pull", "webhook_ping", "webhook_registration_api", "webhook_inbound_secret"),
        coverage_counts={"timeseries": 10, "workout_fields": 4, "sleep_fields": 7, "menstrual_cycle_fields": 0, "health_scores": 4},
        delivery_model="rest_pull + webhook_ping",
        default_live_sync="PULL",
        historical_sync="pull_api",
        notes="Notify-only webhooks; inbound secret is required for verification.",
    ),
    ProviderRecord(
        provider="suunto",
        strategy="SuuntoStrategy",
        display_name="Suunto",
        api_base_url="https://cloudapi.suunto.com",
        components=("SuuntoOAuth", "SuuntoWorkouts", "Suunto247Data", "SuuntoWebhookHandler"),
        capabilities=("rest_pull", "webhook_stream"),
        coverage_counts={"timeseries": 6, "workout_fields": 14, "sleep_fields": 8, "menstrual_cycle_fields": 0, "health_scores": 1},
        delivery_model="rest_pull + webhook_stream",
        default_live_sync="PULL",
        historical_sync="pull_api",
        notes="Full-payload webhook provider with continuous data API.",
    ),
    ProviderRecord(
        provider="whoop",
        strategy="WhoopStrategy",
        display_name="Whoop",
        api_base_url="https://api.prod.whoop.com/developer",
        components=("WhoopOAuth", "WhoopWorkouts", "Whoop247Data", "WhoopWebhookHandler"),
        capabilities=("rest_pull", "webhook_ping"),
        coverage_counts={"timeseries": 6, "workout_fields": 6, "sleep_fields": 8, "menstrual_cycle_fields": 0, "health_scores": 3},
        delivery_model="rest_pull + webhook_ping",
        default_live_sync="PULL",
        historical_sync="pull_api",
        notes="Webhook payloads are notify-only; data is fetched after the ping.",
    ),
    ProviderRecord(
        provider="strava",
        strategy="StravaStrategy",
        display_name="Strava",
        api_base_url="https://www.strava.com",
        components=("StravaOAuth", "StravaWorkouts", "StravaWebhookHandler", "strava_webhook_service"),
        capabilities=("rest_pull", "webhook_ping", "webhook_registration_api"),
        coverage_counts={"timeseries": 4, "workout_fields": 12, "sleep_fields": 0, "menstrual_cycle_fields": 0, "health_scores": 0},
        delivery_model="rest_pull + webhook_ping",
        default_live_sync="PULL",
        historical_sync="pull_api",
        notes="No 24/7 data layer; webhook notifications are activity triggers only.",
    ),
    ProviderRecord(
        provider="oura",
        strategy="OuraStrategy",
        display_name="Oura",
        api_base_url="https://api.ouraring.com",
        components=("OuraOAuth", "OuraWorkouts", "Oura247Data", "OuraWebhookHandler", "oura_webhook_service"),
        capabilities=("rest_pull", "webhook_ping", "webhook_registration_api"),
        coverage_counts={"timeseries": 16, "workout_fields": 3, "sleep_fields": 9, "menstrual_cycle_fields": 0, "health_scores": 3},
        delivery_model="rest_pull + webhook_ping",
        default_live_sync="PULL",
        historical_sync="pull_api",
        notes="Notify-only webhooks with programmatic subscription registration.",
    ),
    ProviderRecord(
        provider="fitbit",
        strategy="FitbitStrategy",
        display_name="Fitbit",
        api_base_url="https://api.fitbit.com",
        components=("FitbitOAuth", "FitbitWorkouts"),
        capabilities=("rest_pull",),
        coverage_counts={"timeseries": 0, "workout_fields": 6, "sleep_fields": 0, "menstrual_cycle_fields": 0, "health_scores": 0},
        delivery_model="rest_pull",
        default_live_sync="PULL",
        historical_sync="pull_api",
        notes="Webhook integration is not enabled in the current strategy.",
    ),
    ProviderRecord(
        provider="ultrahuman",
        strategy="UltrahumanStrategy",
        display_name="Ultrahuman Ring Air",
        api_base_url="https://partner.ultrahuman.com/api/partners/v1",
        components=("UltrahumanOAuth", "Ultrahuman247Data"),
        capabilities=("rest_pull",),
        coverage_counts={"timeseries": 6, "workout_fields": 0, "sleep_fields": 9, "menstrual_cycle_fields": 0, "health_scores": 0},
        delivery_model="rest_pull",
        default_live_sync="PULL",
        historical_sync="pull_api",
        notes="REST-only partner API; no public webhook offering in the current strategy.",
    ),
    ProviderRecord(
        provider="sensorbio",
        strategy="SensorBioStrategy",
        display_name="Sensor Bio",
        api_base_url="https://api.sensorbio.com",
        components=("SensorBioOAuth", "SensorBioWorkouts", "SensorBio247Data"),
        capabilities=("rest_pull",),
        coverage_counts={"timeseries": 8, "workout_fields": 6, "sleep_fields": 8, "menstrual_cycle_fields": 0, "health_scores": 3},
        delivery_model="rest_pull",
        default_live_sync="PULL",
        historical_sync="pull_api",
        notes="REST-only provider with workouts and 24/7 data.",
    ),
)


def provider_count() -> int:
    return len(PROVIDER_INVENTORY)


def validate_provider_count(expected: int = EXPECTED_PROVIDER_COUNT) -> None:
    actual = provider_count()
    if actual != expected:
        raise SystemExit(f"Expected {expected} providers, found {actual}")


def inventory_rows() -> list[dict[str, Any]]:
    return [asdict(record) for record in PROVIDER_INVENTORY]


def render_markdown_table() -> str:
    lines = [
        "| Provider | Strategy | Components | Capabilities | Coverage (ts/wo/sl/mc/hs) | Live sync | Historical sync |",
        "|---|---|---|---|---|---|---|",
    ]
    for record in PROVIDER_INVENTORY:
        c = record.coverage_counts
        coverage = f"{c['timeseries']}/{c['workout_fields']}/{c['sleep_fields']}/{c['menstrual_cycle_fields']}/{c['health_scores']}"
        components = ", ".join(f"`{component}`" for component in record.components)
        capabilities = ", ".join(f"`{capability}`" for capability in record.capabilities)
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{record.provider}`",
                    f"`{record.strategy}`",
                    components,
                    capabilities,
                    coverage,
                    record.default_live_sync,
                    record.historical_sync,
                ]
            )
            + " |"
        )
    lines.append("")
    lines.append(f"Verified provider count: {provider_count()}")
    return "\n".join(lines)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print the verified Open Wearables provider inventory without touching network or credentials.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a markdown table.",
    )
    parser.add_argument(
        "--check-count",
        action="store_true",
        help="Exit non-zero unless the inventory still contains the expected provider count.",
    )
    parser.add_argument(
        "--expected-count",
        type=int,
        default=EXPECTED_PROVIDER_COUNT,
        help="Expected provider count used by --check-count (default: 12).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.check_count:
        validate_provider_count(args.expected_count)

    if args.json:
        print(json.dumps(inventory_rows(), indent=2, sort_keys=True))
    else:
        print(render_markdown_table())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

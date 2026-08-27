#!/usr/bin/env python3
"""Inspect an authorized-user token JSON; live Drive check is opt-in."""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--token-path", required=True)
    parser.add_argument("--expect-email")
    parser.add_argument("--live-drive-check", action="store_true")
    args = parser.parse_args()
    path = Path(args.token_path)
    if not path.is_file():
        print("FAIL token file not found")
        return 1
    try:
        data = json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL invalid JSON: {exc}")
        return 1
    print("OK json")
    for key in ("client_id", "client_secret", "refresh_token", "token"):
        print(("OK" if data.get(key) else "WARN") + f" {key}")
    expiry = data.get("expiry")
    if expiry:
        try:
            dt = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
            print("expiry", dt.isoformat())
            if dt < datetime.now(timezone.utc):
                print("WARN expired")
        except Exception:
            print("WARN could not parse expiry")
    email = data.get("email") or data.get("id_token_email")
    if args.expect_email and email and email.lower() != args.expect_email.lower():
        print(f"FAIL email claim {email} != expected {args.expect_email}")
        return 1
    if args.expect_email and not email:
        print("WARN no local email claim; use --live-drive-check for definitive account")
    if args.live_drive_check:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        creds = Credentials.from_authorized_user_file(str(path), ["https://www.googleapis.com/auth/drive"])
        about = build("drive", "v3", credentials=creds, cache_discovery=False).about().get(fields="user(emailAddress)").execute()
        live = about.get("user", {}).get("emailAddress")
        print("live_email", live)
        if args.expect_email and live and live.lower() != args.expect_email.lower():
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

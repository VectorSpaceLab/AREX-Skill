#!/usr/bin/env python3
"""Safely configure a tiny in-memory Django project and import ChatterBot models."""
from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check ChatterBot Django integration with in-memory sqlite settings.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = {"ok": False}
    try:
        from django.conf import settings

        if not settings.configured:
            settings.configure(
                INSTALLED_APPS=["django.contrib.contenttypes", "chatterbot.ext.django_chatterbot"],
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                SECRET_KEY="chatterbot-diagnostic",
                USE_TZ=True,
                DEFAULT_AUTO_FIELD="django.db.models.AutoField",
            )

        import django
        django.setup()

        from chatterbot.ext.django_chatterbot.models import Statement, Tag
        from chatterbot.storage import DjangoStorageAdapter

        adapter = DjangoStorageAdapter()
        result = {
            "ok": True,
            "django_version": django.get_version(),
            "statement_model": f"{Statement._meta.app_label}.{Statement.__name__}",
            "tag_model": f"{Tag._meta.app_label}.{Tag.__name__}",
            "adapter_database": adapter.database,
            "adapter_statement_model": adapter.statement_model,
            "adapter_tag_model": adapter.tag_model,
        }
    except Exception as exc:
        result = {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

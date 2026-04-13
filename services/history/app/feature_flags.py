from __future__ import annotations

import logging

from app.config import Settings

logger = logging.getLogger(__name__)


class FeatureFlags:
    def __init__(self, settings: Settings) -> None:
        self._client = None
        if not settings.unleash_url:
            logger.info("Unleash URL not set; feature flags default to disabled")
            return
        try:
            from UnleashClient import UnleashClient

            client = UnleashClient(
                url=settings.unleash_url,
                app_name=settings.unleash_app_name,
                custom_headers={"Authorization": settings.unleash_api_token or ""},
                refresh_interval=15,
                disable_metrics=True,
            )
            client.initialize_client()
            self._client = client
        except Exception as exc:
            logger.warning("Unleash initialization failed: %s", exc)

    def is_enabled(self, flag: str, default: bool = False) -> bool:
        if self._client is None:
            return default
        try:
            return self._client.is_enabled(flag, default_value=default)
        except Exception as exc:
            logger.warning("Unleash lookup failed for %s: %s", flag, exc)
            return default

    def shutdown(self) -> None:
        if self._client is not None:
            try:
                self._client.destroy()
            except Exception:
                pass

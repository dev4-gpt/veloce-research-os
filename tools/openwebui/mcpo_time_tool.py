"""
title: Veloce MCPO Time
author: Veloce AI
version: 0.1.0
description: Call the Veloce MCPO time bridge through the internal proxy.
"""

import json
import os
import urllib.request


class Tools:
    async def get_current_time(self, timezone: str = "America/New_York") -> str:
        """
        Get the current time for a timezone from the MCPO time bridge.

        Args:
            timezone: IANA timezone name, for example America/New_York or UTC.
        """
        api_key = os.environ.get("MCPO_API_KEY", "")
        if not api_key:
            return json.dumps(
                {
                    "ok": False,
                    "error": "MCPO_API_KEY is not available inside Open WebUI",
                },
                indent=2,
            )

        payload = json.dumps({"timezone": timezone}).encode()
        request = urllib.request.Request(
            "http://mcpo-openwebui-proxy:8080/get_current_time",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.read().decode("utf-8")
        except Exception as exc:
            return json.dumps(
                {
                    "ok": False,
                    "error": "MCPO time request failed",
                    "error_type": exc.__class__.__name__,
                    "detail": str(exc),
                },
                indent=2,
            )

    async def convert_time(
        self,
        source_timezone: str,
        target_timezone: str,
        time: str,
    ) -> str:
        """
        Convert a time between timezones using the MCPO time bridge.

        Args:
            source_timezone: Source IANA timezone name.
            target_timezone: Target IANA timezone name.
            time: Time string accepted by the upstream MCP time server.
        """
        api_key = os.environ.get("MCPO_API_KEY", "")
        if not api_key:
            return json.dumps(
                {
                    "ok": False,
                    "error": "MCPO_API_KEY is not available inside Open WebUI",
                },
                indent=2,
            )

        payload = json.dumps(
            {
                "source_timezone": source_timezone,
                "target_timezone": target_timezone,
                "time": time,
            }
        ).encode()
        request = urllib.request.Request(
            "http://mcpo-openwebui-proxy:8080/convert_time",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.read().decode("utf-8")
        except Exception as exc:
            return json.dumps(
                {
                    "ok": False,
                    "error": "MCPO convert request failed",
                    "error_type": exc.__class__.__name__,
                    "detail": str(exc),
                },
                indent=2,
            )

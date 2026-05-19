"""
title: Veloce MCPO Stack
author: Veloce AI
version: 0.1.0
description: Call the Veloce MCPO stack status bridge through the internal proxy.
"""

import json
import os
import urllib.request


class Tools:
    async def stack_status(self) -> str:
        """
        Get read-only health/status for the Veloce stack.
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

        request = urllib.request.Request(
            "http://mcpo-openwebui-proxy:8080/stack_status",
            data=b"{}",
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
                    "error": "MCPO stack status request failed",
                    "error_type": exc.__class__.__name__,
                    "detail": str(exc),
                },
                indent=2,
            )

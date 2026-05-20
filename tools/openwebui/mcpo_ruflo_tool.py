"""
title: Veloce MCPO Ruflo
author: Veloce AI
version: 0.1.0
description: Call the read-only Veloce Ruflo sandbox status bridge through the internal proxy.
"""

import json
import os
import urllib.request


class Tools:
    async def ruflo_status(self, scope: str = "sandbox") -> str:
        """
        Get read-only status for the Ruflo planning sandbox.

        Args:
            scope: Status scope. Use "sandbox" for the hardened Ruflo sandbox.
        """
        if scope != "sandbox":
            return json.dumps(
                {
                    "ok": False,
                    "error": "invalid scope; allowed scope is sandbox",
                },
                indent=2,
            )

        api_key = os.environ.get("MCPO_API_KEY", "")
        if not api_key:
            return json.dumps(
                {
                    "ok": False,
                    "error": "MCPO_API_KEY is not available inside Open WebUI",
                },
                indent=2,
            )

        payload = json.dumps({"scope": scope}).encode()
        request = urllib.request.Request(
            "http://mcpo-openwebui-proxy:8080/ruflo_status",
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
                    "error": "MCPO Ruflo status request failed",
                    "error_type": exc.__class__.__name__,
                    "detail": str(exc),
                },
                indent=2,
            )

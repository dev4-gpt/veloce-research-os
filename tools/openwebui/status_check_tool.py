"""
title: Veloce Status Check
author: Veloce AI
version: 0.1.0
description: Check the health of allowlisted Veloce AI stack services through the internal status_check server.
"""

import json
import urllib.request


class Tools:
    async def status_check(self, target: str, timeout_ms: int = 1500) -> str:
        """
        Check one allowlisted Veloce AI stack target.

        Args:
            target: One of openwebui, hermes, paperclip, research_repo.
            timeout_ms: Timeout in milliseconds from 500 to 5000.
        """
        allowed_targets = {"openwebui", "hermes", "paperclip", "research_repo"}
        if target not in allowed_targets:
            return json.dumps(
                {
                    "ok": False,
                    "target": target,
                    "detail": "invalid target; allowed targets are openwebui, hermes, paperclip, research_repo",
                },
                indent=2,
            )

        timeout_ms = max(500, min(int(timeout_ms), 5000))
        payload = json.dumps({"target": target, "timeout_ms": timeout_ms}).encode()
        request = urllib.request.Request(
            "http://status-tool:8080/status_check",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=timeout_ms / 1000) as response:
                return response.read().decode("utf-8")
        except Exception as exc:
            return json.dumps(
                {
                    "ok": False,
                    "target": target,
                    "detail": f"status_check request failed: {exc.__class__.__name__}",
                },
                indent=2,
            )

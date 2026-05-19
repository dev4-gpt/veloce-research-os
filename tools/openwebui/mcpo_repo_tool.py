"""
title: Veloce MCPO Repo
author: Veloce AI
version: 0.1.0
description: Call the Veloce MCPO repo status bridge through the internal proxy.
"""

import json
import os
import urllib.request


class Tools:
    async def repo_status(self, scope: str = "current") -> str:
        """
        Get read-only git status for the Veloce research repository.

        Args:
            scope: Status scope. Use "current" for branch, commit, dirty state, and last commit.
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
            "http://mcpo-openwebui-proxy:8080/repo_status",
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
                    "error": "MCPO repo status request failed",
                    "error_type": exc.__class__.__name__,
                    "detail": str(exc),
                },
                indent=2,
            )

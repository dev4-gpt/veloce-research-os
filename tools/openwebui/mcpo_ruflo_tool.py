"""
title: Veloce MCPO Ruflo
author: Veloce AI
version: 0.1.0
description: Call the read-only Veloce Ruflo sandbox status and planning bridges through the internal proxy.
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

    async def ruflo_plan(
        self,
        title: str,
        description: str,
        issue_id: str = "",
        priority: str = "medium",
        assignee: str = "Technical Builder",
        labels: str = "",
        requested_mode: str = "plan",
    ) -> str:
        """
        Create a planning-only Ruflo bridge plan for a Paperclip-shaped issue.

        Args:
            title: Paperclip issue title.
            description: Paperclip issue description or acceptance criteria.
            issue_id: Optional Paperclip issue id, for example VEL-128.
            priority: Optional issue priority.
            assignee: Optional planned owner.
            labels: Optional comma-separated labels.
            requested_mode: Must be "plan"; execution modes are blocked.
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
                "title": title,
                "description": description,
                "issue_id": issue_id,
                "priority": priority,
                "assignee": assignee,
                "labels": labels,
                "requested_mode": requested_mode,
            }
        ).encode()
        request = urllib.request.Request(
            "http://mcpo-openwebui-proxy:8080/ruflo_plan",
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
                    "error": "MCPO Ruflo plan request failed",
                    "error_type": exc.__class__.__name__,
                    "detail": str(exc),
                },
                indent=2,
            )

    async def ruflo_execution_packet(
        self,
        title: str,
        description: str,
        approved_by: str,
        issue_id: str = "",
        plan_trace_id: str = "",
        execution_owner: str = "Codex/GitHub",
        labels: str = "",
        approval: str = "human_approved",
        requested_mode: str = "execution_packet",
    ) -> str:
        """
        Create an approval-gated execution packet for a Paperclip issue.

        This does not run Ruflo. It produces the Paperclip handoff needed for a
        human/Codex/GitHub/VPS execution loop.

        Args:
            title: Paperclip issue title.
            description: Paperclip issue description or accepted plan summary.
            approved_by: Human approver name.
            issue_id: Optional Paperclip issue id, for example VEL-128.
            plan_trace_id: Optional trace id from a previous ruflo_plan call.
            execution_owner: Owner that will execute outside Ruflo runtime.
            labels: Optional comma-separated labels.
            approval: Must be "human_approved".
            requested_mode: Must be "execution_packet"; runtime execution is blocked.
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
                "title": title,
                "description": description,
                "approved_by": approved_by,
                "issue_id": issue_id,
                "plan_trace_id": plan_trace_id,
                "execution_owner": execution_owner,
                "labels": labels,
                "approval": approval,
                "requested_mode": requested_mode,
            }
        ).encode()
        request = urllib.request.Request(
            "http://mcpo-openwebui-proxy:8080/ruflo_execution_packet",
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
                    "error": "MCPO Ruflo execution packet request failed",
                    "error_type": exc.__class__.__name__,
                    "detail": str(exc),
                },
                indent=2,
            )

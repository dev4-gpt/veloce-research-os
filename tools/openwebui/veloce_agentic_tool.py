"""
title: Veloce Agentic Control
author: Veloce AI
version: 0.1.0
description: Full Veloce v1.9 OpenWebUI tool surface for status, Hermes, Ruflo, and autonomy dry-run controls.
"""

import json
import os
import urllib.request


class Tools:
    def _call(self, path: str, payload: dict) -> str:
        api_key = os.environ.get("MCPO_API_KEY", "")
        if not api_key:
            return json.dumps(
                {"ok": False, "error": "MCPO_API_KEY is not available inside Open WebUI"},
                indent=2,
            )
        request = urllib.request.Request(
            f"http://mcpo-openwebui-proxy:8080{path}",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8")
        except Exception as exc:
            return json.dumps(
                {
                    "ok": False,
                    "path": path,
                    "error": "Veloce agentic tool request failed",
                    "error_type": exc.__class__.__name__,
                    "detail": str(exc),
                },
                indent=2,
            )

    async def veloce_stack_status(self) -> str:
        """Check the Veloce stack through the MCPO proxy."""
        return self._call("/stack_status", {})

    async def veloce_repo_status(self) -> str:
        """Check the Veloce Git repository through the MCPO proxy."""
        return self._call("/repo_status", {})

    async def veloce_ruflo_status(self) -> str:
        """Check the hardened Ruflo sandbox status."""
        return self._call("/ruflo_status", {"scope": "sandbox"})

    async def veloce_hermes_memory_query(self, query: str, dry_run: bool = False) -> str:
        """
        Ask Hermes for project memory or operator context.

        Args:
            query: Memory/context query for Hermes.
            dry_run: When true, validate the bridge without invoking Hermes.
        """
        return self._call("/hermes_memory_query", {"query": query, "dry_run": dry_run})

    async def veloce_hermes_agent_task(
        self,
        task: str,
        context: str = "",
        dry_run: bool = False,
    ) -> str:
        """
        Ask Hermes to perform a structured agent reasoning task.

        Args:
            task: Agent reasoning task.
            context: Optional project/task context.
            dry_run: When true, validate the bridge without invoking Hermes.
        """
        return self._call(
            "/hermes_agent_task",
            {"task": task, "context": context, "dry_run": dry_run},
        )

    async def veloce_ruflo_orchestration_dry_run(
        self,
        goal: str,
        issue_id: str = "",
    ) -> str:
        """
        Create a Ruflo-style orchestration task graph without running Ruflo.

        Args:
            goal: Work goal to turn into a policy-governed task graph.
            issue_id: Optional Paperclip issue id.
        """
        return self._call(
            "/ruflo_orchestration_dry_run",
            {"goal": goal, "issue_id": issue_id, "requested_mode": "dry_run"},
        )

    async def veloce_ruflo_execution_packet(
        self,
        title: str,
        description: str,
        approved_by: str,
        issue_id: str = "",
    ) -> str:
        """
        Create a Ruflo execution packet without running Ruflo.

        Args:
            title: Issue or work title.
            description: Accepted plan summary.
            approved_by: Human approver name.
            issue_id: Optional Paperclip issue id.
        """
        return self._call(
            "/ruflo_execution_packet",
            {
                "title": title,
                "description": description,
                "approved_by": approved_by,
                "issue_id": issue_id,
                "approval": "human_approved",
                "requested_mode": "execution_packet",
            },
        )

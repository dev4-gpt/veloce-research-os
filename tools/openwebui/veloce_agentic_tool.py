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

    async def veloce_knowledge_graph_status(self) -> str:
        """Inspect the Veloce Graphify knowledge graph status."""
        return self._call("/knowledge_graph_status", {})

    async def veloce_knowledge_graph_query(
        self,
        question: str,
        max_results: int = 8,
        source_filter: str = "docs",
        answer_style: str = "summary",
        include_relationships: bool = True,
    ) -> str:
        """
        Query the Veloce Graphify knowledge graph.

        Args:
            question: Knowledge graph question about Veloce docs, code, runbooks, or architecture.
            max_results: Maximum graph nodes/evidence docs to return.
            source_filter: docs, knowledge, code, tests, or all. Defaults to docs for product/architecture analysis.
            answer_style: summary for a graph-grounded narrative, or raw for compact legacy output.
            include_relationships: Include nearby graph relationships in the response.
        """
        return self._call(
            "/knowledge_graph_query",
            {
                "question": question,
                "max_results": max_results,
                "source_filter": source_filter,
                "answer_style": answer_style,
                "include_relationships": include_relationships,
            },
        )

    async def veloce_knowledge_memory_record(
        self,
        source_system: str,
        event_type: str,
        summary: str,
        evidence_refs: list[str] | None = None,
        tags: list[str] | None = None,
        dry_run: bool = True,
    ) -> str:
        """
        Create a secret-free memory event packet for Obsidian and Graphify ingestion.

        Args:
            source_system: System that produced the event, such as openwebui, paperclip, hermes, mcpo, ruflo, github, vps, or obsidian.
            event_type: Short event class such as tool_call, issue_closeout, graph_update, or demo_proof.
            summary: Secret-free summary of what happened.
            evidence_refs: Optional public-safe evidence references.
            tags: Optional graph tags.
            dry_run: Keep true unless a mounted knowledge memory write path is configured.
        """
        return self._call(
            "/knowledge_memory_record",
            {
                "source_system": source_system,
                "event_type": event_type,
                "summary": summary,
                "evidence_refs": evidence_refs or [],
                "tags": tags or [],
                "dry_run": dry_run,
            },
        )

    async def veloce_production_execution_status(self) -> str:
        """Inspect V2 production execution jobs, runner state, and audit ledgers."""
        return self._call("/production_execution_status", {})

    async def veloce_production_job_enqueue(
        self,
        job_id: str,
        capability: str,
        issue_id: str = "",
        budget_minutes: int = 5,
        max_attempts: int = 1,
        heartbeat_seconds: int = 60,
    ) -> str:
        """
        Queue a typed dry-run production job packet.

        Args:
            job_id: Stable job id using letters, numbers, dots, dashes, or underscores.
            capability: Allowlisted capability such as paperclip_writeback, chat_to_pr, chat_to_canary_deploy, autonomous_rollback, long_running_agent_jobs, active_alerting, or graph_memory_ingestion.
            issue_id: Optional Paperclip/Veloce issue id.
            budget_minutes: Maximum job budget in minutes.
            max_attempts: Maximum runner attempts.
            heartbeat_seconds: Heartbeat interval for long-running work.
        """
        return self._call(
            "/production_job_enqueue",
            {
                "job_id": job_id,
                "capability": capability,
                "issue_id": issue_id,
                "budget_minutes": budget_minutes,
                "max_attempts": max_attempts,
                "heartbeat_seconds": heartbeat_seconds,
            },
        )

    async def veloce_production_job_status(self, job_id: str) -> str:
        """
        Inspect one typed production job packet and runner state.

        Args:
            job_id: Job id returned by veloce_production_job_enqueue or the V2 control plane.
        """
        return self._call("/production_job_status", {"job_id": job_id})

    async def veloce_production_job_cancel(
        self,
        job_id: str,
        reason: str = "operator_cancelled",
    ) -> str:
        """
        Cancel a queued or running typed production job.

        Args:
            job_id: Job id to cancel.
            reason: Secret-free cancellation reason.
        """
        return self._call("/production_job_cancel", {"job_id": job_id, "reason": reason})

    async def veloce_production_job_approve(
        self,
        job_id: str,
        approved_by: str,
        approval: str = "human_approved",
    ) -> str:
        """
        Mark a queued dry-run packet as approved_for_live_candidate without executing it.

        Args:
            job_id: Job id to approve.
            approved_by: Human approver name.
            approval: Must be human_approved.
        """
        return self._call(
            "/production_job_approve",
            {"job_id": job_id, "approved_by": approved_by, "approval": approval},
        )

    async def veloce_production_audit_tail(self, limit: int = 20) -> str:
        """
        Return a redacted tail of production execution audit events.

        Args:
            limit: Maximum audit records to return, clamped by the server.
        """
        return self._call("/production_audit_tail", {"limit": limit})

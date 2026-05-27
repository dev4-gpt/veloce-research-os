---
title: Obsidian And Graphify Memory Loop
source_system: obsidian-graphify
generated_at: 2026-05-27T04:40:54Z
commit: 450b5c6
tags: [obsidian, graphify, memory]
---

# Obsidian And Graphify Memory Loop

## Human Layer

Obsidian stores readable markdown notes, issue evidence, runbooks, generated memory packets, and operator closeouts.

## Machine Layer

Graphify extracts a graph from code, docs, runbooks, and graph-memory markdown into `graphify-out/graph.json`.

Graph-memory markdown files are the preferred human-facing evidence nodes. `manifest.json` exists for automation bookkeeping and should not outrank markdown notes in normal product queries.

V2.1-V2.5 production job events are emitted as secret-free markdown under the derived graph-memory event directory, then can be mirrored into Obsidian and re-extracted by Graphify.

V2.6-V3.1 pilot pack events are emitted as secret-free markdown and audit JSONL so OpenWebUI can query what is ready, blocked, or awaiting live approval.

## Chat Layer

OpenWebUI calls `knowledge_graph_status`, `knowledge_graph_query`, and `knowledge_memory_record` through MCPO. The query endpoint uses docs-first ranking for product questions and can filter docs, code, tests, or all sources.

## Public Safety

Raw graph files should not be published to the public showcase until a separate redaction and public-safety scan exists.

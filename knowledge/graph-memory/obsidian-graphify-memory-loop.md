---
title: Obsidian And Graphify Memory Loop
source_system: obsidian-graphify
generated_at: 2026-05-21T18:41:53Z
commit: c038eb7
tags: [obsidian, graphify, memory]
---

# Obsidian And Graphify Memory Loop

## Human Layer

Obsidian stores readable markdown notes, issue evidence, runbooks, generated memory packets, and operator closeouts.

## Machine Layer

Graphify extracts a graph from code, docs, runbooks, and graph-memory markdown into `graphify-out/graph.json`.

Graph-memory markdown files are the preferred human-facing evidence nodes. `manifest.json` exists for automation bookkeeping and should not outrank markdown notes in normal product queries.

## Chat Layer

OpenWebUI calls `knowledge_graph_status`, `knowledge_graph_query`, and `knowledge_memory_record` through MCPO. The query endpoint uses docs-first ranking for product questions and can filter docs, code, tests, or all sources.

## Public Safety

Raw graph files should not be published to the public showcase until a separate redaction and public-safety scan exists.

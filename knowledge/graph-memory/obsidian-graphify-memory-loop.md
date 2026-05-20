---
title: Obsidian And Graphify Memory Loop
source_system: obsidian-graphify
generated_at: 2026-05-20T21:23:34Z
commit: 98f1e06
tags: [obsidian, graphify, memory]
---

# Obsidian And Graphify Memory Loop

## Human Layer

Obsidian stores readable markdown notes, issue evidence, runbooks, generated memory packets, and operator closeouts.

## Machine Layer

Graphify extracts a graph from code, docs, runbooks, and graph-memory markdown into `graphify-out/graph.json`.

## Chat Layer

OpenWebUI calls `knowledge_graph_status`, `knowledge_graph_query`, and `knowledge_memory_record` through MCPO. The query endpoint uses docs-first ranking for product questions and can filter docs, code, tests, or all sources.

## Public Safety

Raw graph files should not be published to the public showcase until a separate redaction and public-safety scan exists.

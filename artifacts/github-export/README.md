# Nexus Global — End-to-End Architecture Blueprint

This repository contains the end-to-end architecture blueprint for the Nexus Global Transaction Banking Platform: an ontology-driven, streaming-enabled, governance-hardened platform for global transaction banking (CB/CM/WM).

It is designed to be:
- Executable by engineers.
- Clear enough for leadership (CDO/CTO/CRO).
- Strict: no marketing, no vague promises.

## How to Use This Blueprint

Start with:
- 00 — End-to-End Architecture (single-page reference)
- diagrams/end-to-end-blueprint.mmd (visual blueprint)

Then go dimension by dimension:
- 01 — Logical Model (canonical graph, nodes, edges, interfaces, kinetic constructs)
- 02 — Materialization Strategy (Neo4j, PostgreSQL, Delta Lake, Redis, CDC)
- 03 — Platform Infrastructure (Confluent, Flink, Databricks, networking, operations)
- 04 — API & Integration Contract (Entity Platform API as ontology action surface)
- 05 — Governance & Trust Layer (proof, mandates, ZKP, auditability)
- 06 — Data Streaming Plan (Confluent/Kafka: roles, topology, topics, guarantees)
- 07 — Stream Computing Plan (Apache Flink: runtime, jobs, Flink-specific use cases)

Decisions:
- decisions/ADR-001-streaming-backbone-confluent.md
- decisions/ADR-002-stream-computing-flink-k8s.md

Presentations (Pinned):
- presentations/leadership-blueprint-presentation.pptx (leadership-ready deck, blueprint style)

  - Branch: project/global-tbp-architecture
  - Direct view:
    - https://github.com/danielssonn/dataarch/blob/project/global-tbp-architecture/artifacts/github-export/presentations/leadership-blueprint-presentation.pptx
  - Shared download link:
    - https://github.com/danielssonn/dataarch/raw/project/global-tbp-architecture/artifacts/github-export/presentations/leadership-blueprint-presentation.pptx

This is opinionated, not generic. Everything ties to the same ontology and the same platform.

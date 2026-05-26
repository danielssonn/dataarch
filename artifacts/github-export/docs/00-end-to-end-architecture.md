# 00 — End-to-End Architecture

**Project:** Nexus Global Transaction Banking Platform  
**Type:** Single-page blueprint reference  
**Status:** Draft for Daniel's review

## 1. Purpose

Define a regulated, ontology-driven, real-time-capable GTB platform that:
- Unifies CB/CM/WM under one canonical model.
- Governs all data, actions, and integrations.
- Enables streaming and Flink for real-time intelligence.

No marketing fluff; this is the architecture we can build.

## 2. High-Level Architecture

```mermaid
flowchart LR
  subgraph Sources
    A[Entity Platform API]
    B[Neo4j Canonical Graph]
    C[PostgreSQL Kinetic + Proof + Mandates]
    D[Vendor Systems (TF / SCF)]
    E[Core Banking / LOB Systems]
    F[ML / AI Services]
  end

  subgraph Confluent [Confluent Cloud (Streaming Backbone)]
    G[Schema Registry]
    H[Topics: domain / kinetic / cdc / vendor / governance]
  end

  subgraph Flink [Flink on Kubernetes (Stream Computing)]
    I[Flink: Kinetic Incident Correlation]
    J[Flink: Vendor Risk + Containment]
    K[Flink: Real-Time Rule Enforcement]
    L[Flink: Reporting + Statements]
    M[Flink: Cash Flow Forecasting]
    N[Flink: Liquidity Monitoring]
  end

  subgraph Core [Core Stores + Lakehouse]
    O[Neo4j (Operational Graph)]
    P[PostgreSQL (Kinetic + Proof + Mandates)]
    Q[Databricks / Delta Lake (Analytics + History)]
    R[Redis (Hot Cache)]
  end

  subgraph Consumers
    S[Fraud / Risk / Compliance]
    T[Vendor / LOB / Ops]
    U[Agentic Decisioning]
  end

  A -->|Action / Domain Events| H
  B -->|Graph CDC| H
  C -->|CDC: kinetic/proof/mandates| H
  D -->|Vendor Events| H
  E -->|Core Banking Events| H

  H -->|Graph writes (curated)| O
  H -->|Streaming sink (Delta Lake)| Q
  H -->|Governance/audit sinks| S

  I -->|Review Queue / Compensations| H
  J -->|Containment Alerts| H
  K -->|Rule Triggers / Alerts| H
  L -->|Reporting / Statement Streams| H
  M -->|Cash Flow Forecast Events| H
  N -->|Liquidity Alerts / Actions| H

  H -->|Event-Driven Invalidation| R
  G -.->|Schema Enforcement| H
```

## 3. Key Pillars

- **One canonical graph (Neo4j):**
  - Source of truth for parties, products, accounts, transactions, obligations, mandates, vendor systems.
  - All operational traversals and entitlement checks.

- **Kinetic + governance in PostgreSQL:**
  - Action types, instances, business rules, functions.
  - Proof registry (append-only, SHA-256 chained).
  - Mandate hierarchy: HumanMandate → SystemMandate → AgentMandate.

- **Delta Lake (Databricks) for analytics/history:**
  - CDC-synced from Neo4j and PostgreSQL.
  - LOB projections: tb_cb, tb_cm, tb_wm.
  - Containment zone analytics: tb_containment.

- **Redis for hot paths:**
  - Entitlements, mandates, hot node/edge lookups.
  - Invalidation via Confluent streams.

- **Confluent Cloud as streaming backbone:**
  - CDC for Neo4j and PostgreSQL.
  - Transport for kinetic/domain/vendor/governance events.
  - Schema-locked, governed, not a random event bus.

- **Flink on Kubernetes (AKS) for stream computing:**
  - Stateful, real-time correlation and complex event processing.
  - Powers reporting, statements, cash flow forecasting, liquidity monitoring.

## 4. Where to Go Next

- Logical Model: docs/01-logical-model.md
- Materialization: docs/02-materialization-strategy.md
- Infrastructure: docs/03-platform-infrastructure.md
- API Contract: docs/04-api-integration-contract.md
- Governance: docs/05-governance-trust-layer.md
- Streaming Plan: docs/06-data-streaming-plan.md
- Stream Computing Plan: docs/07-stream-computing-plan.md

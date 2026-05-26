# 03 — Platform Infrastructure

**Project:** Nexus Global Transaction Banking Platform  
**Type:** Infrastructure and runtime architecture  
**Status:** Draft for Daniel's review

## 1. Core Components

The runtime is composed of tightly integrated, governed services:

- Confluent Cloud (Dedicated) on Azure:
  - Streaming backbone for CDC, kinetic events, vendor events, governance/audit events.
  - Schema-locked via Schema Registry.
  - Private link and VPC-peered to Nexus Global environment.

- Flink on Kubernetes (AKS):
  - Stream computation layer.
  - Stateful joins, CEP, windowed aggregations.
  - Exactly-once for critical decision jobs.

- Neo4j:
  - Operational graph for canonical entities and relationships.

- PostgreSQL:
  - Kinetic actions, proof registry, mandate hierarchy.

- Databricks / Delta Lake:
  - Analytics, history, LOB projections, containment zone.

- Redis (Azure Cache for Redis):
  - Hot cache for latency-critical paths.

## 2. Confluent Cloud — Streaming Backbone

Responsibilities:
- CDC from Neo4j and PostgreSQL.
- Event bus for kinetic actions and domain events.
- Integration transport for vendor-hosted and internal systems.
- Audit/governance event streams.

Not:
- A general-purpose messaging system.
- A replacement for synchronous APIs.

Security:
- mTLS, per-topic ACLs.
- Schema Registry enforced.
- Service accounts only; no anonymous access.

## 3. Flink on Kubernetes (AKS) — Stream Computing

Rationale:
- No “dumb pipes.”
- We need real-time correlation and decisions over multiple event streams.

Runtime:
- State backend: RocksDB.
- Checkpointing: every 30–60 seconds to Azure Blob Storage.
- Exactly-once for critical jobs.

Primary Flink jobs:
- Kinetic Incident Correlation.
- Vendor Risk + Containment.
- Real-Time Rule Enforcement.
- Reporting + Statements.
- Cash Flow Forecasting.
- Liquidity Monitoring.

## 4. Databricks / Delta Lake

- Analytical hub:
  - Time-travel.
  - Unity Catalog governance.
  - LOB projections.
  - KPIs, regulatory exports, ML/analytics.

Ingestion:
- Structured Streaming from Confluent:
  - cdc.neo4j.graph-changes → tb_canonical.entity
  - cdc.postgres.kinetic → tb_canonical.kinetic
  - domain/kinetic/governance events → analytics.

## 5. Networking & Security

- Azure VNet:
  - Databricks, PostgreSQL, Neo4j in same private network.
- API Gateway:
  - Azure API Management or equivalent for Entity Platform API.
- Ingress from vendor systems:
  - Limited via API Gateway → vendor ingestion endpoints → vendor.* topics.

## 6. Operational Model

- Monitoring:
  - Confluent: topic-level lag, throughput, errors.
  - Flink: job-level metrics, state size, checkpoint health.
  - Neo4j/PostgreSQL: standard DBA monitoring.
- Reliability:
  - Confluent/Databricks: managed services.
  - Flink: K8s-native deployment with HPA and observability.

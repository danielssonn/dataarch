# ADR-001: Streaming Backbone — Confluent Cloud (Dedicated)

**Status:** Proposed  
**Date:** 2026-05-26

## Context

We need a unified, governed, replayable event backbone for:
- CDC from Neo4j and PostgreSQL.
- Kinetic action events.
- Vendor integration events.
- Governance/audit events.
Ad hoc Kafka or file-based transports are not acceptable in this environment.

## Options Considered

| Option            | Pros                         | Cons                                  |
|-------------------|------------------------------|----------------------------------------|
| Confluent Cloud (Dedicated) | Fully managed, mature, strong security/observability, Confluent ecosystem (Schema Registry, Connect, KSQL). | Slight vendor lock-in vs vanilla Kafka; cost. |
| Self-managed Kafka on AKS   | Maximum control, aligns tightly with internal Kubernetes footprint. | High operational burden, custom hardening needed. |
| Managed service from another vendor | Possible cost savings. | Less aligned with existing integrations (Neo4j, Debezium, Databricks). |

## Decision

Use **Confluent Cloud (Dedicated)** on Azure as the streaming backbone, with:
- Private link / VPC peering to Nexus Global.
- mTLS, RBAC, per-topic ACLs.
- Schema Registry mandatory for all topics.
- Debezium for PostgreSQL CDC; Neo4j Kafka Connector for graph CDC.
- Fallback to self-managed on AKS only if bank IT policy strictly requires it.

## Consequences

- Single canonical transport for all events and CDC.
- Lower operational overhead vs self-managed.
- Strong regulatory alignment (BCBS-239-style patterns, audit logs).

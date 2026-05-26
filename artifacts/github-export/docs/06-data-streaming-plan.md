# 06 — Data Streaming Plan

**Project:** Nexus Global Transaction Banking Platform  
**Type:** Confluent / Kafka as streaming backbone  
**Status:** Draft for Daniel's review

## 1. Purpose

Confluent (Kafka) is the canonical event backbone. It serves three roles, nothing more:

1. CDC transport:
   - Neo4j → Confluent → Delta Lake / audit.
   - PostgreSQL (kinetic, proof, mandates) → Confluent → Delta Lake / consumers.

2. Event bus for kinetic actions:
   - Every declared action (e.g., InitiatePayment) emits typed events.
   - Real-time consumers: rule engines, risk, audit, analytics.

3. Integration transport:
   - Vendor-hosted and internal systems feed events into the platform via curated topics.

Streaming does not:
- Replace REST for synchronous commands.
- Act as a random message queue.

## 2. Why Confluent?

- Strong fit for regulated environments:
  - BCBS-239-aligned patterns.
  - Audit-ready logs.
- Schema Registry:
  - Controlled schema evolution.
  - Breaking changes prevented by policy.
- Operational maturity:
  - Confluent Cloud (Dedicated) on Azure.
  - Native integrations with Neo4j, PostgreSQL (Debezium), Databricks.

Decision:
- Confluent Cloud (Dedicated), private link, VPC peered to Nexus Global.
- Fallback to self-managed on AKS only if bank IT mandates it.

## 3. Topic Taxonomy (Domain-Aligned)

- kinetic.action-events:
  - Each executed action type with mandateId, affectedEntityIds.
- kinetic.rule-evaluation-events:
  - Results of rule evaluations triggered by kinetic actions.
- kinetic.review-queue-events:
  - Items requiring human/agent review.

- cdc.neo4j.graph-changes:
  - Node/relationship changes (LegalEntity, ProductInstance, Account, etc.).
- cdc.postgres.kinetic:
  - Changes in kinetic.* tables.
- cdc.postgres.proof:
  - Append-only proof records.
- cdc.postgres.mandates:
  - Mandate lifecycle and delegation changes.

- domain.customer-events, domain.account-events, domain.transaction-events, domain.product-events:
  - High-level business events for LOBs and external partners.

- vendor.trade-finance-events, vendor.scf-events:
  - Vendor-hosted events into Containment Zone.

- governance.audit-events, governance.mandate-events, governance.access-events:
  - Canonical audit and access trails.

## 4. Semantic Guarantees

- Ordering:
  - Per-entity / per-transaction partitioning.
- Consistency:
  - Financial-critical streams use idempotent producers and consumers.
- Security:
  - TLS, mTLS, per-topic ACLs.
- Evolution:
  - All topics governed via Schema Registry.

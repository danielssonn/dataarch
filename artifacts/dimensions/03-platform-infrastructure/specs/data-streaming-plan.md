# Data Streaming Plan — Nexus Global Transaction Banking Platform

**Date:** 2026-05-26  
**Status:** Draft — for Daniel’s review  
**Author:** Data Architect Agent  
**Scope:** Integrate Confluent Kafka as a streaming backbone into the existing 5-dimension architecture.  
**Target:** Global Transaction Banking (GTB), 200 → 1,000+ corporates, vendor-hosted + bank-owned systems, regulated.

---

## 1. Executive Summary

We already have a sound three-tier architecture:

- Neo4j — canonical graph (operational traversal)
- PostgreSQL — kinetic layer + proof registry + mandates
- Delta Lake (Databricks on Azure) — analytics + history + projections
- Redis — hot cache
- Entity Platform API — sole write path, ontology action surface

Currently, cross-store sync is described as “CDC via APOC / logical replication → Databricks” and “write-through cache invalidation” but not as a unified, governable event backbone.

**This plan:** introduces Confluent (Kafka) not as “a thing to add” but as a dedicated infrastructure layer for exactly three responsibilities:

1. Event bus for kinetic actions and real-time consumers.
2. CDC backbone from Neo4j and PostgreSQL into analytics, audit, and downstream consumers.
3. Integration transport for vendor-hosted and internal systems into the canonical platform.

Streaming is **not** replacing batch, **not** replacing direct API calls, and **not** a general-purpose messaging system for every microservice.

It is the single source of truth for “something happened” inside this platform.

---

## 2. Strategic Rationale

### 2.1 What problems is streaming solving?

- **Consistent CDC across stores**
  - Problem: Today we plan to mirror Neo4j → Delta Lake and PostgreSQL → Delta Lake via ad hoc CDC. In a regulated environment, that’s not good enough. We need an auditable, replayable, standardized event stream that is:
    - Independently verifiable.
    - Reusable by multiple consumers (analytics, audit, real-time risk).
  - Solution: Confluent as the canonical CDC transport.

- **Real-time kinetic event propagation**
  - Problem: Kinetiс actions (InitiatePayment, ExecuteFXForward, etc.) require:
    - Immediate rule evaluation.
    - Immediate audit/proof events.
    - Real-time downstream consumers (e.g., fraud/risk, vendor systems).
  - Solution: Every declared action emits typed events to Kafka topics, consumed synchronously/asynchronously as needed.

- **Vendor-hosted system integration**
  - Problem: Trade Finance and Supply Chain Finance are vendor-hosted. Data must enter the ontology via the Containment Zone in a controlled, traceable way.
  - Solution: Streaming ingestion topics for vendor events → Containment Zone consumer → progressive mapping into canonical graph.

- **Event-sourced governance and audit**
  - Problem: The Proof Registry is append-only and event-sourced; every state change must have an immutable trail.
  - Solution: Kafka topics for governance/audit events feed:
    - Proof records (into PostgreSQL)
    - Audit tables (into Delta Lake)
    - Downstream compliance systems.

### 2.2 Why Confluent?

- **Regulatory fit:**
  - Mature in financial services (BCBS-239-aligned patterns, audit-ready logs).
  - Schema Registry → guarantees schema evolution control (critical in banking).
  - Role-based access, encryption at rest and in transit, private-link/VPC options on Azure.
- **Operational fit:**
  - Confluent on Azure can be:
    - Confluent Cloud (Dedicated) for strong isolation + lower ops overhead, or
    - Self-managed Kafka on Azure (AKS) for maximum control, if needed.
  - Seamless integration with:
    - Neo4j CDC + Kafka Connect (official).
    - PostgreSQL CDC via Debezium (standard in financial ecosystems).
    - Databricks (structured streaming / Kafka source) for lakehouse ingestion.

- **Decision:**
  - **Recommended:** Confluent Cloud (Dedicated) on Azure, private network, VPC peering to Nexus Global environment.
  - **Open Question:** Final choice between Dedicated vs self-managed depends on bank IT policy (data residency, air-gapping, ops team preferences).

### 2.3 Strategic role of streaming

Streaming is **all three**, but with clear boundaries:

- **Primary: CDC backbone**
  - Neo4j → Confluent → Delta Lake and audit consumers.
  - PostgreSQL (kinetic + proof + mandates) → Confluent → Delta Lake and downstream systems.
- **Primary: Event bus for kinetic actions**
  - Every action (e.g., InitiatePayment) produces:
    - Action events → real-time consumers (fraud, risk, vendor systems).
    - Audit events → Proof/Governance consumers.
- **Secondary: Transport backbone for integration**
  - Used for vendor-hosted and LOB-to-canonical data flows (event-driven ingest, not general SOAP/REST bus).
  - Entity Platform API remains the authoritative request/response interface; Kafka provides event-driven follow-ups and bulk streaming.

We are **not**:
- Replacing REST for synchronous command-and-control.
- Using Kafka as a random message queue for non-critical async tasks.

---

## 3. Recommended Confluent / Kafka Architecture

### 3.1 High-level topology (Mermaid)

```mermaid
flowchart LR

  subgraph "Sources"
    A[Entity Platform API]
    B[Neo4j]
    C[PostgreSQL]
    D[Vendor Systems]
    E[Microservices / Kinetiс Engine]
  end

  subgraph "Confluent / Kafka"
    F[Schema Registry]
    G[Topics: kinetic / cdc / vendor / governance]
  end

  subgraph "Sinks"
    H[Neo4j (via Kafka Connect)]
    I[Delta Lake / Databricks]
    J[Audit / Compliance]
    K[Fraud & Risk / AI]
    L[Vendor / LOB Systems]
  end

  A -->|Action/Command events| G
  B -->|CDC: graph changes| G
  C -->|CDC: kinetic/proof/mandates| G
  D -->|Vendor events| G
  E -->|Domain events| G

  G -->|Graph writes from events| H
  G -->|Streaming ingestion| I
  G -->|Immutable audit streams| J
  G -->|Real-time scoring| K
  G -->|Downstream notifications| L

  F -.->|Enforce schemas for all topics| G
```

Key principles:

- **All topics versioned** in Schema Registry (Avro/Protobuf).
- **Domain-aligned topics**, not technical.
- **Exactly-once semantics (EOS) or strong idempotency** where correctness is financial (e.g., payments, proof chains).

### 3.2 Topic taxonomy (conceptual, domain-specific)

Design by business domain and purpose, not by technology.

#### 3.2.1 Kinetic / Action events

Tied directly to the ontology action surface (Dimension 04) and kinetic layer (Dimension 02, §5).

- **kinetic.action-events**
  - For each executed action type: InitiatePayment, ExecuteFXForward, DrawdownIntercompanyFacility, InitiatePoolSweep, etc.
  - Includes:
    - actionInstanceId
    - actionType
    - initiator (human/agent/system)
    - mandateId
    - affectedEntityIds
    - domain scope
  - Consumers:
    - Rule engines / fraud / risk (real-time)
    - Proof record writer (PostgreSQL)
    - Delta Lake analytics (streaming)

- **kinetic.rule-evaluation-events**
  - For results of business_rules evaluation triggered by action events.
  - Used by:
    - Kinetiс engine for dynamic routing.
    - Governance and audit.

- **kinetic.review-queue-events**
  - For actions/events entering review_queue (proposed relationships, suspicious activity, edge promotions).
  - Enables real-time notification and routing without polling review_queue.

Interaction with existing flows:

- Each `POST /actions/{actionType}`:
  - Writes action instance to PostgreSQL (status: PENDING/COMPLETED/etc.).
  - Emits event to kinetic.action-events.
  - If rule evaluation is required → consumer publishes to kinetic.rule-evaluation-events.
  - If human review is required → event to kinetic.review-queue-events.
  - Review outcomes flow via kinetic.action-events (same topic, different actionType/eventType).

#### 3.2.2 CDC topics (from canonical stores)

Directly support: “Neo4j → Delta Lake”, “PostgreSQL → Delta Lake”, and cross-consumer uses.

- **cdc.neo4j.graph-changes**
  - Produced by Neo4j CDC (db.cdc.* procedures or official Neo4j Kafka Connector).
  - Captures:
    - Node create/update/delete (e.g., LegalEntity, ProductInstance, Account)
    - Relationship create/update/delete (e.g., IS_SUBSIDIARY_OF, SETTLES_AGAINST)
  - Uses:
    - Real-time updates to:
      - Containment Zone: detect changes relevant to vendor mapping.
      - Fraud/risk graph analytics consumers.
    - Delta Lake: streaming mirror to tb_canonical.entity for temporal analysis.
  - Semantics:
    - At-least-once with idempotent consumers.
    - Enrichment mode: DIFF for performance, FULL selectively for key entities (e.g., LegalEntity, Obligations).

- **cdc.postgres.kinetic**
  - Produced by Debezium on PostgreSQL logical replication.
  - Covers kinetic schema:
    - action_instances
    - business_rules
    - proposed_edges
    - review_queue
  - Uses:
    - Delta Lake: streaming into tb_canonical.kinetic.
    - Audit: continuous mirror into immutable tables.

- **cdc.postgres.proof**
  - Covers proof_chains, proof_records.
  - Uses:
    - Delta Lake: tb_canonical.proof summary tables.
    - Regulatory/Compliance: real-time audit event consumers.
  - Semantics:
    - At-least-once, idempotent.
    - Append-only → simpler dedup logic.

- **cdc.postgres.mandates**
  - Covers mandates and delegation changes.
  - Uses:
    - Real-time entitlement consumers (Redis refresh, agent validation backends).
    - Audit.
  - Latency:
    - Target: < 5s from mandate change to consumer visibility.

#### 3.2.3 Entity / Domain events

High-level, business-aligned events for consumption by LOB systems and external partners.

- **domain.customer-events**
  - Onboarding, KYC changes, status changes, entity group changes.
  - Used by LOB apps and external systems that need customer state awareness.

- **domain.account-events**
  - Account open/close, pool membership changes, sweep config changes.
  - Consumers: operational systems, reporting.

- **domain.transaction-events**
  - Payment initiated/completed/rejected.
  - FX hedge created.
  - Trade transaction executed.
  - Settlement obligations updated.
  - Used by:
    - Fraud/risk.
    - Real-time liquidity management.
    - Vendor systems (if allowed).

- **domain.product-events**
  - ProductDefinition/ProductInstance changes (e.g., new FX hedge product, cash pool bundle adjustment).
  - Used by:
    - Eligibility evaluators.
    - LOB systems.
    - Analytics.

These topics are:
- Published by the Entity Platform API / kinetic engine after graph + proof changes.
- Schema-validated, never ad-hoc.

#### 3.2.4 Vendor-hosted integration topics

Aligned with Dimension 01’s Containment Zone and vendor-hosted constraint `[VENDOR-HOSTED]`.

- **vendor.trade-finance-events**
  - Incoming events from TradeFinanceSystem (PROD-TF-001).
  - Contains: LC status updates, documentary evidence references, trade statuses.
  - Consumer:
    - Containment Zone processor: writes to tb_containment.vendor (Delta Lake), then maps to canonical entities.

- **vendor.scf-events**
  - From SupplyChainFinanceSystem (PROD-SCF-001).
  - Similar pattern.

- **vendor.control-plane-events**
  - For sync, mapping status updates, and containmentStatus changes.

Notes:

- All vendor topics:
  - Use Confluent Schema Registry.
  - Are one-way into canonical: vendor systems never write directly to Neo4j/Postgres; only via Containment Zone + Entity Platform API.

#### 3.2.5 Governance / Trust / Audit topics

Directly aligned with Dimension 05.

- **governance.audit-events**
  - Every significant action:
    - Relationship assertion
    - KYC renewal
    - Mandate change
    - Edge state transition
  - Written by:
    - Entity Platform API.
    - Kinetiс engine.
  - Consumed by:
    - Immutable audit tables in Delta Lake.
    - Any external compliance systems.

- **governance.mandate-events**
  - On creation, revocation, scope changes of mandates (HumanMandate, SystemMandate, AgentMandate).
  - Used by:
    - Agent pre-flight validators.
    - Entitlement services.
    - Audit.

- **governance.access-events**
  - Login and access events for sensitive operations.
  - Supports security monitoring and incident response.

### 3.3 How sources feed Confluent

- **Entity Platform API / Kinetiс engine:**
  - Direct producers (client libraries) to kinetic.* and domain.* and governance.* topics.
  - Idempotent producers enabled (for critical writes).

- **Neo4j → Confluent (CDC):**
  - Neo4j CDC (db.cdc.*) or Neo4j Kafka Connector reads the tx log.
  - Streams node/relationship changes into cdc.neo4j.graph-changes.

- **PostgreSQL → Confluent (CDC):**
  - Debezium connector on logical replication slots:
    - For kinetic.* → cdc.postgres.kinetic
    - For proof.* → cdc.postgres.proof
    - For mandates → cdc.postgres.mandates
  - Standard, widely used in financial services.

- **Vendor-hosted systems:**
  - Producers:
    - Vendor webhook → lightweight ingestion service → Confluent, or
    - File-based batch → stream-loader → Confluent (for high volume).
  - Only write to vendor.* topics; Containment Zone is the adapter.

### 3.4 How Confluent feeds downstream

- **Neo4j (streaming writes):**
  - Some events (e.g., vendor mappings, derived relationships, batch FX exposures) may:
    - Originate outside direct API calls.
    - Be written to Neo4j via Kafka Connect (neo4j-streams) from Confluent.
  - Still subject to:
    - Proof chain requirements via Entity Platform API for canonical writes.
    - Kafka Connect used mainly for:
      - Derived data.
      - Containment Zone → canonical promotion (after review).
  - Careful:
    - Never bypass API invariants via direct Kafka→Neo4j for core writes.

- **Delta Lake / Databricks:**
  - Structured Streaming jobs consume:
    - cdc.neo4j.graph-changes → tb_canonical.entity (append-only mirrors)
    - cdc.postgres.kinetic → tb_canonical.kinetic
    - cdc.postgres.proof → tb_canonical.proof summary
    - domain.transaction-events, kinetic.action-events → analytics, metrics, KPIs
    - governance.audit-events → audit tables
  - Uses:
    - Exactly-once semantics via Kafka offsets + Delta transactions where critical.
    - Liquid Clustering aligned to streaming append patterns.

- **Real-time consumers (kinetic engine, fraud, risk, AI/ML):**
  - Consume from:
    - kinetic.action-events
    - domain.transaction-events
    - governance.mandate-events
  - Implement:
    - Low-latency rule checks
    - ML scoring
    - Graph-based fraud checks that call Neo4j or Redis with enriched context.

- **Audit / Governance / Compliance:**
  - All governance.audit-events and governance.mandate-events are:
    - Immutable in Kafka (retention configured).
    - Mirrored into Delta Lake for long-term storage.
    - Optionally exported to external SIEM/GRC tools.

### 3.5 Semantic guarantees

- **Ordering:**
  - Per-entity and per-transaction: use partitioning keys (e.g., entityId, transactionId) so related events are ordered.
  - CDC topics: keyed by database identifier for ordered replay.

- **Exactly-once vs at-least-once:**
  - Financial-critical streams (transaction-events, kinetic.action-events):
    - Use idempotent producers + idempotent consumers.
    - Effectively exactly-once at business level, even if transport is at-least-once.
  - Analytics/audit:
    - At-least-once with idempotent sinks (Delta Lake handles duplicates via merge/append patterns).

---

## 4. Integration with Existing 5 Dimensions

### 4.1 Dimension 01 — Logical Model & Ontology

- **Changes/additions:**
  - Introduce “Event” as a first-class conceptual layer:
    - Each key ontology action (e.g., assert relationship, approve KYC, execute FX forward) is mapped not only to:
      - A graph mutation
    - But also:
      - A corresponding Kafka event (e.g., kinetic.action-events).
  - Vendor systems are represented as both:
    - `VendorSystem` nodes.
    - Producers to vendor.* topics.

- **Impact:**
  - The ontology must document:
    - Which actions generate which events.
    - Which events are “systemic” vs “internal.”

- **No generic patterns:**
  - This is tied to:
    - Our declared Action Types.
    - Our Containment Zone model.

### 4.2 Dimension 02 — Materialization Strategy

- **Cross-store sync:**
  - Existing “Neo4j → Delta Lake” and “PostgreSQL → Delta Lake” pipelines become:
    - Explicitly Kafka-based:
      - CDC topics → Databricks streaming jobs.
  - Latency:
    - Target <5s CDC end-to-end remains, now using well-known Kafka + Structured Streaming.

- **Kinetic layer:**
  - Kinetiс action_instances flow:
    - On execution:
      - Entity Platform API writes to PostgreSQL.
      - Debezium captures change.
      - Databricks consumes cdc.postgres.kinetic for analytics.
      - Kinetiс engine and downstream consumers (risk, audit, etc.) read kinetic.action-events directly.
  - Reduces direct coupling between kinetic engine and databases.

- **Redis cache invalidation:**
  - Option:
    - Redis consumers read:
      - cdc.neo4j.graph-changes
      - cdc.postgres.mandates
    - To invalidate or update hot caches based on actual changes rather than polling.
  - This is optional in early phases; can remain API-triggered initially.

### 4.3 Dimension 03 — Platform Infrastructure

- **New infrastructure components:**
  - Confluent deployment:
    - Confluent Cloud (Dedicated) on Azure or self-managed on AKS.
    - Integration via:
      - Private Link / VNet.
      - mTLS / OAuth between platform services and Confluent.
  - Kafka Connect:
    - Debezium connector for PostgreSQL.
    - Neo4j CDC / Kafka Connector for Neo4j.
  - Schema Registry:
    - Central schema management for all topics (Avro/Protobuf).

- **Networking:**
  - Streaming sits in the same private network as:
    - Neo4j, PostgreSQL, Databricks.
  - Ingress from vendor systems:
    - Limited via API Gateways → vendor ingestion endpoints → vendor.* topics.

- **Open Question:**
  - Data residency / cross-region if Nexus Global operates globally: need to confirm if single-region Confluent deployment is allowed, or if regional clusters are required.

### 4.4 Dimension 04 — API + Integration Contract

- **Entity Platform API:**
  - Becomes an event producer:
    - For each action:
      - Writes to Neo4j + PostgreSQL (via saga).
      - Emits events to Kafka.
  - This:
    - Preserves the “API is sole write path” principle.
    - Enhances it: API writes + streams the events.

- **External integrations:**
  - LOB and vendor consumers:
    - For command-and-control → use REST / Entity Platform API.
    - For event-driven consumption → subscribe to relevant Kafka topics via:
      - Confluent API or internal consumers.
      - Governed by topic-level access controls.

- **New contract aspects:**
  - Define:
    - Which topics are “external-facing.”
    - Required consumer reliability (e.g., idempotency).
    - Error handling:
      - Dead-letter topics (DLT) for failed vendor or LOB messages.
  - This is a non-trivial addition that must be documented in Dimension 04 spec.

### 4.5 Dimension 05 — Governance & Trust Layer

- **Audit:**
  - governance.audit-events becomes:
    - The canonical audit event stream.
    - All significant actions write here.
    - Delta Lake and external systems consume it.
  - This aligns with:
    - Append-only proof philosophy.
    - “State derived from event replay, never direct mutation.”

- **Mandates:**
  - governance.mandate-events:
    - Ensures real-time propagation of mandate changes.
    - Critical for:
      - Agent pre-flight validation:
        - Consumers can refresh local mandate caches faster than polling.
      - Enforcing “No agent action executes without valid mandate” invariant.

- **Security:**
  - Confluent:
    - TLS encryption for all in-flight data.
    - Role-based access per topic.
    - Audit logging of consumer/producer access.
  - Schemas:
    - Enforced in Schema Registry: prevents silent breaking changes in regulated environment.

---

## 5. Phased Implementation Plan

### Phase 0 — Decision & Reference Architecture (4–6 weeks)

- **Scope:**
  - Confirm Confluent deployment model (Dedicated vs self-managed).
  - Validate CDC feasibility:
    - Neo4j CDC integration.
    - PostgreSQL Debezium integration.
  - Define initial topic set:
    - Subset of kinetic.action-events, cdc.neo4j.graph-changes, cdc.postgres.proof, governance.audit-events.

- **Deliverables:**
  - Confluent deployment recommendation.
  - Initial topic design + schema samples (via Schema Registry).
  - Integration patterns for:
    - Entity Platform API as producer.
    - Neo4j/PostgreSQL as CDC sources.
    - Databricks as consumer.

- **Key risks:**
  - Bank IT policy resistance to managed Kafka or external Confluent.
  - If data residency constraints require self-managed: longer implementation timeline.

### Phase 1 — Foundational Streaming Backbone (8–12 weeks)

- **Scope:**
  - Deploy Confluent (sandbox → staging → prod).
  - Implement:
    - Neo4j CDC → Kafka.
    - PostgreSQL CDC (Debezium) → Kafka.
    - Entity Platform API → selected topics (kinetic.action-events, governance.audit-events).
  - Databricks streaming consumers:
    - Mirror CDC topics into tb_canonical entity/kinetic/proof.

- **Deliverables:**
  - Production Kafka cluster + Schema Registry.
  - CDC pipelines running.
  - Databricks structured streaming jobs consuming CDC.
  - Operational runbooks (monitoring, alerting, log analysis).

- **Key risks:**
  - Operational readiness: team may lack Kafka expertise → require training and clear runbooks.
  - Latency tuning: CDC must meet <5s SLA → capacity and connector tuning needed.

### Phase 2 — CDC + Analytics + Vendor Streaming (10–16 weeks)

- **Scope:**
  - Extend streaming to:
    - Vendor-hosted systems:
      - vendor.trade-finance-events
      - vendor.scf-events
    - Containment Zone:
      - Stream-based ingestion from vendors → tb_containment → mapping → canonical.
  - Use streaming for:
    - Real-time analytics:
      - transaction-events for KPIs.
      - kinetic.action-events for operational metrics.

- **Deliverables:**
  - Vendor event pipelines operational.
  - Containment Zone streaming integration.
  - End-to-end observability:
    - From vendor → Kafka → Containment → canonical.

- **Key risks:**
  - Vendor readiness:
    - Many vendors may not be streaming-capable → need adapters.
  - Schema evolution:
    - Vendor changes must be governed via Schema Registry to avoid breaking canonical consumers.

### Phase 3 — Advanced Streaming: Real-Time Kinetic, AI/ML (ongoing)

- **Scope:**
  - Real-time:
    - Fraud detection, risk scoring, anomaly detection consuming domain.transaction-events + kinetic.action-events.
  - AI/ML:
    - Graph-enhanced ML models (Neo4j + streaming context) via Databricks MLflow.
    - Event-driven triggers for automated reviews.

- **Deliverables:**
  - Real-time rule/ML scoring pipelines.
  - Tight integration between Kafka, Neo4j, and Databricks ML workflows.
  - Advanced observability and performance tuning.

- **Key risks:**
  - Overengineering:
    - Keep real-time consumers focused on actual business needs, not hypothetical use cases.
  - Latency:
    - ML scoring must not become a bottleneck for kinetic execution.

---

## 6. Key Risks + Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Overuse of Kafka** — “Kafka for everything” culture | Unnecessary complexity; performance impact | Clearly separate: REST for commands, Kafka for events/CDC; maintain API as sole write path |
| **Regulatory / Data residency concerns** | Deployment blocked or delayed | Plan for both Confluent Cloud Dedicated and self-managed; align early with Security/GRC |
| **Operational complexity (Kafka expertise gap)** | SLA breaches; downtime | Invest in runbooks, monitoring, training; leverage Confluent Control Center / Cloud UI |
| **Schema chaos / breaking changes** | Downstream failures, audit risk | Enforce Schema Registry; require approval for schema changes |
| **Latency degradation in CDC pipelines** | Analytics/audit stale | Use dedicated CDC clusters/connectors; monitor offsets lag; capacity plan early |
| **Inconsistent event semantics** | Confusion across LOBs | Document each topic’s contract (events, keys, ordering, idempotency); tie to ontology |
| **Dual-write problems (API writes + Kafka writes)** | Inconsistency between graph/DB and events | API is authoritative: all events emitted after canonical writes or as part of saga; Kafka never is source of truth |

---

## 7. Open Questions

- **Confluent deployment model:**
  - Final decision: Dedicated vs self-managed (depends on IT policy and security review).

- **Data residency / multi-region:**
  - If Nexus Global requires per-region clusters, topology needs extension.

- **Access model for LOB systems:**
  - Who can consume which topics? Must be defined in Dimension 04 as part of integration contracts.

- **Interaction with ZKP layer:**
  - Should zero-knowledge proofs generate their own governance events in Kafka? Currently: yes, as “systemic” events tied to the respective ZKP verification (future phase).

- **Initial vendor readiness:**
  - Confirm if TradeFinanceSystem / SupplyChainFinanceSystem can produce streaming events, or if batch + webhook + ingestion service is more realistic.

---

End of document.

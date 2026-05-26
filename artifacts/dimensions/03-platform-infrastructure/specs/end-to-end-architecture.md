# End-to-End Architecture — Nexus Global Transaction Banking Platform

**Date:** 2026-05-26  
**Status:** Draft — for Daniel’s review  
**Author:** Data Architect Agent  
**Scope:** Single end-to-end architecture view integrating:
- Canonical graph (Neo4j)
- Kinetic + governance stores (PostgreSQL)
- Lakehouse analytics (Delta Lake on Databricks)
- Hot cache (Redis)
- Streaming backbone (Confluent/Kafka)
- Stream computation (Apache Flink)

This document merges streaming, stream computation, and the 5 architecture dimensions into one coherent design for Nexus Global (Maya’s world) — no generic messaging fluff.

---

## 1. Executive Summary

We are architecting a **regulated, ontology-driven, real-time capable GTB platform** for Nexus Global. 

Core design:

- **Canonical Graph (Neo4j):**
  - Single source of truth for:
    - Parties, products, accounts, transactions, channels, obligations, mandates, vendors.
  - All operational traversal, ownership, relationship, and entitlement queries.

- **Kinetic + Governance Store (PostgreSQL):**
  - Kinetic layer:
    - action_types, action_instances, business_rules, function_definitions,
      proposed_edges, review_queue, compensating_actions.
  - Governance:
    - Proof registry (append-only, SHA-256 chaining),
    - Mandate hierarchy (HumanMandate → SystemMandate → AgentMandate),
    - Agentic execution audit.

- **Lakehouse (Delta Lake on Databricks):**
  - Analytics, temporal history, regulatory reporting.
  - CDC-synced views of Neo4j, PostgreSQL, and streaming events.
  - LOB projections: tb_cb, tb_cm, tb_wm.
  - Containment Zone analytics: tb_containment.

- **Hot Cache (Redis):**
  - Latency-critical paths: entitlements, mandates, hot node/edge lookups.
  - Event-driven invalidation via streams (Confluent).

- **Streaming Backbone (Confluent/Kafka):**
  - Not “dumb pipes.” Not a random event bus.
  - Roles:
    - CDC backbone (Neo4j + PostgreSQL → multiple consumers).
    - Kinetic + domain event transport (action, transaction, vendor, governance).
    - Integration bus between platform and external/internal systems.

- **Stream Computation (Apache Flink on Kubernetes):**
  - Stateful, real-time analytics and complex event processing on top of Confluent.
  - Purpose (Nexus Global use cases):
    - Real-time reporting and regulatory-ready event streams.
    - Real-time statement assembly from payments and ledger data.
    - Cash flow forecasting (T+0/T+1/T+7/T+30) for Treasury.
    - Liquidity monitoring and automated kinetic actions.
    - Kinetic incident correlation, vendor risk, and rule enforcement.

Key philosophy:

- Streaming and Flink:
  - Enhance the ontology.
  - Activate the kinetic layer.
  - Provide real-time correlation and decisions.
- Everything is:
  - Governed.
  - Schema-locked.
  - Auditable.
  - Non-magical.

---

## 2. Guiding Principles (Nexus Global)

- **Ontology-first, everywhere:**
  - Every event, stream, Flink job, and API endpoint ties back to the canonical model:
    - Entities, relationships, products, obligations, mandates.
- **Kinetic reality:**
  - The system doesn’t just store state;
    it emits actions, triggers rules, queues reviews, and enforces compensations.
- **Real-time, not batch-only:**
  - For Nexus Global’s scale:
    - Risk, fraud, vendor anomalies, liquidity checks cannot wait for nightly jobs.
- **Governance as default:**
  - Every decision:
    - Is traceable.
    - Is linked to a mandate.
    - Is recorded in an immutable, replayable way.
- **Separation of concerns:**
  - Sync commands: Entity Platform API.
  - Async events: Confluent.
  - Real-time analytics/CEP: Flink.

---

## 3. Overall System Architecture (End-to-End)

High-level architecture diagram:

```mermaid
flowchart LR

  subgraph Sources
    A[Entity Platform API]
    B[Neo4j Canonical Graph]
    C[PostgreSQL Kinetic / Proof / Mandates]
    D[Vendor Systems (TF / SCF)]
    E[Internal Banking / Core Systems]
    F[ML / AI Services]
  end

  subgraph Confluent
    G[Schema Registry]
    H[Streaming Topics
        (domain, kinetic, cdc, vendor, governance)]
  end

  subgraph Flink
    J[Flink: Kinetic Incident Correlation]
    K[Flink: Vendor Risk + Containment]
    L[Flink: Real-Time Rule Enforcement]
    M[Flink: Reporting + Statements]
    N[Flink: Cash Flow Forecasting]
    O[Flink: Liquidity Monitoring]
  end

  subgraph Core
    M[Neo4j (Operational Graph)]
    N[PostgreSQL (Kinetic + Proof + Mandates)]
    O[Databricks / Delta Lake (Analytics + History)]
    P[Redis (Hot Cache)]
  end

  subgraph Consumers
    Q[Fraud / Risk / Compliance]
    R[Vendor / LOB / Ops]
    S[Agentic Decisioning]
  end

  A -->|Action / Domain Events| H
  B -->|Graph CDC| H
  C -->|CDC (Kinetic / Proof / Mandates)| H
  D -->|Vendor Ingestion Events| H
  E -->|Core Banking Events| H

  H -->|Graph writes (limited, curated)| M
  H -->|Streaming sink (Delta Lake)| O
  H -->|Governance / audit sinks| Q

  J -->|review_queue events, compensating_actions| H
  K -->|containment alerts + mapping events| H
  L -->|action/rule triggers + alerts| H
  M -->|reporting-ready and statement-ready streams| H
  N -->|cash flow forecast events| H
  O -->|liquidity alerts and kinetic actions| H

  H -->|Event-driven invalidation| P

  J -.->|Uses business_rules + function_definitions| N
  K -.->|Uses containment_zone + vendor mappings| O
  L -.->|Uses mandates + obligations| N

  G -.->|Schema enforcement| H
```

End-to-end flow (simplified):

- External/Internal systems and the Entity Platform API produce events into Confluent.
- Neo4j and PostgreSQL change events are CDC-captured into Confluent.
- Flink jobs:
  - Read from those events.
  - Perform real-time correlation, anomaly detection, kinetic rule evaluation.
  - Emit decisions back as events to:
    - Kinetic topics
    - Governance topics
    - Containment topics
- Downstream:
  - Neo4j updated selectively (graph writes from events).
  - PostgreSQL updated (review_queue, action_instances, mandates).
  - Delta Lake consumes streams (analytics, history).
  - Redis invalidated/refreshed from events.
  - Fraud, Risk, Compliance, Agentic services consume curated streams.

---

## 4. Logical Model + Streaming + Flink Integration

Reference: Dimension 01 (Logical Model).

The logical model defines:
- Entity types (Party, Product, Account, Transaction, Obligation, Mandate, VendorSystem, etc.)
- Relationship types and constraints (ownership, authority, product subscriptions, settlement, vendor mapping).

Streaming and Flink now become the runtime mechanism for:

- Observing changes in this model.
- Enforcing rules that span it in real time.

Key aspects:

- **CDC topics reflect the ontology:**
  - cdc.neo4j.graph-changes:
    - Nodes/edges: LegalEntity, Account, ProductInstance, Obligation.
    - Relationships: IS_SUBSIDIARY_OF, HAS_BALANCE, SETTLES_AGAINST, OPERATES_UNDER, IS_HOSTED_BY, etc.
  - Confluent provides:
    - Replayable source of truth for all structural changes.

- **Domain events mapped to ontology constructs:**
  - domain.transaction-events:
    - Tied to Transaction nodes and edges (initiatedBy, settlesAgainst).
  - domain.account-events:
    - Tied to Account and Pool constructs.
  - domain.customer-events:
    - Tied to Party and EntityGroup constructs.

- **Flink’s role on the logical model:**
  - Perform cross-entity correlation:
    - Example: suspicious behavior across related accounts of the same LegalEntity.
  - Evaluate patterns in relationships:
    - Example: rapid structural changes (new vendor mappings, new entities) around high-value transactions.

This ensures:
- The ontology is not just for design-time modeling.
- It becomes the vocabulary for real-time stream processing.

---

## 5. Kinetic Layer + Real-Time Decisioning

Reference: Dimension 02 (Materialization Strategy), kinetic layer tables.

Today:
- Kinetic is:
  - action_types, action_instances, business_rules, function_definitions,
    proposed_edges, review_queue, compensating_actions.
- Actions:
  - InitiatePayment, ExecuteFXForward, DrawdownIntercompanyFacility,
    InitiatePoolSweep, etc.

Now with streaming + Flink:
- The kinetic layer becomes the brain of real-time decisions.

### 5.1 Kinetic event flow (streaming)

- Entity Platform API:
  - POST /actions/{actionType}:
    - Writes action_instances (PostgreSQL).
    - Emits kinetic.action-events (Confluent).

- Flink consumers:
  - Read kinetic.action-events.
  - Correlate with:
    - domain.transaction-events
    - domain.customer-events
    - vendor trade finance events
  - Evaluate business_rules:
    - Using function_definitions as reference.

- Flink outputs:
  - kinetic.review-queue-events:
    - Add items to review_queue for humans/agents.
  - kinetic.action-events:
    - Trigger compensating_actions (e.g., freeze limit, halt processing).
  - governance.audit-events:
    - All decisions logged with rule IDs and input sets.

This turns the kinetic layer into:
- A real-time decision engine:
  - Actions are not just recorded.
  - They are observed, correlated, and acted upon in (near) real time.

### 5.2 Primary use case: Real-time Kinetic Incident Correlation (Maya’s world)

This is the core justification for Flink.

Purpose:
- Detect complex, high-risk patterns across:
  - Transactions
  - Accounts
  - Products
  - Vendors
  - Kinetic actions
- Proactively trigger:
  - Review queue
  - Compensations
  - Governance alerts

Example patterns:

- Rapid cross-account fund movement:
  - Many small outflows from multiple accounts linked to a single entity, followed by a large incoming trade finance payment.
  - Flink:
    - Maintains per-entity state.
    - Uses sliding windows.
    - Evaluates:
      - Frequency, value, counterparties.
      - Graph relationships (IS_SUBSIDIARY_OF, OWNS).
  - If a match:
    - Writes to review_queue.
    - Optionally emits compensating_actions (e.g., block further payments until review).

- Vendor-hosted anomalies:
  - Trade Finance / SCF vendor events show:
    - Unexpected counterparties.
    - Unusual document/payment flows.
  - Flink:
    - Joins vendor.* events with domain events and graph-derived risk flags.
  - Output:
    - Containment zone alerts.
    - Review queue entries.
    - Governance events.

This is not “generic fraud.” It is:
- Concrete correlation, driven by:
  - The ontology.
  - The kinetic layer.
  - The containment zone.

---

## 6. Containment Zone + Vendor Streaming

Reference: Dimension 02, § Containment Zone; Dimension 01, [VENDOR-HOSTED] constraint.

Vendor-hosted products:
- Trade Finance
- Supply Chain Finance

They:
- Don’t share canonical schemas.
- Are not fully trustworthy.
- Need gradual mapping.

Streaming + Flink integration:

- Confluent topics:
  - vendor.trade-finance-events
  - vendor.scf-events

- Ingestion:
  - Vendors publish or push events → Confluent.
  - Containment Zone consumer:
    - Writes to containment_zone_raw (tb_containment catalog).
    - Uses vendor_mapping_status to track progress.

- Flink: Vendor Risk + Containment Use Case:
  - Inputs:
    - vendor.* topics
    - domain.transaction-events
    - domain.customer-events
  - Logic:
    - Maintain per-vendor and per-customer states.
    - Detect:
      - Anomalous volumes
      - Counterparty concentration
      - Schema drift
      - Unusual timing
  - Outputs:
    - kinetic.review-queue-events
    - governance.alert-events
    - Containment zone mapping updates

This makes Containment Zone:
- Not just a static data lake.
- A streaming-aware sandbox with real-time monitoring.

---

## 7. Platform Infrastructure (Compute, Storage, Streaming, Flink)

Reference: Dimension 03.

### 7.1 Core stores

- Neo4j:
  - Canonical graph.
  - Served via Entity Platform API.
  - CDC to Confluent for replayability and analytics.

- PostgreSQL:
  - Kinetic tables.
  - Proof registry.
  - Mandate hierarchy.
  - CDC to Confluent; read by Flink and analytics.

- Delta Lake on Databricks:
  - Analytics:
    - tb_canonical.* (entity, product, account, transaction, etc.)
    - tb_containment.* (vendor data, mapping).
    - LOB projections (tb_cb, tb_cm, tb_wm).
  - Streaming:
    - Direct ingestion from Confluent via Structured Streaming.

- Redis:
  - Hot caches for:
    - Entitlements.
    - Active mandates.
    - High-frequency lookups.
  - Invalidation via event consumers watching:
    - cdc.neo4j.graph-changes
    - cdc.postgres.*
    - kinetic.* events.

### 7.2 Confluent (Streaming backbone)

Decision: Confluent Cloud (Dedicated) on Azure, private link, VPC peered to Nexus Global.
- Open Question only if bank IT mandates self-managed on AKS (override default).

Key components:

- Schema Registry:
  - Mandatory for all topics.
  - Enforces backward-compatible schema evolution.

- Connect:
  - Sources:
    - Neo4j CDC
    - PostgreSQL CDC (Debezium)
  - Sinks:
    - Neo4j (limited, curated writes)
    - Delta Lake / Databricks (streaming ingestion)
    - Audit systems (if needed)

- Security:
  - mTLS between services.
  - Per-topic ACLs.
  - Service accounts (no anonymous access).
  - Encryption at rest and in transit.

### 7.3 Apache Flink (Stream computation layer)

Rationale:
- We do not want “dumb pipes.”
- Flink enables:
  - Stateful joins (events + graph + reference data).
  - Complex event processing (CEP) across kinetic + vendor + transactions.
  - Windowed aggregations for real-time risk and limits.
  - Exactly-once semantics for critical decisions.

Decision: Flink on Kubernetes (AKS), integrated with Confluent and Databricks.
- Runtime:
  - State backend: RocksDB.
  - Checkpointing: every 30–60 seconds to Azure Blob Storage.
  - Exactly-once semantics for critical decision jobs.

Flink jobs (primary):

- Kinetic Incident Correlation:
  - Real-time correlation of actions, transactions, relationships, vendors.
  - Output → review_queue, compensating_actions, governance events.

- Vendor Risk & Containment:
  - Real-time anomaly detection on vendor-hosted events.
  - Output → containment_zone updates, review_queue.

- Real-Time Rule Enforcement:
  - Uses business_rules + function_definitions (from PostgreSQL/Delta Lake reference data) to:
    - Validate actions on the fly.
    - Emit alerts if rules are violated.

- Reporting and Statements (payments + ledger):
  - Purpose: produce reporting-ready and statement-ready streams for Nexus Global.
  - Inputs:
    - domain.payment-events
    - domain.account-events
    - cdc.neo4j.graph-changes (entity/account updates)
    - cdc.postgres.kinetic (action_instances, compensating_actions)
  - Logic:
    - Per-customer, per-account stateful aggregation.
    - Classify events into: payment events, ledger postings, reversals, fees.
    - Ensure consistent ordering and idempotency.
  - Outputs:
    - Reporting topics → Delta Lake (tb_canonical.reporting) for regulatory and executive reports.
    - Statement topics → consumed by statement generation services; also Delta Lake for historical statements.

- Cash Flow Forecasting (Treasury + TBP):
  - Purpose: near-real-time projected cash flows based on payments, trades, vendor flows.
  - Inputs:
    - domain.payment-events
    - domain.transaction-events (sweeps, pools)
    - vendor.trade-finance-events, vendor.scf-events
  - Logic:
    - Maintain per-entity, per-product projected cash flows in stateful windows.
    - Use rules for horizon buckets (T+0, T+1, T+7, T+30).
  - Outputs:
    - Forecast streams → Delta Lake (tb_canonical.forecasting).
    - Governance/kinetic alerts when forecasts breach configured thresholds.

- Liquidity Monitoring (real-time):
  - Purpose: continuously track liquidity positions and react to stress.
  - Inputs:
    - domain.account-events
    - domain.transaction-events
    - kinetic.action-events (facility usage, pool sweeps)
  - Logic:
    - Per-entity / per-pool / per-currency running positions.
    - Detect breaches and concentration anomalies in rolling windows.
  - Outputs:
    - governance.alert-events for risk/treasury.
    - kinetic.action-events to trigger compensating_actions (e.g., initiate pool sweep, adjust limits).

Reliability:

- Exactly-once for critical decision jobs.
- Checkpointing:
  - Every 30–60 seconds to Azure Blob Storage.
- State:
  - RocksDB-backed; persisted, recoverable.

This is integral, not optional.

---

## 8. API & Integration Contract (Sync + Async)

Reference: Dimension 04 (API Integration Contract).

Core principle:

- Synchronous operations:
  - Entity Platform API:
    - Sole write path for canonical state.
    - Ontology action surface:
      - POST /actions/{actionType}, GET /entities, etc.
- Asynchronous operations:
  - Confluent events:
    - Observe and react to what happened.
    - Support streaming consumers, Flink, analytics, audit.

Streaming does not replace:
- The Entity Platform API.
- Direct REST/gRPC for simple, synchronous calls.

New patterns:

- Action execution flow:
  - API:
    - Validates, checks mandates, writes action_instances.
  - Confluent:
    - kinetic.action-events emitted.
  - Flink:
    - Observes action events, correlates with other streams.
    - Outputs review_queue / compensating_actions / governance events as needed.

- External consumers:
  - Primary: REST/gRPC via Entity Platform API.
  - Secondary: Kafka consumer access for:
    - Internal partners (fraud, risk, ops).
    - Tightly governed; no arbitrary access.

---

## 9. Governance, Trust, and Mandates

Reference: Dimension 05 (Governance + Trust Layer).

Streaming + Flink must be fully governed.

- Mandate hierarchy:
  - HumanMandate → SystemMandate → AgentMandate.
  - Each decision (kinetic action, Flink-triggered review, compensation):
    - Must be bound to a mandate.
    - Must include a mandateId in the event payload.

- Proof registry:
  - Flink decisions:
    - Are logged as governance.audit-events.
    - Batched and linked via SHA-256 hash chains into proof_records.
  - Enables:
    - “Here is exactly what the system saw.”
    - “Here is exactly what it decided, when, and under what rules.”

- ZKP hooks:
  - Where needed (e.g., sensitive risk scores):
    - ZKP can be used to prove compliance:
      - “The system evaluated rule X” without leaking details.

- Security:
  - Access to streams:
    - Controlled via ACLs and domain_scope.
  - Sensitive data:
    - Masked at the source (API), and:
    - In streaming (e.g., PII columns masked in domain events).

Streaming + Flink are:
- Not separate from governance.
- Deeply embedded into it.

---

## 10. Data Quality, Observability, and Security

Data quality:

- Schema Registry:
  - All critical topics require schemas.
  - Breaking changes = no.
  - Evolution = strictly governed.

- Flink jobs:
  - Versioned logic.
  - Explicit configuration.
  - No opaque behavior.

Observability:

- For Confluent:
  - Topic-level metrics (lag, throughput, errors).
  - Per-consumer lag tracking.

- For Flink:
  - Job-level metrics (throughput, state size, latencies).
  - Alerts for checkpoint failures and backpressure.

Security:

- Confluent:
  - mTLS, private endpoints, per-service credentials.
- Flink:
  - Running in its own secured cluster.
  - Strict environment variables and secrets management.
  - No direct public internet access.

---

## 11. Phased Implementation (Concise)

Phase 0: Decision + Reference Architecture

- Scope:
  - Confirm and align stakeholders on:
    - Confluent as streaming backbone.
    - Flink as primary stream computation engine.
- Deliverables:
  - Approved end-to-end architecture (this doc).
  - Topic taxonomy finalized.
  - Schemas for kinetic.action-events, domain.transaction-events, governance.audit-events.
- Key risks:
  - Cross-team schema ownership: must be decided early.

Phase 1: Foundational backbone + CDC + first Flink jobs

- Scope:
  - Deploy:
    - Confluent Cloud (Dedicated)
    - Flink on Kubernetes (AKS)
  - Enable CDC:
    - PostgreSQL → Confluent
    - Neo4j → Confluent
  - Flink:
    - Kinetic Incident Correlation (limited pattern set)
    - Initial Reporting + Statements pipeline
- Deliverables:
  - Production-grade streaming and Flink runtime.
  - Confluent → Delta Lake streaming pipelines.
  - First real-time review_queue feeds from Flink.
  - First reporting-ready and statement-ready event streams.
- Key risks:
  - Operational complexity: strong runbooks and observability required.

Phase 2: Vendor streaming + Containment + advanced Flink

- Scope:
  - Vendor streaming (Trade Finance, SCF) into Confluent.
  - Flink:
    - Vendor Risk + Containment job
    - Cash Flow Forecasting job
    - Liquidity Monitoring job
  - Integration:
    - Deeper Neo4j + Flink correlation.
- Deliverables:
  - Streaming vendor ingestion.
  - Real-time anomaly detection.
  - Near-real-time cash flow and liquidity views for Treasury/TBP.
- Key risks:
  - Vendor alignment on schemas; latency spikes; data quality.

Phase 3: Advanced real-time kinetic + AI/ML

- Scope:
  - Real-time ML model inference fed by Flink (risk/fraud scoring).
  - Advanced patterns:
    - Liquidity / concentration monitoring.
    - Cross-product orchestration.
- Deliverables:
  - Live real-time risk/fraud consumers.
  - Agentic decision logs fully integrated.
- Key risks:
  - Avoid over-engineering; keep models interpretable and governed.

---

## 12. Open Questions (Explicit)

These must be resolved with Daniel (and Maya’s stakeholders) before finalizing:

- Confluent deployment:
  - Decision: Confluent Cloud (Dedicated). Self-managed only if mandated.

- Flink runtime:
  - Decision: Flink on Kubernetes (AKS).

- Vendor integration:
  - Confirm that streaming is the primary transport for Trade Finance / SCF events from vendors into Containment Zone?

- AI/ML:
  - Confirmed: reporting, statements, cash flow forecasting, and liquidity are prioritized.

- Governance:
  - How should Flink rules be versioned and tied to HumanMandate / SystemMandate?
  - Any restrictions on automated compensating actions (hard limits vs soft recommendations)?

End.

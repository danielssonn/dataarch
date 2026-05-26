# 02 — Materialization Strategy

**Project:** Nexus Global Transaction Banking Platform  
**Type:** Physical store architecture, sync, projections  
**Status:** Draft for Daniel's review

## 1. Guiding Rule

Materialization is always derived from the graph. The graph is never derived from materialization.

We use four complementary stores, each optimized for its access pattern.

## 2. Store Roles

- **Neo4j (Graph Store):**
  - Current canonical graph (nodes, edges, traversals).
  - Real-time multi-hop queries: ownership chains, beneficial owners, entitlement resolution, regulatory exposure.
  - Served via Entity Platform API.
  - CDC to Confluent → Delta Lake for history.

- **PostgreSQL (RDBMS):**
  - Kinetic layer:
    - Interfaces, interface_implementations.
    - action_types, action_instances.
    - function_definitions, business_rules.
    - proposed_edges, review_queue, compensating_actions.
  - Proof Registry:
    - proof_chains, proof_records (append-only, SHA-256 chained).
  - Mandates:
    - mandate.mandates (HumanMandate → SystemMandate → AgentMandate).
  - ACID, constraints, RLS, efficient ordered access.

- **Delta Lake / Databricks (Lakehouse):**
  - Analytics and temporal history:
    - tb_canonical: CDC-synced mirrors of Neo4j and PostgreSQL (entity, product, account, transaction, channel, proof summaries, metrics).
    - LOB projections: tb_cb, tb_cm, tb_wm (read-only).
    - Containment: tb_containment (vendor data, mapping).
  - Uses:
    - KPI computation, regulatory reporting, ML, batch jobs.
    - Point-in-time reconstruction via Delta time-travel.

- **Redis (Hot Cache):**
  - Caches:
    - Entitlements, active mandates.
    - Interface implementations.
    - Hot node lookups (by LEI).
  - Invalidated via Confluent event streams.
  - Optimization only; never source of truth.

## 3. Cross-Store Sync

- **Neo4j → Delta Lake:**
  - CDC (via Confluent/Kafka).
  - Near-real-time append to historical tables.

- **PostgreSQL → Delta Lake:**
  - CDC (Debezium via Confluent).
  - Kinetic, proof, mandate state mirrored.

- **Confluent → Redis:**
  - Event-driven invalidation.
  - Mandates, entitlements, hot nodes refreshed from cdc and kinetic events.

## 4. Unity Catalog Topology

- tb_canonical (Channels Technology):
  - entity, product, account, transaction, channel, proof (summaries), metrics.
- tb_cb, tb_cm, tb_wm:
  - Read-only LOB views.
- tb_containment:
  - Vendor zone (separate governance).

## 5. Data Volume (Nexus Global, high level)

- Neo4j:
  - ~28K nodes (Y1, 200 customers), ~62K edges.
- PostgreSQL:
  - Kinetic + proof + mandates (order-of-magnitude small).
- Delta Lake:
  - Mirrors + analytics: < 2 GB even by Y5.

At this scale, latency and consistency matter more than raw volume.

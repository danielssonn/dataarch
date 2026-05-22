# Dimension 02 — Materialization Strategy

**Status:** ✅ Rewritten 2026-05-22 — correct three-tier architecture
**File:** `artifacts/dimensions/02-materialization-strategy/specs/materialization-strategy.md` (~52KB, ~1400 lines)

## Store Architecture (Resolved)
- **Neo4j** — Graph store for operational entity-relationship traversal, ownership chains, beneficial ownership queries (<5ms p99). All node types + edge types from ontology spec. Cypher queries aligned with API contract (Dimension 04) traversal endpoints.
- **PostgreSQL** — Kinetic layer (9 tables: interfaces, interface_implementations, action_types, action_instances, function_definitions, business_rules, proposed_edges, review_queue, compensating_actions) + Proof registry (2 tables: proof_chains, proof_records with append-only trigger + SHA-256 hash chaining) + Mandate state (1 table: mandates with three-tier delegation hierarchy). ACID transactions for two-phase write state machine.
- **Delta Lake (Databricks on Azure)** — Analytics + temporal history. CDC-synced mirrors of Neo4j (entity/product/account/transaction/channel nodes+edges) and PostgreSQL (kinetic.action_instances). Containment zone (3 tables in separate `tb_containment` catalog). LOB projections (`tb_cb`/`tb_cm`/`tb_wm`). Metrics/KPIs.
- **Azure Cache for Redis** — Hot operational paths: entitlements, active mandates, interface implementations, hot node lookups. Write-through invalidation. Never source of truth.

## Cross-Store Synchronization
| Sync Path | Mechanism | Latency |
|-----------|-----------|---------|
| Neo4j → Delta Lake | CDC via Neo4j APOC trigger → Event Grid → Databricks Job | <5s |
| PostgreSQL → Delta Lake | CDC via PostgreSQL logical replication → Databricks | <5s |
| PostgreSQL → Redis | Write-through cache invalidation via pub/sub | <1ms |
| Neo4j → Redis | Write-through cache invalidation | <1ms |

## Table Design
### Neo4j (Graph Store)
- **Labels:** All node types from ontology spec (Party, EntityGroup, Product, Account, Transaction, Channel, Obligation, Mandate, VendorSystem)
- **Relationships:** IS_SUBSIDIARY_OF, OWNS, IS_SUBSCRIBED_TO, IS_PART_OF, HAS_BALANCE, SETTLES_AGAINST, IS_KNOWN_BY, IS_SCREENED_AGAINST, IS_SUBJECT_TO, OPERATES_UNDER, DELEGATED_FROM, IS_HOSTED_BY, HAS_SIGNING_AUTHORITY
- **Indexes:** Primary lookups by id, lei, productCode. Relationship traversal indexes.
- **Key queries:** Ownership chain, beneficial owners, regulatory exposure, interface resolution — all aligned with Dimension 04 API contract

### PostgreSQL (Kinetic + Proof + Mandate)
- **kinetic schema (9 tables):** interfaces, interface_implementations, action_types, action_instances, function_definitions, business_rules, proposed_edges, review_queue, compensating_actions
- **proof schema (2 tables):** proof_chains, proof_records (append-only via trigger, SHA-256 hash chaining, column masking via masked view)
- **mandate schema (1 table):** mandates (three-tier hierarchy: HumanMandate → SystemMandate → AgentMandate, delegation chain validation)

### Delta Lake (Analytics + History)
- **tb_canonical.entity** — CDC mirror of Neo4j nodes/edges (append-only, Liquid Clustering)
- **tb_canonical.kinetic** — CDC mirror of PostgreSQL kinetic tables
- **tb_canonical.metrics** — KPIs, metric definitions
- **tb_containment.vendor** — vendor_systems, containment_zone_raw, vendor_mapping_status (separate catalog, separate governance)
- **tb_cb / tb_cm / tb_wm** — LOB projection catalogs

## Pipeline Architecture
### Cross-Store Sync (4 pipelines)
- Graph History Sync (Neo4j → Delta Lake, CDC)
- Kinetic Mirror Sync (PostgreSQL → Delta Lake, CDC)
- Cache Invalidation (PostgreSQL → Redis, write-through)
- Cache Invalidation (Neo4j → Redis, write-through)

### Analytical (4 pipelines, unchanged)
- Proof Integrity Sweep (15min), KPI Computation (hourly), CB Projection Refresh (CDF), Entitlement Snapshot (CDF)

### Kinetic Layer (4 pipelines)
- Action Execution Pipeline (Phases 1-3: pre-flight → execute → governance routing; cross-store: Neo4j + PostgreSQL)
- Function Evaluation Pipeline (CDC-triggered, dependency-ordered)
- Proposed → Active Promotion Pipeline (synchronous API + Redis invalidation; cross-store: PostgreSQL + Neo4j)
- Vendor Data Ingestion Pipeline (event-triggered: ingest → parse → map → integrate; Delta Lake + Neo4j + PostgreSQL)

## Nexus Global Volume Estimates
| Store | Y1 (200 customers) | Y5 (1,000 customers) |
|-------|-------------------|---------------------|
| Neo4j (nodes + edges) | ~500 MB | ~2.5 GB |
| PostgreSQL (proof) | ~500 MB | ~5 GB |
| PostgreSQL (kinetic) | ~10 MB/mo | ~50 MB/mo |
| PostgreSQL (mandates) | ~1 MB | ~5 MB |
| Delta Lake (total) | ~410 MB | ~1.25 GB |
| Redis (hot cache) | ~10 MB | ~50 MB |

## New Critical Risks (Three-Tier Architecture)
- 🔴 **Cross-store transaction consistency** — Action execution writes to both Neo4j (graph mutation) and PostgreSQL (proof record + action instance). Need compensating transaction pattern or distributed transaction coordinator.
- 🔴 **Vendor API contract review** — TF-API-v2.1 and SCF-API-v1.4 schemas unknown; blocks vendor integration
- 🟠 **CDC sync latency** — Neo4j → Delta Lake must be <5s; needs benchmarking
- 🟠 **Neo4j operational readiness** — Team needs Cypher/graph DB expertise; training plan required
- 🟠 **Initial seeding strategy** — Legacy relationships lack digital evidence
- 🟡 Hash chain computation at batch scale (~188K initial records)
- 🟡 API non-functional requirements (rate limits, pagination, circuit breakers)
- 🟡 Business rule engine selection

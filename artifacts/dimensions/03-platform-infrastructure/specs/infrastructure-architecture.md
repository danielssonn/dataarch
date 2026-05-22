# Infrastructure Architecture — Global Transaction Banking Canonical Platform

**Date:** 2026-05-21  
**Status:** Draft — pending Daniel's review  
**Author:** Data Architect Agent  
**Scope:** Platform topology, store selection, networking, compute, and operational model for the canonical graph and proof registry system.

---

## 1. Executive Summary

This document resolves the critical architecture ambiguity identified in the Architectural Impact Analysis: **what is the optimal infrastructure topology** for serving both operational graph traversal (sub-millisecond to <5ms latency) and analytical/batch workloads (aggregations, KPI computation, point-in-time reconstruction, regulatory reporting)?

Two options are evaluated:

| Option | Stores | Name |
|--------|--------|------|
| **A** | Graph DB (Neo4j) + RDBMS (PostgreSQL) + Data Lake (Databricks/Delta Lake) | **Three-Store Architecture** |
| **B** | RDBMS (PostgreSQL) + Data Lake (Databricks/Delta Lake) | **Two-Store Architecture** |

Both options share the same logical model (canonical graph + proof registry), the same API contract (Entity Platform API as sole write path), and the same governance posture (Unity Catalog, append-only enforcement, row-level security). The difference is in **where operational reads and writes execute**, and what trade-offs that creates.

---

## 2. Requirements (Non-Negotiable)

These drive the evaluation. Any topology must satisfy them all.

### 2.1 Latency Targets

| Operation | Target | Consumer |
|-----------|--------|----------|
| Entitlement check (party → channel access) | < 5ms p99 | Real-time transaction processing |
| Agent mandate pre-flight validation | < 1ms p99 | Agentic execution path (blocking) |
| Entity resolution by ID or LEI | < 10ms p99 | LOB applications |
| Ownership chain traversal (multi-hop) | < 50ms p99 | UBO/AML compliance |
| Beneficial owner resolution | < 100ms p99 | Regulatory reporting |
| Point-in-time proof chain retrieval | < 200ms p99 | Audit/regulatory examination |

### 2.2 Throughput Targets

| Operation | Target |
|-----------|--------|
| Relationship assertions (writes) | TBD — needs data volume estimation |
| Proof record appends | TBD — correlated with write volume |
| Analytical batch jobs (KPI, projections) | Hourly cadence acceptable |
| Integrity sweep | 15-minute cadence |

### 2.3 Consistency & Durability

- **Append-only enforcement** on all canonical data (invariant #4)
- **Every edge requires a proof chain** (invariant #5) — no unverified assertions
- **Point-in-time reconstruction** at arbitrary historical timestamps
- **Hash chain integrity** — SHA-256 linked proof records, verifiable at any time
- **Row-Level Security** via `domain_scope` — enforced at storage layer, not just application

### 2.4 Governance

- Unity Catalog governance plane with `tb_canonical` (Channels Technology owned) + LOB catalogs
- Column-level masking on proof records (auditor-only visibility for `intent_payload`, `signature`)
- Full temporal auditability — satisfies regulatory examination without separate archive systems
- LOB consumers read only via projections; never write back to canonical

---

## 3. Option A — Three-Store Architecture

### 3.1 Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                    Entity Platform API                           │
│              (Sole write path + read orchestration)              │
└──────────────┬──────────────────────┬──────────────────┬────────┘
               │                      │                  │
        ┌──────▼──────┐      ┌───────▼──────┐   ┌──────▼───────┐
        │   Neo4j     │      │  PostgreSQL   │   │  Databricks  │
        │  Graph DB   │      │    RDBMS      │   │  Delta Lake  │
        │             │      │               │   │              │
        │ • Canonical │      │ • Proof       │   │ • Analytical │
        │   graph     │      │   Registry    │   │   Projections│
        │ • Edges     │      │ • Mandates    │   │ • KPIs       │
        │ • Nodes     │      │ • Entitlements│   │ • LOB Views  │
        │ • Traversal │      │ • Auth data   │   │ • Batch Jobs │
        │   <5ms      │      │   <5ms        │   │ • Time-travel│
        └─────────────┘      └───────────────┘   └──────────────┘
               │                      │                  │
        ┌──────▼──────┐      ┌───────▼──────┐   ┌──────▼───────┐
        │  Neo4j      │      │  PostgreSQL   │   │  Unity       │
        │  CDC/Feed   │      │  CDC/Feed     │   │  Catalog     │
        │  → Delta    │      │  → Delta      │   │  (governs   │
        └─────────────┘      └───────────────┘   │   Delta)     │
                                                  └──────────────┘
```

### 3.2 Store Responsibilities

#### Neo4j — Operational Graph Store

| Concern | Detail |
|---------|--------|
| **Role** | Primary operational store for the canonical graph (nodes + edges) |
| **Workload** | Real-time graph traversal, relationship queries, ownership chain resolution, UBO resolution |
| **Write Path** | Entity Platform API writes new nodes/edges here first |
| **Sync to Delta** | CDC stream (Neo4j → Kafka → Databricks) for analytical materialization |
| **Strengths** | Native graph traversal (Cypher), sub-millisecond multi-hop queries, mature enterprise support, GDS library for advanced algorithms (community detection, centrality) |
| **Weaknesses** | Operational overhead (cluster management, backup/restore), limited native temporal support (requires application-level versioning), append-only enforcement is application-layer not storage-layer |

#### PostgreSQL — Structured Operational Store

| Concern | Detail |
|---------|--------|
| **Role** | ACID transactional store for proof registry, mandates, entitlements |
| **Workload** | Proof record appends (with hash chain validation), mandate CRUD, entitlement lookups, authorization checks |
| **Write Path** | Entity Platform API writes proof records and mandate state here |
| **Sync to Delta** | Logical replication (pgoutput) → Kafka → Databricks |
| **Strengths** | Mature ACID guarantees, constraint enforcement (CHECK constraints on proof chain references), row-level security native, temporal extensions (pg_ivm, bitemporal patterns), well-understood operational model |
| **Weaknesses** | No native graph traversal (adjacency queries at depth >3 become expensive), limited analytical capability vs Delta Lake |

#### Databricks/Delta Lake — Analytical Layer

| Concern | Detail |
|---------|--------|
| **Role** | Analytical projection layer, batch processing, temporal reconstruction, LOB views |
| **Workload** | KPI computation, integrity sweeps, point-in-time queries, LOB projection refresh, regulatory reporting, ML/analytics |
| **Data Source** | CDC-fed from Neo4j (graph state) + PostgreSQL (proof/mandate state) |
| **Strengths** | Native time-travel, Liquid Clustering for query optimization, Unity Catalog governance, scalable batch/stream processing, existing DDL implementation matches this layer |
| **Weaknesses** | Not suitable for sub-millisecond operational queries, latency for ad-hoc analytical queries (seconds not milliseconds), cost at scale for high-frequency small queries |

### 3.3 Data Flow

```
Write Path:
  API → Neo4j (graph mutation) + PostgreSQL (proof record) → Atomic commit via saga/2PC
         ↓
  CDC: Neo4j → Kafka → Databricks (graph state materialization)
       PostgreSQL → Kafka → Databricks (proof/mandate state materialization)
         ↓
  Databricks: Merge into append-only Delta tables → Unity Catalog projections

Read Path (Operational):
  API → Neo4j (graph traversal) + PostgreSQL (proof/mandate lookup) → Aggregate response

Read Path (Analytical):
  API/BI Tool → Databricks → Unity Catalog → Delta tables (time-travel enabled)
```

### 3.4 Sizing (Preliminary — needs data volume input)

| Component | Estimate | Basis |
|-----------|----------|-------|
| Neo4j Cluster | 3-node HA (1 primary, 2 read replicas) | Enterprise graph workloads; scale horizontally as entity count grows |
| PostgreSQL | Primary + 1 replica (read scaling for proof queries) | Proof registry is append-heavy, read patterns are targeted (by chain_id) |
| Databricks | All-purpose cluster (interactive) + Job clusters (batch) | Separate compute for interactive dev vs scheduled pipelines |
| Kafka | 3-broker cluster (CDC transport) | Standard for change event streaming; consider Confluent Cloud if managed preferred |

### 3.5 Pros & Cons

| Advantages | Disadvantages |
|------------|---------------|
| ✅ Optimal latency for graph traversal (Neo4j native) | ❌ Three stores to operate, monitor, and maintain |
| ✅ Optimal ACID for proof registry (PostgreSQL constraints) | ❌ Data consistency across stores requires CDC reliability + lag monitoring |
| ✅ Optimal analytics (Delta Lake time-travel + Unity Catalog) | ❌ Write path spans two stores — needs saga/2PC or compensating transactions |
| ✅ Proven pattern in enterprise (polyglot persistence) | ❌ CDC lag creates eventual consistency window — operational reads from Delta may be stale |
| ✅ Team skill specialization (graph engineers + DBAs + data engineers) | ❌ Higher infrastructure cost (three platforms vs two) |
| ✅ Clear separation of concerns (graph ≠ transactions ≠ analytics) | ❌ Failure mode complexity (which store is the source of truth when they diverge?) |

---

## 4. Option B — Two-Store Architecture

### 4.1 Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                    Entity Platform API                           │
│              (Sole write path + read orchestration)              │
└──────────────┬──────────────────────┬──────────────────┬────────┘
               │                      │                  │
        ┌──────▼──────┐            ┌──▼──────────────┐  │
        │  PostgreSQL  │            │  Databricks     │  │
        │    RDBMS     │            │  Delta Lake     │  │
        │              │            │                 │  │
        │ • Canonical  │            │ • Analytical    │  │
        │   Graph      │            │   Projections   │  │
        │   (relational│            │ • KPIs          │  │
        │    model)    │            │ • LOB Views     │  │
        │ • Proof      │            │ • Batch Jobs    │  │
        │   Registry   │            │ • Time-travel   │  │
        │ • Mandates   │            │ • Temporal      │  │
        │ • Entitlements│           │   Queries       │  │
        │ • Auth data  │            └─────────────────┘  │
        └──────┬───────┘                                 │
               │                                         │
        ┌──────▼──────┐                            ┌────▼───────┐
        │  PostgreSQL  │                            │  Unity     │
        │  Logical     │                            │  Catalog   │
        │  Replication │                            │  (governs  │
        │  → Kafka     │                            │   Delta)   │
        └──────┬───────┘                            └───────────┘
               │
        ┌──────▼──────┐
        │  Databricks  │
        │  (CDC sink)  │
        └─────────────┘
```

### 4.2 Store Responsibilities

#### PostgreSQL — Unified Operational Store

| Concern | Detail |
|---------|--------|
| **Role** | Single operational store for graph (relational model), proof registry, mandates, entitlements |
| **Workload** | All operational reads and writes: entity resolution, relationship queries, proof record appends, mandate validation, entitlement checks |
| **Graph Model** | Adjacency list pattern (nodes table + edges table with foreign keys); recursive CTEs for traversal; materialized paths or closure tables for frequently-queried depths |
| **Write Path** | Entity Platform API writes everything here in a single transaction |
| **Sync to Delta** | Logical replication (pgoutput) → Kafka → Databricks |
| **Strengths** | Single source of truth for operational data, ACID across graph + proof in one transaction, native RLS, CHECK constraints, mature operational tooling, simpler failure modes |
| **Weaknesses** | Graph traversal performance degrades at depth >3 without careful indexing/materialization, no native graph algorithms (community detection, centrality require custom implementation), recursive CTEs can be expensive at scale |

#### Databricks/Delta Lake — Analytical Layer

| Concern | Detail |
|---------|--------|
| **Role** | Same as Option A — analytical projection, batch processing, temporal reconstruction |
| **Workload** | Same as Option A |
| **Data Source** | CDC-fed from PostgreSQL only (single source simplifies sync) |
| **Strengths** | Same as Option A |
| **Weaknesses** | Same as Option A |

### 4.3 Data Flow

```
Write Path:
  API → PostgreSQL (graph + proof + mandate in single transaction) → Commit
         ↓
  CDC: PostgreSQL → Kafka → Databricks (unified materialization)
         ↓
  Databricks: Merge into append-only Delta tables → Unity Catalog projections

Read Path (Operational):
  API → PostgreSQL (all operational queries) → Response

Read Path (Analytical):
  API/BI Tool → Databricks → Unity Catalog → Delta tables (time-travel enabled)
```

### 4.4 Sizing (Preliminary — needs data volume input)

| Component | Estimate | Basis |
|-----------|----------|-------|
| PostgreSQL | Primary + 2 read replicas (scale reads for deep traversal queries) | Single store handles all operational load; may need connection pooling (PgBouncer) and aggressive indexing |
| Databricks | Same as Option A | Analytical workload unchanged |
| Kafka | Same as Option A | CDC transport unchanged, but only one source simplifies topic topology |

### 4.5 Graph Traversal in PostgreSQL — Feasibility Assessment

The critical question for Option B: **Can PostgreSQL handle the graph traversal workload at transaction banking scale?**

| Traversal Pattern | PostgreSQL Approach | Latency Expectation | Risk |
|-------------------|---------------------|---------------------|------|
| Entity resolution by ID/LEI | Simple indexed lookup | < 5ms ✅ | Low — straightforward |
| Direct relationships (1-hop) | Indexed join on edges table | < 5ms ✅ | Low — straightforward |
| Ownership chain (2-3 hops) | Recursive CTE with LIMIT depth | 10-50ms ⚠️ | Medium — depends on graph density |
| UBO resolution (variable depth) | Recursive CTE + materialized path | 50-200ms ⚠️ | Medium-High — could exceed 100ms target at scale |
| Regulatory exposure (multi-type edges) | Recursive CTE + type filtering | 50-200ms ⚠️ | Medium — complex query patterns |
| Community detection / centrality | Custom SQL or pgRouting extension | Seconds ❌ | High — not operational, must use Delta Lake |

**Mitigation strategies for Option B graph traversal:**

1. **Materialized paths** — store the full ancestry path as an array column; enables O(1) subtree queries at the cost of write amplification
2. **Closure tables** — pre-compute all ancestor/descendant pairs; fast reads but write-heavy on graph mutations
3. **pgRouting extension** — adds graph algorithms to PostgreSQL; covers shortest path, centrality, but not as mature as Neo4j GDS
4. **Strategic caching** — Redis layer for frequently-traversed paths (ownership chains change infrequently); cache invalidation on graph mutations
5. **Depth limiting** — enforce max traversal depth at API layer; most compliance queries are bounded (UBO = 25% ownership threshold, typically 2-4 hops)

### 4.6 Pros & Cons

| Advantages | Disadvantages |
|------------|---------------|
| ✅ Single operational source of truth — no cross-store consistency issues | ❌ Graph traversal performance at depth >3 requires careful optimization |
| ✅ Atomic writes across graph + proof (single transaction) | ❌ No native graph algorithms — custom implementation needed |
| ✅ Simpler operations (two platforms vs three) | ❌ Write amplification for materialized paths/closure tables |
| ✅ Lower infrastructure cost (one fewer platform) | ❌ Cache layer adds complexity if needed for traversal performance |
| ✅ Simpler CDC (one source → Delta) | ❌ PostgreSQL scaling has harder ceiling than Neo4j's horizontal graph partitioning |
| ✅ Clearer failure modes (one store to recover) | ❌ Team may need new skills (advanced PostgreSQL, recursive query optimization) |

---

## 5. Head-to-Head Comparison

### 5.1 Requirement Satisfaction

| Requirement | Option A (3-Store) | Option B (2-Store) |
|-------------|-------------------|-------------------|
| Entitlement check < 5ms | ✅ Native (PostgreSQL indexed lookup) | ✅ Native (PostgreSQL indexed lookup) |
| Mandate validation < 1ms | ✅ Native (PostgreSQL) | ✅ Native (PostgreSQL) |
| Entity resolution < 10ms | ✅ Native (Neo4j) | ✅ Native (PostgreSQL indexed) |
| Ownership chain < 50ms | ✅ Native (Neo4j traversal) | ⚠️ Possible with materialized paths + caching |
| UBO resolution < 100ms | ✅ Native (Neo4j) | ⚠️ Risk at scale; needs POC validation |
| Proof chain retrieval < 200ms | ✅ PostgreSQL + Delta time-travel | ✅ PostgreSQL + Delta time-travel |
| Append-only enforcement | ⚠️ Application-layer in Neo4j; native in Postgres | ✅ Native CHECK constraints everywhere |
| Point-in-time reconstruction | ✅ Delta Lake time-travel | ✅ Delta Lake time-travel |
| Atomic graph + proof writes | ⚠️ Saga/2PC across Neo4j + Postgres | ✅ Single PostgreSQL transaction |
| Unity Catalog governance | ✅ Delta Lake layer | ✅ Delta Lake layer |
| Row-Level Security | ✅ Both stores support it | ✅ Native PostgreSQL RLS |
| Operational simplicity | ❌ Three platforms to manage | ✅ Two platforms to manage |
| Infrastructure cost | ❌ Higher (three platforms) | ✅ Lower (two platforms) |

### 5.2 Operational Complexity

| Dimension | Option A | Option B |
|-----------|----------|----------|
| Platforms to operate | 3 (Neo4j + Postgres + Databricks) | 2 (Postgres + Databricks) |
| CDC pipelines | 2 (Neo4j→Delta + Postgres→Delta) | 1 (Postgres→Delta) |
| Consistency model | Eventual (CDC lag between stores) | Strong (single operational store) |
| Backup/recovery | 3 independent strategies | 2 independent strategies |
| Monitoring surfaces | 3 dashboards + CDC lag metrics | 2 dashboards + CDC lag metrics |
| Team skills | Graph DB + DBA + Data Eng | DBA + Data Eng |
| Write transaction scope | Distributed (saga/2PC) | Local (single transaction) |

### 5.3 Cost Model (Relative — needs actual sizing)

| Cost Factor | Option A | Option B |
|-------------|----------|----------|
| License/subscription | Neo4j Enterprise + PostgreSQL (open) + Databricks | PostgreSQL (open) + Databricks |
| Compute | Higher (3 clusters) | Lower (2 clusters) |
| Storage | Higher (graph data replicated to Delta) | Lower (single operational copy → Delta) |
| Operational labor | Higher (3 platforms) | Lower (2 platforms) |
| Kafka/CDC | Same | Same |

---

## 6. Recommendation Framework

The right choice depends on three factors that need concrete answers before deciding:

### 6.1 Decision Factor 1: Graph Traversal Depth & Frequency

**If** the majority of operational queries are 1-2 hop traversals (entity resolution, direct relationship lookups, entitlement checks):

→ **Option B is sufficient.** PostgreSQL with proper indexing and materialized paths can meet the latency targets.

**If** multi-hop traversals (3+ hops) are frequent and must consistently hit <50ms p99:

→ **Option A is safer.** Neo4j's native graph engine handles arbitrary-depth traversal without query plan degradation.

### 6.2 Decision Factor 2: Data Volume

**If** entity count < 1M, edge count < 10M, traversal depth ≤ 3:

→ **Option B is viable.** PostgreSQL can handle this scale with proper indexing.

**If** entity count > 1M, edge count > 50M, or variable-depth traversal is common:

→ **Option A is recommended.** Neo4j scales horizontally for graph workloads; PostgreSQL recursive CTEs degrade at this scale.

### 6.3 Decision Factor 3: Team & Operational Capacity

**If** the team has PostgreSQL expertise but no graph database experience, and operational simplicity is a priority:

→ **Option B reduces risk.** Fewer moving parts, easier to staff, simpler incident response.

**If** the team can invest in Neo4j expertise and values optimal graph performance:

→ **Option A delivers better performance** at the cost of operational overhead.

---

## 7. Recommendation

**Start with Option B (Two-Store) with a POC exit criterion.**

### Rationale

1. **The current DDL implementation is already Delta Lake.** The 31-step DDL execution order, Unity Catalog topology, and pipeline definitions all target this layer. Starting with Option B means the analytical layer is ready; we only need to validate PostgreSQL as the operational store.

2. **Most operational queries are shallow.** Entitlement checks (<5ms), entity resolution (<10ms), and mandate validation (<1ms) are all 0-1 hop lookups. These work well in PostgreSQL.

3. **The deep traversal use cases (UBO, ownership chain) are bounded.** Regulatory UBO resolution typically caps at 25% ownership thresholds, which in practice means 2-4 hops. With materialized paths and strategic caching, PostgreSQL can likely meet the <100ms target.

4. **Simplicity wins early.** Option B eliminates the cross-store consistency problem entirely. Atomic writes across graph + proof in a single transaction is a significant architectural advantage during Phase 1 when the system is under the most pressure.

5. **Option A remains available as an evolution.** If POC benchmarks show PostgreSQL cannot meet traversal latency targets at expected data volumes, migrating the graph layer to Neo4j is a contained change — the API contract and Delta Lake layer stay the same.

### POC Exit Criteria

Before committing to Option B, validate:

| Benchmark | Target | Pass/Fail |
|-----------|--------|-----------|
| Entity resolution by LEI (1M entities) | < 10ms p99 | |
| Direct relationship lookup (10M edges) | < 5ms p99 | |
| Ownership chain traversal (3 hops, 10M edges) | < 50ms p99 | |
| UBO resolution (variable depth, 10M edges) | < 100ms p99 | |
| Proof record append + hash chain computation | < 10ms per write | |
| Mandate validation | < 1ms p99 | |
| Entitlement check | < 5ms p99 | |
| Concurrent write throughput | TBD — needs volume estimate | |

**If any benchmark fails → evaluate Option A for the specific failing workload.** Consider a hybrid: PostgreSQL for proof/mandate/entitlement + Neo4j only for graph traversal, with Delta Lake unchanged.

---

## 8. Shared Infrastructure (Both Options)

Elements that are the same regardless of store choice:

### 8.1 Databricks / Delta Lake Layer

Unchanged between options. The analytical layer serves:

- **KPI Computation** — hourly job refreshing `tb_canonical.metrics.canonical_kpis`
- **Integrity Sweep** — 15-minute cadence validating hash chain integrity
- **LOB Projection Refresh** — CDF-triggered updates to `tb_cb`, `tb_cm`, `tb_wm`
- **Entitlement Snapshot** — periodic authority state capture
- **Point-in-Time Queries** — Delta Lake time-travel for historical reconstruction
- **Regulatory Reporting** — batch exports, audit trails

### 8.2 Unity Catalog Governance

```
tb_canonical                          ← Channels Technology
├── entity                            ← nodes, edges, current_* views
├── product                           ← definitions, instances, bundles
├── account                           ← operating, virtual, pools
├── transaction                       ← payments, trades, FX, fees
├── channel                           ← entitlements, mandates
├── proof                             ← chains, records, integrity views
└── metrics                           ← KPI definitions, time-series

tb_cb / tb_cm / tb_wm                 ← LOB read-projections only
```

### 8.3 Entity Platform API

Unchanged API contract. The API orchestrates reads/writes across the operational store(s) and Delta Lake. Internal implementation differs by option, but external contract is identical.

### 8.4 Networking & Security

| Concern | Detail |
|---------|--------|
| **VNet / VPC** | Azure VNet for Databricks + PostgreSQL/Neo4j; private endpoints for all data stores |
| **API Gateway** | Azure API Management or Kong; rate limiting, auth, routing |
| **Kafka** | Confluent Cloud or MSK; CDC transport from operational store(s) → Databricks |
| **Secrets** | Azure Key Vault or HashiCorp Vault; no hardcoded credentials |
| **TLS** | All inter-service communication encrypted in transit |
| **Backup** | Operational store: native backup (pg_dump/Neo4j backup); Delta Lake: Unity Catalog + Delta time-travel provides implicit backup |

---

## 9. Open Questions

| # | Question | Impact | Blocked By |
|---|----------|--------|------------|
| 1 | What are the estimated entity/edge volumes? | Sizing for both options | Daniel / business input |
| 2 | What is the expected write throughput (relationships/sec)? | Write path design | Daniel / business input |
| 3 | Are there existing PostgreSQL instances we can leverage? | Option B feasibility | Infrastructure inventory |
| 4 | Is there an existing Kafka/Confluent deployment? | CDC infrastructure | Infrastructure inventory |
| 5 | What is the LOB integration timeline? | Phase 2 dependency | Program management |
| 6 | Are there specific regulatory requirements for proof chain storage duration? | Retention policy | Compliance/legal |
| 7 | What is the budget envelope for infrastructure? | Option A vs B cost trade-off | Finance |

---

## 9. Proof Registry Store: PostgreSQL vs. QLDB

### Evaluation

| Criterion | PostgreSQL + Hash Chain | Amazon QLDB |
|-----------|------------------------|-------------|
| **Append-only enforcement** | Trigger-based insert-only policy + CHECK constraints | Native (immutable by design) |
| **Cryptographic integrity** | SHA-256 hash chaining in application logic | Native (SHA-256 digest map) |
| **Point-in-time queries** | Application-layer replay from event history | Native (`AS OF` syntax) |
| **Regulatory narrative** | "Immutable ledger pattern in PostgreSQL" | "AWS purpose-built immutable ledger" |
| **Team familiarity** | High (existing SQL skills) | Low (new technology) |
| **Operational complexity** | Low (one less technology to manage) | Medium (new service, new tooling) |
| **Cross-store consistency** | Same RDBMS as kinetic layer → single transaction for action execution | Separate store → distributed transaction needed |
| **Azure-native** | Azure Database for PostgreSQL (fully managed) | Available but not Azure-native |
| **Cost** | Pay for compute + storage | Pay per digest map + storage |

### Decision: PostgreSQL

**Rationale:**

1. **Cross-store consistency.** The kinetic layer (action execution, proof records, mandate validation) already lives in PostgreSQL. Keeping the proof registry in the same store means action execution writes (graph mutation in Neo4j + proof record in PostgreSQL) touch only two stores instead of three. This simplifies the Saga/compensating transaction pattern.

2. **Team familiarity.** The engineering team has PostgreSQL expertise. QLDB introduces a new technology with no existing internal knowledge, adding training overhead and operational risk.

3. **Operational simplicity.** One fewer technology to manage, monitor, and operate. PostgreSQL's append-only trigger pattern + hash chaining provides equivalent cryptographic integrity to QLDB's digest map.

4. **Azure alignment.** Azure Database for PostgreSQL is a first-class managed service with geo-replication, automated backups, and integration with Azure Monitor. QLDB is available but not Azure-native.

5. **Regulatory narrative is addressable.** QLDB's advantage is the "purpose-built immutable ledger" story. This can be addressed through documentation: the append-only trigger, hash chain verification pipeline, and integrity sweep job collectively demonstrate equivalent immutability. The regulatory examination conversation is about evidence, not technology branding.

### Implementation Notes

- Proof registry tables (`proof_chains`, `proof_records`) reside in the same PostgreSQL instance as kinetic layer tables
- Append-only enforced via `BEFORE UPDATE/DELETE` trigger that raises an exception
- Hash chain computed at insert time; integrity sweep job runs every 15 minutes to validate chain continuity
- Column-level masking via PostgreSQL row-level security + Unity Catalog grants for Delta Lake mirror

---

## 10. Next Steps

1. **Daniel reviews this document** — confirm scope, flag gaps, indicate preference direction
2. **Obtain data volume estimates** — entity count, edge count, write throughput (addresses Open Questions #1-2)
3. **Infrastructure inventory** — existing PostgreSQL, Kafka, Azure resources (addresses #3-4)
4. **Design POC test harness** — benchmark Neo4j traversal + PostgreSQL transaction throughput against estimated volumes
5. **Run POC benchmarks** — validate three-store architecture against latency targets in §2.1
6. **Finalize infrastructure decision** — three-store architecture is the committed direction; POC validates sizing, not topology

---

*This document supersedes the infrastructure section of the original Architecture.md §9 Technology Options. Once approved, it becomes the authoritative reference for platform provisioning and infrastructure procurement.*

---

## Change Log

| Date | Change |
|------|--------|
| 2026-05-22 | Added §9 Proof Registry Store decision (PostgreSQL over QLDB). Updated §10 Next Steps to reflect committed three-store direction. |




# Dimension 03: Platform & Infrastructure — Memory Log

## Scope
Databricks on Azure, Unity Catalog governance plane, Lakebase instances, Neo4j cluster sizing, networking, compute profiles. Purely tech-stack topology and provisioning concerns. No business semantics leaking in either direction.

---

## Current State (2026-05-21)
Session recovered from git history + research artifacts after restart wipe. DDL README migrated to `artifacts/dimensions/03-platform-infrastructure/specs/ddl-readme.md`. Full Architecture spec at original location still has tech stack details in §9 Technology Options.

### Platform Stack (Locked Decisions — per Impact Analysis)
- **Databricks + Delta Lake** locked as analytical/projection layer with Unity Catalog governance plane explicitly defined
  - `tb_canonical` catalog owned by Channels Technology — primary canonical schema
  - LOB catalogs (`tb_cb`, `tb_cm`, `tb_wm`) open for domain extensions but never write back to canonical (read-projections only via grants + RLS)
- **Liquid Clustering** strategy explicitly defined per table: e.g., `entity.edges` clustered by `(type, from_node_id, state)` — assumes specific query patterns; if actual access patterns differ significantly (heavy cross-LOB joins or time-series queries on edges), clustering will need adjustment and full reorg

### Graph Store Recommendation (§9 Tech Options)
| Option | Fit | Notes |
|--------|-----|-------|
| **Neo4j** | High | Native graph, mature Cypher, enterprise support — RECOMMENDED for canonical store |
| Amazon Neptune | High | Managed, supports RDF + property graph, good for regulated envs |
| Apache AGE (Postgres ext) | Medium | Lower overhead if existing Postgres infra |
| Databricks-only | Medium | Better for analytical projections than operational traversal |

**Recommendation:** Neo4j as canonical store. Databricks for analytical projections only. Entity Platform API sits between — consumers never touch graph directly.

### Proof Registry Store (§9)
- **Amazon QLDB** recommended (purpose-built immutable ledger, strong regulatory narrative) over PostgreSQL insert-only or Kafka compacted topics
- Alternatives considered: Postgres with hash chain + check constraints; Apache Kafka for event-sourced high-throughput

### Unity Catalog Topology (from DDL README execution order — 31 steps):
```
tb_canonical                              ← top-level catalog (Channels Technology owns)
├── tb_canonical.entity                   ← entity schema (Party, EntityGroup, KYC)
├── tb_canonical.product                  ← product schema (Definition, Instance, Bundle)
├── tb_canonical.account                  ← account schema (Operating, Virtual, Pool)
├── tb_canonical.transaction              ← transaction schema (Payment, Trade, FX)
├── tb_canonical.channel                  ← channel + entitlement schema
├── tb_canonical.proof                    ← proof chain summaries (not full registry)
└── tb_canonical.metrics                  ← canonical KPIs defined once

tb_cb / tb_cm / tb_wm                     ← LOB-owned extension catalogs (read-projection only)
```

### Pipeline Infrastructure (~4 pipelines identified):
1. **Integrity Sweep** — 15min cadence, validates hash chain integrity across proof registry
2. **KPI Computation** — hourly refresh of canonical metrics in `tb_canonical.metrics`
3. **CB Projection Refresh** — LOB-specific analytical view updates via CDF-triggered jobs
4. **Entitlement Snapshot Job** — periodic authority state capture for audit replay

### Compute Targets (from API contract implications):
- Entitlement store access: < 5ms latency target
- Agent mandate validation (`/mandates/{agentId}/validate`): sub-millisecond on critical path, blocks execution if invalid
- Point-in-time queries via Delta Lake time-travel — need temporal partitioning strategy validated at scale

## Key Decisions Captured in Spec (from impact analysis)
1. **Databricks/Delta locked** as analytical projection layer with production-grade DDL (not exploratory schema); 31-step execution order requires platform provisioning before Phase 1 begins
2. **Row-Level Security via `domain_scope ARRAY<STRING>`** — dynamic LOB context resolution (`array_contains(domain_scope, caller_lob)`) prevents cross-LOB data leakage at SQL layer even if app logic fails

## Open Questions / Critical Risks (from impact analysis)
- 🔴 **Two-store vs one-store ambiguity** — spec recommends Neo4j + Databricks but entire DDL implementation is Delta Lake with no separate graph DB references; blocks infrastructure procurement and team skill assessment until resolved via POC benchmarks against actual data volumes
- 🟠 No CI/CD pipeline definition for 31-step DDL deployment (dev→test→UAT→prod sequence, schema versioning, rollback strategy when append-only tables can't be dropped/truncated)
- Liquid Clustering assumptions need validation against real query patterns before Phase 1

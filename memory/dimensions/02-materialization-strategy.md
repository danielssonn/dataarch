# Dimension 02: Materialization Strategy — Memory Log

## Scope
How the logical model physically lives and ages. Append-only tables vs current-state views, temporal indexing, CDF pipelines, access-tier routing (which queries go where). The "how data moves" layer. No business semantics; no infra topology.

---

## Current State (2026-05-21)
Session recovered from git history + research artifacts after restart wipe. Impact analysis at `artifacts/dimensions/02-materialization-strategy/research/impact-analysis.md` (~16KB, 115 lines). DDL skeleton exists but SQL files not yet populated (empty directories created during migration prep).

### Physical Model — Delta Lake / Unity Catalog
- **tb_canonical** catalog owned by Channels Technology — primary canonical schema with append-only enforcement (`delta.appendOnly = true`) on all core tables
- **LOB catalogs:** tb_cb, tb_cm, tb_wm as read-projection consumers only; never write back to canonical (enforced via grants + RLS)
- Liquid Clustering strategy per table: e.g., `entity.edges` clustered by `(type, from_node_id, state)` for graph traversal optimization

### Proof Registry Materialization
Append-only event-sourced tables with cryptographic hash chaining (`hash` + `previousHash`):
- `tb_canonical.proof.01_proof_chains.sql` — chain metadata and current state derived from replay
- `tb_canonical.proof.02_proof_records.sql` — individual records (unbounded growth)
- Views: `current_proof_chains_view`, `proof_integrity_view`

### Pipeline Definitions Identified (~4 pipelines per impact analysis):
1. **Integrity Sweep** — 15min cadence, validates hash chain integrity across proof registry
2. **KPI Computation** — hourly refresh of canonical metrics (8 KPIs defined: client_revenue_total, onboarding_cycle_time <5d target, product_adoption_rate, entitlement_provisioning_time <4h, cross_lob_client_count, kyc_reuse_rate >80%, payment_stp_rate >95%, proof_chain_integrity_rate 100% target)
3. **CB Projection Refresh** — LOB-specific analytical view updates via CDF-triggered jobs
4. **Entitlement Snapshot Job** — periodic capture of authority state for audit replay

### Canonical Metrics (Governance Commitments, Not Just Monitoring):
| KPI | Target | Notes |
|-----|--------|-------|
| onboarding_cycle_time | < 5 days | Cross-LOB client setup duration |
| entitlement_provisioning_time | < 4 hours | Time from mandate grant to system enforcement |
| kyc_reuse_rate | > 80% | Reusing existing KYC across LOBs vs duplicate collection |
| payment_stp_rate | > 95% | Straight-through processing for payments |
| proof_chain_integrity_rate | 100% | Every edge has valid, unbroken chain — aspirational SLA under pressure during initial migration when legacy relationships lack digital evidence; needs exception handling + remediation timeline per relationship type/risk tier |

## Key Decisions Captured in Spec (from impact analysis)
- **Databricks/Delta Lake locked as analytical projection layer** with Unity Catalog governance and Liquid Clustering strategy explicitly defined per table — this is production-grade DDL, not exploratory schema; 31-step execution order requires platform provisioning before Phase 1 begins

## Open Questions / Critical Risks (from impact analysis)
- 🔴 **Two-store vs one-store ambiguity** — spec recommends Neo4j as canonical store + Databricks for analytical projections, but entire DDL implementation is Delta Lake with no separate graph database references; blocks infrastructure procurement and team skill assessment
- 🟠 No initial seeding strategy documented beyond DDL skeleton (legacy relationships lacking digital evidence need migration runbook)
- Storage growth unbounded — append-only tables without partitioning/archival/lifecycle management for aged records
- Hash chain verification latency at batch scale during Phase 1 data seeding needs benchmarking

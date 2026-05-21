# Architectural Impact Analysis — txnbankingdatamodel Repository

**Date:** 2026-05-21  
**Repo:** https://github.com/danielssonn/txnbankingdatamodel (main, sha `796ef70`)  
**Scope:** Full codebase review — Architecture.md (~29KB), 30+ DDL files, Unity Catalog mappings, pipeline definitions, Entity Platform API spec

---

## Executive Summary

This is a **complete architecture specification + reference implementation** for an evidence-anchored knowledge graph and proof registry system targeting Global Transaction Banking at a Top 10 North American bank. The repo defines both the logical model (Architecture.md) and physical DDL layer (Databricks/Delta Lake), with operational pipelines, stakeholder engagement strategy, and open questions documented inline.

**Maturity:** Specification-complete. Ready for Phase 1 implementation decisions. Not yet validated against production data volumes or performance benchmarks.

---

## Repository Inventory

| Area | Files | Purpose |
|------|-------|---------|
| Architecture.md | 29KB, 11 sections | Full logical spec: graph model, proof registry, mandates, projections, API contract, ZKP integration points, tech options (Neo4j+QLDB), key invariants, phased plan |
| ddl/ | ~30 SQL files | Databricks/Delta Lake physical implementation across Unity Catalog schemas (`tb_canonical`, `tb_cb`, `tb_cm`, `tb_wm`) |
| ddl/pipelines/ | 4 pipeline definitions | Integrity sweep (15min), KPI computation (hourly), CB projection refresh, entitlement snapshot job — all CDF-triggered or scheduled |
| docs/Engagement.md | Stakeholder matrix | Mandate → Authority → Participation → Gravity framework targeting Head of GTB through Chief AI Officer for bootcamp delivery model |

---

## Architectural Impacts by Category

### 1. Data Platform Foundation (High Impact)

**Decision locked:** Databricks + Delta Lake as the analytical/analytics projection layer, with Unity Catalog governance and Liquid Clustering strategy explicitly defined per table. The `tb_canonical` catalog is owned by Channels Technology; LOB catalogs (`tb_cb`, `tb_cm`, `tb_wm`) are open for domain extensions but never write back to canonical — enforcing a strict read-only consumer pattern via projection views with explicit freshness timestamps and LOB-scoped RLS through `domain_scope ARRAY<STRING>`.

**Impact:** This is not an exploratory schema. The DDL execution order (31 sequential steps), catalog grants, row-level security functions, append-only table properties (`delta.appendOnly = true`), Change Data Feed enablement on core tables, and pipeline scheduling are all production-grade specifications requiring platform provisioning before Phase 1 can begin.

**Open risk:** Liquid Clustering column choices assume specific query patterns (e.g., `entity.edges` clustered by `(type, from_node_id, state)` for graph traversal). If actual access patterns differ significantly — e.g., heavy cross-LOB joins or time-series queries on edges — the clustering strategy will need adjustment and full table reorganization.

### 2. Graph Store vs. Delta Lake Tension (Critical)

**The spec recommends Neo4j as canonical store + Databricks for analytical projections**, but the entire DDL implementation is in Delta Lake/Databricks with no separate graph database references. This creates a fundamental architecture question: **Is this a two-store system or one?**

- If two stores, there's an unmodeled synchronization layer between Neo4j (operational CRUD + sub-millisecond traversal) and Delta Lake (analytical projections). The Entity Platform API spec shows endpoints that imply real-time graph operations (`POST /relationships`, `GET .../ownership-chain`), which would be impractical against Delta Lake alone at transaction banking scale.
- If one store, the Neo4j recommendation in §9 becomes irrelevant — and we need to validate whether Delta Lake can support sub-millisecond relationship traversal for operational use cases (entitlement checks <5ms is called out as a target).

**Recommendation:** Resolve this before Phase 1 kickoff. The current DDL assumes single-store Delta Lake, but the API contract implies two-store semantics. This affects infrastructure budgeting, team skills requirements, and data consistency guarantees.

### 3. Proof Registry Design (High Impact)

The proof registry is architecturally ambitious: append-only event-sourced records with cryptographic hash chaining (`hash` + `previousHash` per record), channel-aware evidence capture across six proof types (declarative through regulatory), authority-linked entitlement snapshots, and ZKP integration points for agentic mandate verification.

**Impacts:**
- **Storage growth is unbounded.** Every relationship change generates new append-only records with full intent payloads containing potentially large JSON blobs (`intentPayload: Record<string, unknown>`). At transaction banking scale (millions of edges × multiple proof events per edge), this will grow rapidly without partitioning or archival strategy. The current DDL has no retention policy, partition scheme beyond Liquid Clustering columns, or lifecycle management for aged records.
- **Hash chain verification adds latency to every write.** Computing SHA-256 and linking `previousHash` is computationally trivial per record but becomes significant at batch scale during initial data seeding (§8 Phase 1). Need benchmarking on seed volume × hash computation throughput.
- **ZKP integration points are defined as placeholders** (`zkpProof?: string`). The choice of proof system (Groth16 vs PLONK vs STARKs) is listed as an open question with no evaluation framework yet — this blocks Phase 4 but doesn't block earlier phases since it's opt-in per record.

### 4. Entity Platform API Contract (Medium Impact)

The API spec defines a clean RESTful interface over the canonical graph: entity resolution by ID/LEI, relationship traversal (`ownership-chain`, `beneficial-owners`), point-in-time queries via `?asOf={timestamp}`, and proof chain retrieval at any historical moment. Pre-flight mandate validation endpoint for agentic scope checking is included.

**Impacts:**
- This API becomes the **sole write path to canonical data**. All operational systems (CB, CM, Wealth) must route through it rather than writing directly — which means existing LOB teams need integration changes before any migration begins. The bootcamp engagement model in `docs/Engagement.md` addresses this politically but not technically.
- Point-in-time queries (`asOf`) require efficient temporal indexing on append-only tables. Delta Lake's time-travel supports this natively, but at scale the scan ranges for arbitrary historical timestamps could be expensive without careful partitioning by temporal boundaries (e.g., monthly partitions with `created_at` as a co-clustering column).
- The API contract shows no rate limiting, pagination, or circuit breaker patterns — these need to be addressed in implementation design before exposing this to production LOB consumers.

### 5. Agentic Mandate Model (Forward-Looking Impact)

The three-tier mandate hierarchy (`HumanMandate → SystemMandate → AgentMandate`) with delegation chain validation, pre-flight scope checking, and automatic suspension on violation is a complete specification for AI agent governance in transaction banking contexts. This is ahead of most enterprise implementations — few banks have formalized this level of agentic authority tracking yet.

**Impacts:**
- Mandates themselves require proof chains (recursive: `AgentMandate.proofChainId`), creating circular dependency resolution during initial data load that needs careful sequencing in the seeding pipeline.
- The scope violation handling spec mandates **blocking before execution**, not post-hoc detection — this means the mandate validation endpoint (`POST /mandates/{agentId}/validate`) is on the critical path for every agent action and must meet sub-millisecond latency targets alongside the entitlement store (<5ms target).

### 6. Canonical Metrics as Contract (Medium Impact)

Eight KPIs defined once in `tb_canonical.metrics` with explicit definitions, time-series fact tables (`canonical_kpis`), trend views, and intermediate metric computation logic seeded directly into DDL:
- `client_revenue_total`, `onboarding_cycle_time (<5d target)`, `product_adoption_rate`, `entitlement_provisioning_time (<4h)` , `cross_lob_client_count`, `kyc_reuse_rate (>80%)` , `payment_stp_rate (>95%)`, `proof_chain_integrity_rate (100% target)`

**Impact:** These are governance commitments, not just monitoring. The 100% proof chain integrity rate is an aspirational SLA that will be under constant pressure during initial data migration — legacy systems won't have evidence-anchored relationships and the gap between "no historical proofs" and "every edge has valid chains" needs a realistic transition plan with temporary exception handling.

### 7. Security & Governance (High Impact)

The security model is multi-layered:
1. **Append-only enforcement** via Delta table properties (`delta.appendOnly = true`) — prevents direct mutation even by privileged users outside the API path, plus `CHECK` constraints on proof chain references as a last-resort guard against bypass writes
2. **Row-Level Security** via `domain_scope ARRAY<STRING>` filtering in materialized views with dynamic LOB context resolution (`array_contains(domain_scope, caller_lob)`) — prevents cross-LOB data leakage at the SQL layer even if application logic fails  
3. **Column-Level Masking** on proof records (`intent_payload`, `signature` visible only to auditor roles via masked views; raw table access restricted to writer/auditor roles), with Unity Catalog grants explicitly defined per catalog/schema for separation of duties
4. **Temporal auditability** — full point-in-time reconstruction from append-only event history satisfies regulatory examination requirements without separate archive systems

### 8. Implementation Risks & Gaps

| Risk | Severity | Notes |
|------|----------|-------|
| Two-store vs one-store ambiguity (Neo4j + Delta Lake) | 🔴 Critical | Blocks infrastructure procurement and team skill assessment — must resolve before Phase 1 kickoff with proof-of-concept benchmarks against actual data volumes |
| No initial seeding strategy documented beyond DDL skeleton | 🟠 High | How do we populate millions of existing entities/relationships into append-only tables while creating valid proof chains for legacy relationships that lack digital evidence? Need a migration runbook before Phase 1 completion, including exception handling when historical proofs cannot be constructed — the `kyc_reuse_rate` and `proof_chain_integrity_rate` metrics will fail until this is resolved |
| No test data strategy or benchmarking harness defined | 🟠 High | The phased plan references "unit tests: every edge write requires proof chain record" but no validation framework exists yet. Need performance baselines for graph traversal queries against Delta Lake before committing to single-store vs two-store decision, plus load testing on hash-chain computation throughput at expected ingestion rates |
| ZKP library choice deferred with no evaluation criteria | 🟡 Medium | Phase 4 blocker — should start vendor/library research now since procurement cycles in banks are long (6-12 months) and the open question lists three proof systems without comparison matrix or decision framework for selecting based on regulatory acceptance, performance characteristics, or integration complexity |
| No CI/CD pipeline definition for DDL deployment | 🟡 Medium | 31-step execution order needs automated migration tooling — who runs these? In what environment sequence (dev → test → UAT → prod)? How are schema changes versioned and rolled back when append-only tables can't be dropped or truncated without full catalog recreation? |
| API contract lacks non-functional requirements | 🟡 Medium | No rate limits, pagination strategy, circuit breakers, retry semantics, or error taxonomy defined — LOB consumers will need these before integration work begins. Consider OpenAPI 3.x spec generation as Phase 1 deliverable alongside the CRUD implementation to enable parallel consumer development with mock servers |

---

## Recommended Next Steps (Priority Order)

1. **Resolve Neo4j vs Delta Lake decision** through proof-of-concept benchmarks — test sub-millisecond relationship traversal and entitlement checking against actual data volumes before locking infrastructure
2. **Define initial seeding/migration runbook** including exception handling for legacy relationships lacking digital evidence, with clear acceptance criteria for when a "best effort" proof chain is acceptable vs requiring remediation
3. **Establish performance baselines:** hash-chain computation throughput at expected ingestion rates, temporal query latency across Delta Lake time-travel ranges (partitioning strategy validation), graph traversal patterns against Liquid Clustering assumptions  
4. **Generate OpenAPI 3.x spec** from API contract for parallel consumer development — LOB integration teams need this before Phase 2 to begin mock-server testing and client code generation
5. **Begin ZKP library evaluation research now** even though it's a Phase 4 item — document decision criteria matrix (proof size vs verification speed vs regulatory acceptance vs trusted setup requirements) with vendor landscape assessment to prevent procurement delays from blocking the agentic layer timeline

---

## Questions for Discussion

- Are you planning this as two-store (Neo4j + Delta Lake per spec §9 recommendation) or single-store (Delta Lake only matching current DDL implementation)? This cascades into every downstream decision — infrastructure, team composition, data consistency model
- What's the estimated entity/relationship volume we're designing for? The Liquid Clustering strategy and append-only storage approach need concrete numbers to validate partitioning boundaries, compute sizing, and cost projections  
- Is there an existing LOB integration pattern (API gateway standards, auth protocols, rate limiting policies) that the Entity Platform API must conform to, or is this establishing a new platform contract?
- For legacy data migration: do we have access to historical evidence documents/audit trails that could be retroactively ingested as proof records, or will initial seeding require an exception process with defined remediation timelines per relationship type and regulatory risk tier?
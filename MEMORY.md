# MEMORY.md — Data Architect Agent Memory Index

## Active Projects

### Global Transaction Banking Platform (2026-05-20 → ongoing)
- **Client:** Daniel Maly | Top 10 North American bank
- **Status:** Architecture recovered from git history + research artifacts post-restart wipe. All five dimensions rebuilt with full content from discovery notes, Architectural Impact Analysis (~32KB spec), and DDL definitions.

#### Five Architecture Dimensions (Memory Files)
| # | File | Bytes | Status |
|---|------|-------|--------|
| 01 | `memory/dimensions/01-logical-model.md` | ~6.5K | ✅ Expanded 2026-05-22 — entity catalog (17.7K, all 4 product lines), relationship scenarios (17.2K, 7 validated workflows), 5 Mermaid diagrams + PNGs, 5 new node subtypes added, `creates` edge recommended, compound settlement validated |
| 02 | `memory/dimensions/02-materialization-strategy.md` | ~3.9K | ✅ Rebuilt — Delta Lake/Databricks append-only tables, Liquid Clustering per table, Unity Catalog governance plane (tb_canonical + LOB catalogs), CDF pipelines (~4 defined: integrity sweep 15min, KPI hourly, CB projection refresh, entitlement snapshot), canonical metrics/KPI targets |
| 03 | `memory/dimensions/03-platform-infrastructure.md` | ~5.0K | ✅ Rebuilt — Databricks on Azure locked as analytical layer, Neo4j recommended for operational graph store (two-store architecture pending POC validation), QLDB proof registry recommendation, Unity Catalog topology + 31-step DDL execution order, RLS via domain_scope ARRAY\<STRING\>, compute targets (<5ms entitlement) |
| 04 | `memory/dimensions/04-api-integration-contract.md` | ~4.6K | ✅ Rebuilt — Entity Platform API surface (REST endpoints for entity resolution by ID/LEI, relationship traversal including ownership-chain/beneficial-owners/regulatory-exposure), point-in-time queries via ?asOf={timestamp}, proof chain retrieval at any historical moment, sole write path to canonical data, LEI as canonical identity invariant |
| 05 | `memory/dimensions/05-governance-trust-layer.md` | ~7.1K | ✅ Rebuilt — Proof registry design (append-only event-sourced with SHA-256 hash chaining), proof type taxonomy (declarative→behavioural→delegated→agentic→systemic→regulatory), agentic mandate model three-tier hierarchy (HumanMandate→SystemMandate→AgentMandate) with pre-flight scope validation, ZKP integration points for 4 use cases, security layers (append-only enforcement + RLS + column masking + temporal auditability) |

#### Key Critical Risks (from Impact Analysis — need resolution before Phase 1 kickoff):
- 🔴 **Two-store vs one-store ambiguity** — spec recommends Neo4j as canonical store but DDL implementation is entirely Delta Lake; blocks infrastructure procurement and team skill assessment until resolved via POC benchmarks against actual data volumes
- 🟠 No initial seeding strategy documented (legacy relationships lacking digital evidence need migration runbook + exception handling)
- 🟡 API contract lacks non-functional requirements (rate limiting, pagination, circuit breakers — LOB consumers need this before Phase 2 integration work begins)

#### Palantir + Industry Research (2026-05-22):
- Expanded `palantir-ontology-analysis.md` with full industry comparison (Palantir/Stardog/Neo4j/GTB)
- Key finding: our Kinetic Layer (Section 9) aligns with industry leaders on noun+verb integration
- Gaps identified: inherited security, formal consistency checking, property chain inference
- Stardog's BCBS-239 compliance focus validates our regulatory-first approach
- Four-platform comparison matrix shows GTB strong on governance/kinetics, needs work on reasoning/security

#### Artifacts Directory Structure:
```
artifacts/dimensions/                    ← per-dimension specs/research/diagrams
├── 01-logical-model/
│   ├── specs/canonical-graph-spec.md          (697 lines, ~32K — full Architecture spec)
│   ├── research/entity-catalog.md             (~17.7K — all 4 product lines mapped)
│   ├── research/relationship-scenarios.md     (~17.2K — 7 validated workflows)
│   └── diagrams/                              (5 .mmd + 5 .png)
│       ├── entity-taxonomy.{mmd,png}
│       ├── relationship-lifecycle.{mmd,png}
│       ├── product-hierarchy.{mmd,png}
│       ├── dual-containment.{mmd,png}
│       └── cross-product-view.{mmd,png}
├── 02-materialization-strategy/research/impact-analysis.md (~16K architectural impact analysis)
├── 03-platform-infrastructure/specs/
│   ├── ddl-readme.md                          (DDL execution order + Unity Catalog mapping)
│   ├── infrastructure-architecture.md         (two-store vs consolidated comparison)
│   └── platform-topology.md                   (component topology + network zones)
└── 05-governance-trust-layer/specs/stakeholder-engagement.md

artifacts/research/txnbankingdatamodel/    ← source research directory (original uncommitted files, still present as reference)
```

## Completed Projects
_(none yet)_

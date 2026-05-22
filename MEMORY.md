# MEMORY.md — Data Architect Agent Memory Index

## Active Projects

### Global Transaction Banking Platform (2026-05-20 → ongoing)
- **Reference Client:** Nexus Global (Maya's client) — all ontology examples now grounded in this reality
- **Client:** Daniel Maly | Top 10 North American bank
- **Status:** Architecture recovered from git history + research artifacts post-restart wipe. All five dimensions rebuilt with full content from discovery notes, Architectural Impact Analysis (~32KB spec), and DDL definitions.

#### Five Architecture Dimensions (Memory Files)
| # | File | Bytes | Status |
|---|------|-------|--------|
| 01 | `memory/dimensions/01-logical-model.md` | ~7K | ✅ Refocused 2026-05-22 — all examples mapped to Nexus Global (Maya's client). Added VendorSystem node type + [VENDOR-HOSTED] constraint for Trade Finance (PROD-TF-001) + Supply Chain Finance (PROD-SCF-001). Entity catalog (20K, 6 product areas), relationship scenarios (22K, 9 workflows incl. 2 vendor), 5 Mermaid diagrams + PNGs updated, Maya product codes (PROD-003/004/010), cash pool config (USA-East 35.5%, Canada 23.2%) |
| 02 | `memory/dimensions/02-materialization-strategy.md` | ~3.3K | ✅ Greenfield rewrite 2026-05-22 — Delta Lake only (no Neo4j) + Azure Cache for Redis hot cache, kinetic layer 9 tables (interfaces, action_types, action_instances, function_definitions, business_rules, proposed_edges, review_queue, compensating_actions), containment zone 3 tables (vendor_systems, containment_zone_raw, vendor_mapping_status) in separate tb_containment catalog, 4 new pipelines (action execution, function evaluation, proposed→active promotion, vendor ingestion), Nexus Global volume estimates (~28K nodes / ~62K edges Y1, ~1GB storage) |
| 03 | `memory/dimensions/03-platform-infrastructure.md` | ~5.0K | ✅ Updated 2026-05-22 — Three-tier architecture committed (Neo4j + PostgreSQL + Delta Lake + Redis). PostgreSQL chosen over QLDB for proof registry (co-located with kinetic, team familiarity, Azure-native). Databricks on Azure locked as analytical layer. Unity Catalog topology + 31-step DDL execution order. RLS via domain_scope ARRAY\<STRING\>. |
| 04 | `memory/dimensions/04-api-integration-contract.md` | ~4.6K | ✅ Reworked 2026-05-22 — Ontology action surface (supersedes REST CRUD). 7 action endpoints, 6 function endpoints, interface resolution, containment zone API. Full NFRs: latency targets, rate limiting, cursor pagination, circuit breaker, idempotency, error taxonomy. Nexus Global examples. |
| 05 | `memory/dimensions/05-governance-trust-layer.md` | ~7.1K | ✅ Rebuilt — Proof registry design (append-only event-sourced with SHA-256 hash chaining), proof type taxonomy (declarative→behavioural→delegated→agentic→systemic→regulatory), agentic mandate model three-tier hierarchy (HumanMandate→SystemMandate→AgentMandate) with pre-flight scope validation, ZKP integration points for 4 use cases, security layers (append-only enforcement + RLS + column masking + temporal auditability) |

#### Key Critical Risks (updated 2026-05-22):
- 🟠 **Cross-store transaction consistency** — Saga pattern designed (Dim 02 §6); implementation needed before Phase 1
- 🔴 **[VENDOR-HOSTED] Trade Finance + Supply Chain Finance** — both product lines are vendor-hosted; requires vendor API contract review, containment zone schema definition, and progressive mapping strategy; blocks vendor integration work
- 🟠 No initial seeding strategy documented (legacy relationships lacking digital evidence need migration runbook + exception handling)
- ✅ **API contract NFRs** — resolved in Dim 04 spec (rate limiting, pagination, circuit breakers, idempotency, error taxonomy)
- ✅ **Two-store vs one-store** — resolved: three-tier (Neo4j + PostgreSQL + Delta Lake + Redis) is committed direction
- ✅ **QLDB vs PostgreSQL** — resolved: PostgreSQL chosen for proof registry (co-located with kinetic layer, team familiarity, Azure-native)

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
│   ├── specs/canonical-graph-spec.md          (~1500 lines, ~40K — full spec + Nexus Global §14 + VendorSystem)
│   ├── research/entity-catalog.md             (~20K — all 6 product areas mapped incl. 2 vendor-hosted)
│   ├── research/relationship-scenarios.md     (~22K — 9 validated workflows incl. 2 vendor integration)
│   └── diagrams/                              (5 .mmd + 5 .png + puppeteer-config.json)
│       ├── entity-taxonomy.{mmd,png}
│       ├── relationship-lifecycle.{mmd,png}
│       ├── product-hierarchy.{mmd,png}
│       ├── dual-containment.{mmd,png}
│       └── cross-product-view.{mmd,png}
├── 02-materialization-strategy/
│   ├── specs/materialization-strategy.md    (~1102 lines, ~45K — greenfield rewrite, Delta Lake + Redis, kinetic tables, containment zone, pipelines, volume estimates)
│   ├── diagrams/pipeline-data-flow.png      (rendered pipeline architecture diagram)
│   └── research/impact-analysis.md          (~16K architectural impact analysis)
├── 03-platform-infrastructure/specs/
│   ├── ddl-readme.md                          (DDL execution order + Unity Catalog mapping)
│   ├── infrastructure-architecture.md         (three-store architecture + QLDB vs PostgreSQL decision)
│   └── platform-topology.md                   (component topology + network zones)
├── 04-api-integration-contract/specs/
│   └── entity-platform-api.md                 (~18.5KB — ontology action surface, NFRs, Nexus Global examples)
└── 05-governance-trust-layer/specs/stakeholder-engagement.md

artifacts/research/txnbankingdatamodel/    ← source research directory (original uncommitted files, still present as reference)
```

## Completed Projects
_(none yet)_

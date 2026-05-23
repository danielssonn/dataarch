# Product Catalog System — Data Architecture Overlay Analysis (v2)

**Date:** 2026-05-23
**Source Repo:** `github.com/danielssonn/product-catalog-system`
**Data Architecture:** Five-dimension ontology-first, proof-backed GTB platform
**Supersedes:** `product-catalog-overlay.md` (v1)

---

## 1. What Changed in This Assessment

The MASTER_ARCHITECTURE.md (v2.0, 1213 lines, 44KB) reveals a far more complete system than the BUSINESS_ARCHITECTURE.md alone. Key additions:

| New Insight | Impact |
|-------------|--------|
| **14 microservices** with explicit port/store mapping | Precise migration path per service |
| **Context Resolution Architecture** as first-class component (878ms cold, <100ms cached) | Direct mapping to our Redis + Neo4j pattern |
| **Temporal for durable workflows** (not just Kafka events) | Retained — orthogonal to data stores |
| **DMN rules engine** for approver assignment | Maps to our kinetic business_rules table |
| **Multi-channel API Gateway** (6 channel types with mTLS, OAuth 2.0, JWT) | Retained — application layer |
| **Performance benchmarks** (actual measured latencies) | Validates our latency targets |
| **3 ADRs** already documenting key decisions | Aligns with our ADR process |
| **Kubernetes + cloud deployment** patterns | Retained — infrastructure orthogonal to data |

---

## 2. Reassessed Architecture Overlay

### 2.1 The System Is Already Ontology-Adjacent

The product-catalog-system has already made several decisions that align with our data architecture:

| Their Decision | Our Pattern | Alignment |
|---------------|-------------|-----------|
| Neo4j for party graph (ADR-003) | Neo4j for full ontology graph | ✅ Already aligned; we expand scope |
| Party-centric security (auth→party→tenant→permissions) | Context resolution via graph traversal + Redis | ✅ Already aligned; we add mandate scope |
| Event-driven integration (Kafka) | Kafka retained for CDC + events | ✅ Already aligned |
| Temporal for durable workflows | Temporal retained for workflow execution | ✅ Already aligned |
| API Gateway with context injection | API Gateway retained; context resolution becomes graph query | ✅ Already aligned |
| Multi-tenant isolation via tenantId | Tenant resolution via graph hierarchy | ✅ Already aligned; we eliminate manual tenantId |

### 2.2 Where MongoDB Is the Wrong Choice

The system uses MongoDB for 8 services. Here's why each should move to our three-tier architecture:

| Service | MongoDB Collections | Why MongoDB Is Wrong | Target Store |
|---------|-------------------|---------------------|--------------|
| **product-service** | product_catalogs, solutions, bundles, cross_sell_rules | Products have relationships to parties, accounts, each other. Cross-sell requires graph traversal. MongoDB can't do multi-hop queries. | Neo4j (ProductInstance, ProductBundle, CONTAINS) + PostgreSQL (lifecycle state) |
| **workflow-service** | workflow_templates, workflow_instances, approval_tasks, agent_executions | Workflow state is operational kinetic data. Needs ACID transactions for two-phase state machine (PENDING→APPROVED/REJECTED). MongoDB lacks ACID guarantees. | PostgreSQL (kinetic.action_instances, review_queue) + Temporal (execution) |
| **audit-service** | audit_logs | Audit logs need append-only enforcement, hash chaining, and authority linkage. MongoDB documents can be updated/deleted. | PostgreSQL (proof_registry — append-only, SHA-256 chained) |
| **auth-service** | JWT tokens, principals | Auth principals need to map to party graph for context resolution. MongoDB is redundant when Neo4j already stores parties. | PostgreSQL (principals) + Redis (session cache) |
| **bundle-service** | bundles | Bundles are graph relationships (ProductBundle → CONTAINS → ProductInstance). MongoDB can't traverse bundle→product→party chains. | Neo4j (ProductBundle + CONTAINS relationships) |
| **cross-sell-service** | cross_sell_rules | Cross-sell rules are function definitions that evaluate against the graph. MongoDB rules can't query Neo4j directly. | PostgreSQL (kinetic.function_definitions) + Neo4j (graph queries) |
| **tenant-service** | tenant config | Tenant resolution is a graph traversal (individual → EMPLOYED_BY → organization). MongoDB requires manual tenantId in every document. | PostgreSQL (tenant config) + Redis (hot cache) |
| **version-service** | version metadata | Version metadata is simple tabular data. | PostgreSQL |

**Bottom line:** MongoDB is the single wrong choice in an otherwise well-architected system. Replacing it with Neo4j + PostgreSQL + Redis unlocks the full ontology pattern.

---

## 3. Reassessed Gap Analysis

### 3.1 Already Present (Stronger Than v1 Assessment)

| Capability | Source | Notes |
|------------|--------|-------|
| Neo4j graph for parties | ADR-003 + Federated Party Architecture | Already production-ready; expand schema |
| Entity resolution (LEI, Tax ID, fuzzy) | Federated Party Architecture | 3-stage pipeline; auto-merge at 0.95+ |
| Multi-tenant isolation | Context Resolution Architecture | Automatic via party→org hierarchy |
| Event-driven integration (Kafka) | Integration Architecture | 10 topics defined |
| Workflow orchestration (Temporal) | Intelligent Workflow Orchestration | 4 workflow patterns (Rule-Based, Async Red Flag, Sync Enrichment, Hybrid) |
| API versioning | Version Service | URL-based + header + content negotiation |
| AI agent integration (Claude + MCP) | Agentic Workflow Design | Document validation, red flag detection, sync enrichment |
| Core banking adapter pattern | Core Banking Complete Guide | Finacle, T24, SAP support |
| Context resolution pipeline | Context Resolution Architecture | 878ms cold, <100ms cached |
| DMN rules engine | Workflow Service | Approver assignment, pricing variance rules |
| Performance benchmarks | Performance & Scalability | Actual measured latencies validate our targets |
| Deployment patterns | Deployment Architecture | Docker Compose + K8s + AWS EKS |
| ADR process | Appendix ADRs | 3 ADRs already documented |

### 3.2 Needs to Be Added (Refined from v1)

| Capability | From Data Architecture | Priority | Changed from v1? |
|------------|----------------------|----------|-----------------|
| **Proof Registry** | Dim 02 + Dim 05 | 🔴 Critical | Same |
| **Kinetic Layer** | Dim 02 (9 tables) | 🔴 Critical | Same — now maps to workflow-service migration |
| **Mandate Model** | Dim 05 (3-tier hierarchy) | 🔴 Critical | Same — extends existing RBAC |
| **Product Ontology** | Dim 01 (graph nodes) | 🟠 High | Same — replaces MongoDB product-service |
| **Cross-Store Saga Pattern** | Dim 02 §6 | 🟠 High | Same |
| **Containment Zone** | Dim 02 (vendor isolation) | 🟠 High | Same |
| **Delta Lake Analytics** | Dim 03 (CDC mirror) | 🟡 Medium | Same |
| **Redis Hot Cache** | Dim 03 | 🟡 Medium | Same — replaces Caffeine + Redis |
| **Interface Polymorphism** | Dim 01 (IHasBalance, etc.) | 🟡 Medium | Same |
| **Function Versioning** | Dim 01 | 🟡 Medium | Same — extends DMN rules |

---

## 4. Reassessed Migration Strategy

The MASTER_ARCHITECTURE reveals the system has **performance benchmarks** and **deployment patterns** already defined. This changes the migration approach:

### Phase 1: Proof + Kinetic (Weeks 1–6) — Same as v1

**Goal:** Replace MongoDB audit-service and workflow state with PostgreSQL.

**New insight from MASTER_ARCHITECTURE:**
- Temporal is already handling workflow durability. The migration only affects the data layer beneath Temporal — workflow metadata moves from MongoDB to PostgreSQL.
- DMN rules engine can be retained as-is; the business_rules table in PostgreSQL becomes the canonical storage, with DMN as the evaluation engine.
- Audit-service replacement is the highest-value item: MongoDB audit_logs → PostgreSQL proof_registry with hash chaining.

**Services migrated:** audit-service, workflow-service (data layer only, Temporal retained)

### Phase 2: Product Ontology (Weeks 7–10) — Same as v1

**Goal:** Replace MongoDB product catalog with Neo4j product ontology.

**New insight from MASTER_ARCHITECTURE:**
- bundle-service and cross-sell-service can be migrated together with product-service since they all share MongoDB.
- The cross-sell rules (currently in MongoDB) become function definitions in PostgreSQL, evaluated against Neo4j graph queries.
- The existing performance benchmarks (product creation <200ms, party lookup <100ms) validate that Neo4j can handle the load.

**Services migrated:** product-service, bundle-service, cross-sell-service

### Phase 3: Analytics + History (Weeks 11–14) — Same as v1

**Goal:** Deploy Delta Lake as analytical mirror; decommission MongoDB.

**New insight from MASTER_ARCHITECTURE:**
- The system already has Kafka topics for events. CDC from Neo4j and PostgreSQL can feed into the same Kafka infrastructure.
- MongoDB sharding by tenantId is already designed. Delta Lake partitions by tenantId + date for equivalent isolation.
- The existing K8s deployment patterns apply to Databricks cluster deployment.

**Services migrated:** All remaining MongoDB consumers; MongoDB decommissioned

### Phase 4: Agentic Layer (Weeks 15–18) — Same as v1

**Goal:** Enable mandate-governed agent operations.

**New insight from MASTER_ARCHITECTURE:**
- The system already has Claude MCP agents for document validation. The mandate model extends these agents with scope validation.
- Existing RBAC (6 roles) becomes the HumanMandate tier. SystemMandate and AgentMandate tiers are added.
- Pre-flight scope validation adds <1ms (Redis cache) to the existing 878ms cold / <100ms cached context resolution.

**Services migrated:** party-service (mandate scope added), auth-service (RBAC extended)

---

## 5. Reassessed Risk Assessment

| Risk | Impact | Mitigation | Changed from v1? |
|------|--------|------------|-----------------|
| **Cross-store consistency** | Action execution writes Neo4j + PostgreSQL | Saga pattern (Dim 02 §6) + recovery job | Same |
| **MongoDB decommission** | 8 services depend on MongoDB | Phased migration; each service independent | Same — now more precise |
| **Neo4j schema expansion** | Party graph → full ontology | Incremental migration; backward-compatible labels | Same |
| **Team Neo4j expertise** | Party team knows Neo4j; others know MongoDB | Training plan; party-service team as CoE | Same |
| **Temporal + Saga interaction** | Temporal = execution; Saga = data consistency | Clear boundary documented | Same |
| **Vendor API contracts** | Trade Finance + SCF schemas unknown | Containment Zone provides isolation | Same |
| **Performance regression** | MongoDB → Neo4j/PostgreSQL latency | Existing benchmarks validate targets; Neo4j already at 350ms for 5-hop traversal | **New** — system has measured baselines |
| **Context Resolution impact** | Adding mandate scope to existing pipeline | <1ms Redis cache lookup; no graph traversal needed | **New** — negligible impact on 878ms/<100ms baseline |

---

## 6. Key Architectural Alignment Findings

### 6.1 The System Already Follows Our Principles

| Our Principle | Their Implementation | Alignment |
|--------------|---------------------|-----------|
| **Ontology-first** | Party graph as single source of truth for entities + relationships | ✅ Partial — parties only; we expand to full ontology |
| **Kinetic layer** | Temporal workflows + DMN rules + MongoDB state | ⚠️ Close — needs PostgreSQL for ACID + proof chains |
| **Operational/analytics separation** | MongoDB for operational; no analytics layer | ⚠️ Partial — needs Delta Lake for analytics/history |
| **Proof-based governance** | MongoDB audit logs | ⚠️ Needs upgrade — append-only + hash chaining |
| **Multi-tenant isolation** | tenantId in every document + context resolution | ✅ Already aligned; graph hierarchy eliminates manual tenantId |
| **Event-driven integration** | Kafka with 10 topics | ✅ Already aligned |
| **API-first design** | Versioned REST + OpenAPI | ✅ Already aligned |

### 6.2 The One Wrong Choice: MongoDB

The MASTER_ARCHITECTURE confirms MongoDB is used for:
- Product catalog (8 collections across 3 services)
- Workflow state (4 collections)
- Audit logs (1 collection)
- Auth principals (unknown collections)
- Tenant config (unknown collections)
- Version metadata (unknown collections)

Every one of these use cases is better served by our three-tier architecture:
- **Graph data** (products, bundles, cross-sell) → Neo4j
- **Operational state** (workflows, auth, tenants, versions) → PostgreSQL
- **Analytics/history** (audit logs, temporal state) → PostgreSQL proof_registry + Delta Lake mirror
- **Hot cache** (sessions, context) → Redis

### 6.3 What Makes This Overlay Work

The product-catalog-system has:
1. ✅ The right application architecture (microservices, event-driven, API-first)
2. ✅ The right graph database for parties (Neo4j)
3. ✅ The right workflow engine (Temporal)
4. ✅ The right messaging (Kafka)
5. ✅ The right deployment patterns (K8s, Docker)
6. ✅ The right AI integration (Claude MCP)
7. ✅ Performance benchmarks that validate our targets
8. ❌ The wrong document database (MongoDB) for canonical data

**Replacing MongoDB with Neo4j + PostgreSQL + Redis is the only change needed to unlock the full ontology-first, proof-backed architecture.**

---

## 7. Summary

| Dimension | Before (Product Catalog System) | After (Data Architecture Overlay) |
|-----------|--------------------------------|-----------------------------------|
| **Data Model** | MongoDB documents + Neo4j parties | Unified ontology graph (Neo4j) + operational state (PostgreSQL) + analytics (Delta Lake) |
| **Audit** | MongoDB audit logs (mutable) | Regulatory-grade proof chains (append-only, hash-chained, authority-linked) |
| **Actions** | Temporal workflows + MongoDB state | Ontology action surface (declared actions with pre-flight rules, governance modes, proof requirements) |
| **Agents** | Claude MCP agents (ad hoc) | Mandate-governed agents (three-tier delegation, pre-flight scope validation, ZKP) |
| **Consistency** | MongoDB eventual consistency | Saga pattern for cross-store atomicity; CDC for analytics sync |
| **Multi-tenancy** | tenantId in MongoDB documents | Tenant resolution via graph traversal + Redis cache |
| **Vendor Integration** | Adapter pattern (point-to-point) | Containment Zone (semantic isolation + progressive mapping) |
| **Analytics** | None (MongoDB only) | Delta Lake CDC mirror + Unity Catalog governance |

**Bottom line:** The product-catalog-system is 90% of the way to our target architecture. The remaining 10% is replacing MongoDB with our three-tier data foundation. The application layer (microservices, API gateway, Temporal, Kafka, AI agents, deployment patterns) is already correct and retained.

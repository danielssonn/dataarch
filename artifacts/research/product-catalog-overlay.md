# Product Catalog System — Data Architecture Overlay Analysis

**Date:** 2026-05-23
**Source Repo:** `github.com/danielssonn/product-catalog-system`
**Data Architecture:** Five-dimension ontology-first, proof-backed GTB platform

---

## 1. What This System Is

The product-catalog-system is the **application-layer implementation** that the data architecture enables. It is a multi-tenant transaction banking platform with three core capabilities:

| Capability | Description | Current Implementation |
|------------|-------------|----------------------|
| **Product Catalog Management** | Design, configure, approve, and launch banking products across tenants/channels | MongoDB + Spring Boot microservices |
| **Federated Party Management** | Unified graph-based view of all parties across Commercial Banking + Capital Markets | Neo4j + entity resolution engine |
| **Intelligent Workflow Orchestration** | Hybrid human-AI approval workflows with document validation | Temporal + DMN + Claude agents |

**Key finding:** The system already has the right application architecture (microservices, event-driven, Neo4j for parties, multi-tenant). The data architecture we've designed becomes its **foundational data layer** — replacing MongoDB for canonical data, adding the proof registry, and providing the kinetic layer that makes the ontology actionable.

---

## 2. Architecture Overlay: Current vs. Target

### 2.1 Current Data Stores (Product Catalog System)

| Store | Role | Used By |
|-------|------|---------|
| **MongoDB** | Product catalog, workflows, audit logs, tenant config, auth | Product Service, Workflow Service, Auth Service, Bundle Service, Cross-Sell Service, Audit Service, Tenant Service, Version Service |
| **Neo4j** | Party graph (entities + relationships + provenance) | Party Service, Context Resolution |
| **PostgreSQL** | Source systems only (Commercial Banking, Capital Markets) | Source party services |
| **Temporal** | Durable workflow execution | Workflow Service |
| **Kafka** | Event-driven integration | All services |

### 2.2 Target Data Stores (After Overlay)

| Store | Role | Replaces |
|-------|------|----------|
| **Neo4j** | Operational graph — parties + products + relationships + vendor systems | Same Neo4j, but expanded scope (not just parties) |
| **PostgreSQL** | Kinetic layer (9 tables) + Proof Registry (2 tables) + Mandates (1 table) | Replaces MongoDB for canonical operational data |
| **Delta Lake** | Analytics + temporal history + LOB projections | Replaces MongoDB for historical/analytical queries |
| **Azure Cache for Redis** | Hot cache — entitlements, mandates, context resolution | Replaces application-level caching |
| **Temporal** | Workflow execution | Retained — orthogonal to data stores |
| **Kafka** | Event-driven integration | Retained — orthogonal to data stores |

### 2.3 What Changes

| Current | Target | Rationale |
|---------|--------|-----------|
| MongoDB for product catalog | Neo4j (Product node types) + PostgreSQL (kinetic state) | Products are ontology entities with relationships to parties, accounts, and each other. Graph traversal enables cross-sell, bundling, and eligibility queries. |
| MongoDB for workflows | PostgreSQL (action_instances) + Temporal (execution) | Workflow state is operational kinetic data. Action instances are saga-coordinated writes. |
| MongoDB for audit logs | PostgreSQL Proof Registry (append-only, hash-chained) | Operational audit logs → regulatory-grade evidentiary chains. |
| MongoDB for tenant config | Redis (hot cache) + PostgreSQL (canonical) | Tenant resolution is <100ms path. Cache for reads, PostgreSQL for writes. |
| Neo4j for parties only | Neo4j for full ontology graph | Parties are just one node type. Add Product, Account, Relationship, VendorSystem, Mandate. |

---

## 3. Domain Mapping: Product Catalog → Ontology Dimensions

### 3.1 Product Catalog Domain

The product catalog system's domain model maps directly to our ontology:

```
Product Catalog System                    Ontology (Dim 01)
────────────────────────                  ──────────────────
ProductCatalog (template)         →       ProductType (node type)
    └─ Pricing Template              └─ pricing_rules (property group)
    └─ Configuration Options         └─ configurable_properties (schema)
    └─ Catalog Terms                 └─ terms_and_conditions (linked document)
    └─ Product Category              └─ product_category (property)
                                        ↓
Solution (tenant instance)        →       ProductInstance (node type)
    └─ Custom Pricing                └─ pricing (computed from template + tenant override)
    └─ Custom Features               └─ features (subset of configurable_properties)
    └─ Approval Status               └─ lifecycle_status (kinetic property)
    └─ Workflow Metadata             └─ action_instances (linked via proof chain)
                                        ↓
Bundle                            →       ProductBundle (node type)
                                        └─ CONTAINS relationship → ProductInstance
CrossSellRule                     →       CrossSellRule (Function definition)
                                        └─ computeProductEligibility (Dim 01 §9.4)
```

**Key insight:** The ProductCatalog→Solution template-instantiation pattern is already an ontology pattern. The template declares what's configurable; the solution is the tenant-specific materialization. This maps cleanly to our interface-based polymorphism — `IHasPricing`, `IIsBundleMember`, `IIsCrossSellTarget`.

### 3.2 Party Domain

Already aligned. The product catalog system's Federated Party Architecture uses Neo4j with:
- **Node types:** Organization, LegalEntity, Individual, SourceRecord
- **Relationships:** PARENT_OF, BENEFICIAL_OWNER_OF, OPERATES_ON_BEHALF_OF, PROVIDES_SERVICES_TO, DUPLICATES, SOURCED_FROM

Our ontology (Dim 01) extends this with:
- **Additional node types:** Account, ProductInstance, VendorSystem, Mandate
- **Additional relationships:** HAS_ACCOUNT, SUBSCRIBED_TO, VENDOR_HOSTED, AUTHORIZED_BY
- **Proof chains:** Every relationship gets an append-only proof chain (PostgreSQL)
- **Kinetic state:** Relationships have lifecycle state (PROPOSED → REVIEWED → ACTIVE) managed by the kinetic layer

### 3.3 Workflow Domain

The product catalog system's workflow patterns map to our ontology action surface:

```
Product Catalog System                    Ontology (Dim 01 + Dim 04)
────────────────────────                  ──────────────────
Workflow Template                 →       Action Type (declared in ontology)
    └─ Decision Rules (DMN)          └─ business_rules (kinetic table)
    └─ Approver Assignment           └─ mandate scope validation
    └─ Agent Configuration           └─ function_definitions (kinetic table)
    └─ SLA & Escalation              └─ governance_mode (IMMEDIATE/PROPOSED/REVIEWED)
                                        ↓
Workflow Instance                 →       Action Instance (kinetic.action_instances)
    └─ Validation Results            └─ function evaluation results
    └─ Approval Tasks                └─ review_queue (kinetic table)
    └─ Audit Trail                   └─ proof_chain (PostgreSQL proof registry)
    └─ Status                        └─ lifecycle_status (saga state)
```

**Key insight:** The workflow service's Temporal orchestration is retained. What changes is the data layer beneath it — workflow state moves from MongoDB to PostgreSQL (kinetic layer), and audit trails become proof chains with hash chaining.

### 3.4 Context Resolution Domain

The product catalog system's Context Resolution architecture maps directly to our Redis + PostgreSQL pattern:

```
Product Catalog System                    Ontology (Dim 02 + Dim 03)
────────────────────────                  ──────────────────
Principal → Party (Neo4j)         →       Same Neo4j graph traversal
Tenant Resolution (org hierarchy) →       Same graph traversal + Redis cache
Permission Enrichment             →       Mandate validation (PostgreSQL + Redis)
Context Caching (5-min TTL)       →       Azure Cache for Redis (write-through invalidation)
```

**Latency alignment:** The product catalog system achieves <100ms cached context resolution. Our Redis layer targets <1ms for mandate validation. The graph traversal for party lookup remains Neo4j (<5ms p99).

---

## 4. Microservice Mapping: Before and After

### 4.1 Service-to-Store Mapping

| Service | Current Store | Target Store | Migration Path |
|---------|--------------|--------------|----------------|
| **product-service** | MongoDB | Neo4j (ProductInstance) + PostgreSQL (kinetic) | Migrate product templates to Neo4j; solution instances + lifecycle state to PostgreSQL |
| **party-service** | Neo4j | Neo4j (expanded) | No migration needed; expand schema with additional node types |
| **workflow-service** | MongoDB + Temporal | PostgreSQL (action_instances) + Temporal | Migrate workflow state to PostgreSQL; retain Temporal for execution |
| **audit-service** | MongoDB | PostgreSQL (proof_registry) | Migrate audit logs to append-only proof registry with hash chaining |
| **tenant-service** | MongoDB | Redis + PostgreSQL | Tenant config to PostgreSQL; hot reads from Redis |
| **bundle-service** | MongoDB | Neo4j (ProductBundle + CONTAINS) | Migrate bundles to graph relationships |
| **cross-sell-service** | MongoDB | PostgreSQL (function_definitions) + Neo4j (queries) | Rules become function definitions; recommendations use graph traversal |
| **auth-service** | MongoDB | PostgreSQL + Redis | Auth principals to PostgreSQL; session cache in Redis |
| **version-service** | MongoDB | PostgreSQL | Version metadata to PostgreSQL |

### 4.2 Retained Components

| Component | Role | Why Retained |
|-----------|------|-------------|
| **Temporal** | Durable workflow execution | Orthogonal to data stores; provides workflow durability, retries, sagas |
| **Kafka** | Event-driven integration | Orthogonal to data stores; enables CDC-like event publishing |
| **API Gateway** | Request routing, context injection | Application layer; no change needed |
| **Spring Boot services** | Business logic | Retained; data access layer changes from MongoDB to Neo4j/PostgreSQL |
| **Angular frontend** | UI | No change; consumes APIs, not data stores directly |

---

## 5. Gap Analysis: What the Product Catalog System Needs

### 5.1 Already Present ✅

| Capability | Source |
|------------|--------|
| Neo4j graph for parties | Federated Party Architecture |
| Entity resolution (LEI, Tax ID, fuzzy matching) | Federated Party Architecture §Entity Resolution |
| Multi-tenant isolation | Tenant Service + Context Resolution |
| Event-driven integration (Kafka) | Integration Architecture |
| Workflow orchestration (Temporal) | Workflow Service |
| API versioning | Version Service |
| AI agent integration (Claude + MCP) | Agentic Workflow Design |
| Core banking adapter pattern | Core Banking Complete Guide |
| Context resolution pipeline | Context Resolution Architecture |

### 5.2 Needs to Be Added 🔧

| Capability | From Data Architecture | Priority |
|------------|----------------------|----------|
| **Proof Registry** | Dim 02 + Dim 05 — append-only, hash-chained proof records | 🔴 Critical — replaces audit-service |
| **Kinetic Layer** | Dim 02 — 9 operational tables for action state machine | 🔴 Critical — replaces MongoDB workflow state |
| **Mandate Model** | Dim 05 — three-tier hierarchy (Human→System→Agent) | 🔴 Critical — enables agentic operations |
| **Product Ontology** | Dim 01 — ProductType, ProductInstance, ProductBundle as graph nodes | 🟠 High — replaces MongoDB product catalog |
| **Cross-Store Saga Pattern** | Dim 02 §6 — Neo4j+PostgreSQL transaction consistency | 🟠 High — needed before action execution |
| **Containment Zone** | Dim 02 — vendor system isolation + progressive mapping | 🟠 High — needed for Trade Finance + SCF |
| **Delta Lake Analytics** | Dim 03 — CDC-synced historical mirror | 🟡 Medium — Phase 2+ |
| **Redis Hot Cache** | Dim 03 — mandate validation, entitlements, context | 🟡 Medium — replaces app-level caching |
| **Interface Polymorphism** | Dim 01 — IHasBalance, IIsSettlementTarget, etc. | 🟡 Medium — enables cross-type queries |
| **Function Versioning** | Dim 01 — named, versioned business logic | 🟡 Medium — tracks rule evolution |

---

## 6. Migration Strategy

### Phase 1: Proof + Kinetic (Weeks 1–6)

**Goal:** Replace MongoDB audit-service and workflow state with PostgreSQL proof registry + kinetic layer.

1. Deploy PostgreSQL with proof_registry and kinetic schemas (Dim 02 DDL)
2. Migrate audit-service data → proof_registry (append-only, hash-chain seeded)
3. Migrate workflow state → kinetic.action_instances
4. Update workflow-service to write to PostgreSQL instead of MongoDB
5. Implement cross-store saga pattern (Dim 02 §6)
6. Deploy Redis for mandate/entitlement caching

**Services affected:** audit-service, workflow-service

### Phase 2: Product Ontology (Weeks 7–10)

**Goal:** Replace MongoDB product catalog with Neo4j product ontology + PostgreSQL kinetic state.

1. Define ProductType, ProductInstance, ProductBundle node types in Neo4j schema
2. Migrate product templates → Neo4j ProductType nodes
3. Migrate solution instances → Neo4j ProductInstance nodes + PostgreSQL kinetic state
4. Migrate bundles → Neo4j CONTAINS relationships
5. Update product-service to query Neo4j instead of MongoDB
6. Implement interface polymorphism (IHasPricing, IIsBundleMember)

**Services affected:** product-service, bundle-service, cross-sell-service

### Phase 3: Analytics + History (Weeks 11–14)

**Goal:** Deploy Delta Lake as analytical mirror; decommission MongoDB.

1. Deploy Databricks + Delta Lake + Unity Catalog
2. Configure CDC from Neo4j (APOC triggers → Kafka → Databricks)
3. Configure CDC from PostgreSQL (Debezium → Kafka → Databricks)
4. Deploy LOB projections (CB, CM, Wealth)
5. Migrate historical queries from MongoDB → Delta Lake
6. Decommission MongoDB

**Services affected:** All services with historical query paths

### Phase 4: Agentic Layer (Weeks 15–18)

**Goal:** Enable mandate-governed agent operations.

1. Deploy mandate model (three-tier hierarchy) in PostgreSQL
2. Implement pre-flight scope validation (<1ms via Redis cache)
3. Integrate scope violation detection + auto-suspend
4. Deploy ZKP integration points (Phase 4 use cases)
5. Update context resolution to include mandate scope

**Services affected:** party-service, workflow-service, auth-service

---

## 7. Risk Assessment

| Risk | Impact on Product Catalog System | Mitigation |
|------|----------------------------------|------------|
| **Cross-store consistency** | Action execution writes to both Neo4j (graph) and PostgreSQL (kinetic) | Saga pattern (Dim 02 §6) + recovery job |
| **MongoDB decommission** | 8 services currently depend on MongoDB | Phased migration; each service migrated independently |
| **Neo4j schema expansion** | Party graph expands from 4 node types to 10+ | Incremental schema migration; backward-compatible labels |
| **Team Neo4j expertise** | Party team knows Neo4j; product team knows MongoDB | Training plan; start with party-service team as center of excellence |
| **Temporal + Saga interaction** | Temporal manages workflow durability; Saga manages cross-store consistency | Clear boundary: Temporal = execution, Saga = data consistency |
| **Vendor API contracts** | Trade Finance + SCF schemas unknown | Containment Zone provides isolation; progressive mapping lifts signal over time |

---

## 8. Summary: What the Overlay Achieves

| Dimension | Before (Product Catalog System) | After (Data Architecture Overlay) |
|-----------|--------------------------------|-----------------------------------|
| **Data Model** | MongoDB documents + Neo4j parties | Unified ontology graph (Neo4j) + operational state (PostgreSQL) + analytics (Delta Lake) |
| **Audit** | MongoDB audit logs | Regulatory-grade proof chains (append-only, hash-chained, authority-linked) |
| **Actions** | Temporal workflows + MongoDB state | Ontology action surface (declared actions with pre-flight rules, governance modes, proof requirements) |
| **Agents** | Claude MCP agents (ad hoc) | Mandate-governed agents (three-tier delegation, pre-flight scope validation, ZKP) |
| **Consistency** | MongoDB eventual consistency | Saga pattern for cross-store atomicity; CDC for analytics sync |
| **Multi-tenancy** | tenantId in MongoDB documents | Tenant resolution via graph traversal + Redis cache |
| **Vendor Integration** | Adapter pattern (point-to-point) | Containment Zone (semantic isolation + progressive mapping) |

**Bottom line:** The product catalog system has the right application architecture. The data architecture replaces its data foundation (MongoDB) with an ontology-first, proof-backed system that enables regulatory-grade governance while retaining all existing application capabilities.

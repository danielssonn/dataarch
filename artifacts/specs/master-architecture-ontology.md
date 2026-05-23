# Master Architecture Document
**Ontology-First Global Transaction Banking Platform**

Version: 3.1
Date: 2026-05-23
Status: Draft — ontology + kinetic alignment for Products & Parties

---

## Document Overview

This is the **master architecture document** for the Global Transaction Banking platform. It describes how the ontology-first, proof-backed data platform (five architectural dimensions) enables the application system.

Two fundamental business constructs drive the entire architecture:

1. **Products** (what we sell) — Product catalog management, configuration, bundling, cross-sell, lifecycle
2. **Parties** (who we sell to) — Federated party management, entity resolution, ownership chains, context resolution

Every service, every workflow, every API call ultimately resolves to these two constructs and their relationships in the canonical graph. The ontology layer defines them. The kinetic layer makes them operational. The API layer exposes them. The proof layer governs them.

Previous versions described a MongoDB-based architecture. This version replaces that foundation with a three-tier operational store (Neo4j + PostgreSQL + Redis) plus Delta Lake analytics, while retaining the correct application-layer decisions (microservices, Temporal, Kafka, API Gateway, AI agents).

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Principles](#architecture-principles)
3. [The Ontology Layer](#the-ontology-layer)
4. [The Kinetic Layer](#the-kinetic-layer)
5. [The API Layer](#the-api-layer)
6. [The Operational Store](#the-operational-store)
7. [The Analytics Layer](#the-analytics-layer)
8. [The Governance Layer](#the-governance-layer)
9. [Application Services](#application-services)
10. [Integration Architecture](#integration-architecture)
11. [Security Architecture](#security-architecture)
12. [Deployment Architecture](#deployment-architecture)
13. [Performance & Scalability](#performance--scalability)
14. [Service Catalog](#service-catalog)
15. [Architecture Decision Records](#architecture-decision-records)
16. [Glossary](#glossary)

---

## Executive Summary

The Global Transaction Banking platform delivers three core capabilities:

### Core Capabilities

1. **Product Catalog Management** — Multi-tenant product design, configuration, approval, and lifecycle management
2. **Federated Party Management** — Unified graph-based view of all parties across Commercial Banking, Cash Management, and Wealth Management
3. **Intelligent Workflow Orchestration** — Hybrid human-AI approval workflows with regulatory-grade evidentiary chains

### Differentiator

This platform is **ontology-first and proof-backed**. The canonical graph is not a data warehouse or a semantic layer — it is **the operational interface through which the bank acts on its data**. Every relationship has an append-only, hash-chained proof record. Every automated action has a complete, verifiable delegation chain back to a human with signing authority.

| Capability | Metric | Impact |
|------------|--------|--------|
| **Product Launch Speed** | 60% faster | Products live in days, not weeks |
| **Party Data Quality** | 75% fewer duplicates | Single customer view |
| **Approval Efficiency** | 50% faster cycles | AI pre-screening |
| **Security** | Zero cross-tenant leaks | Automatic tenant isolation |
| **Context Resolution** | <100ms (cached) | Seamless user experience |
| **Compliance Automation** | 95% automated checks | Reduced risk |
| **Proof Chain Integrity** | 100% of edges have valid chains | Regulatory examination readiness |
| **Agent Mandate Validation** | <1ms p99 | Safe agentic operations |

### Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      CLIENT APPLICATIONS                                 │
│         Web UI (Angular) │ Mobile │ API Clients │ Branch                 │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    API GATEWAY (Port 8080)                               │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │ JWT Auth     │→ │ Context          │→ │ Context Injection        │  │
│  │ Filter       │  │ Resolution       │  │ Filter                   │  │
│  └──────────────┘  └────────┬─────────┘  └────────┬─────────────────┘  │
│                             │                      │                    │
│  Injects: X-Processing-Context, X-Tenant-ID, X-Party-ID, X-Request-ID  │
└──────────────────────────────┼──────────────────────┼───────────────────┘
                               │                      │
            ┌──────────────────┼──────────────────────┼───────────────┐
            ▼                  ▼                      ▼               ▼
     ┌──────────────┐ ┌──────────────┐   ┌─────────────────┐ ┌────────────┐
     │ Auth Service │ │Party Service │   │  Business        │ │ Workflow   │
     │   (8084)     │ │   (8083)     │   │  Services        │ │   (8089)   │
     │              │ │              │   │                  │ │            │
     │ JWT +        │ │ Context      │   │ Product,         │ │ Temporal   │
     │ Principal    │ │ Resolution   │   │ Bundle,          │ │ + DMN +    │
     │ Mgmt         │ │ via Neo4j    │   │ Cross-Sell       │ │ Claude MCP │
     └──────────────┘ └──────────────┘   └─────────────────┘ └────────────┘
            │                  │                    │               │
            ▼                  ▼                    ▼               ▼
     ┌──────────────┐ ┌──────────────┐   ┌─────────────────┐ ┌────────────┐
     │  PostgreSQL  │ │    Neo4j     │   │    Neo4j        │ │ PostgreSQL │
     │  (Auth       │ │  (Party      │   │  (Product       │ │  (Kinetic  │
     │   Principals)│ │   Graph)     │   │   Ontology)     │ │   Layer)   │
     └──────────────┘ └──────────────┘   └─────────────────┘ └────────────┘
            │                  │                    │               │
            └──────────────────┴────────────────────┼───────────────┘
                                                    │
                                    ┌───────────────┼───────────────┐
                                    ▼               ▼               ▼
                              ┌──────────┐  ┌──────────────┐  ┌──────────┐
                              │   Redis  │  │  PostgreSQL  │  │ Delta    │
                              │ (Hot      │  │  (Proof      │  │  Lake    │
                              │  Cache)  │  │  Registry)   │  │  (Databr.│
                              └──────────┘  └──────────────┘  └──────────┘
```

---

## Architecture Principles

### 1. Ontology First

**Principle:** The canonical graph is the source of truth. Every system — CB, CM, Wealth, vendor platforms — consumes read-only projections from the ontology. No system writes to canonical data except through the Entity Platform API.

**Implementation:**
- Neo4j holds the operational graph (nodes, edges, current state)
- Entity Platform API is the sole write path
- LOB applications read from Delta Lake projections
- Materialization is always derived from the graph, never the other way around

### 2. Proof Is Mandatory

**Principle:** Every relationship in the graph has an append-only, hash-chained proof record. An edge without a proof chain is an unverified assertion and is architecturally invalid.

**Implementation:**
- PostgreSQL proof registry with append-only enforcement (triggers block UPDATE/DELETE)
- SHA-256 hash chaining between records (tamper-evident)
- Authority-linked: every proof captures who had the right to act, at what time, under what mandate
- Six proof types: declarative, behavioural, delegated, agentic, systemic, regulatory

### 3. Kinetic Layer — Noun + Verb Integration

**Principle:** The ontology declares not just what exists (entities, relationships) but what can be done (actions, functions). Actions are first-class ontology constructs with pre-flight rules, effects, and governance modes.

**Implementation:**
- Action Types declared in the ontology (7 defined: AssertRelationship, InitiatePayment, ExecuteFXForward, etc.)
- Functions declared in the ontology (6 defined: deriveEdgeState, validateMandateScope, computeProductEligibility, etc.)
- Interfaces enable polymorphic operations (IHasBalance, IIsSettlementTarget, IIsPoolMember)
- Kinetic layer tables in PostgreSQL store action instances, review queues, business rules, function definitions

### 4. Multi-Tenancy First

**Principle:** Every piece of data belongs to a tenant. Tenant isolation is automatic and enforced at all layers.

**Implementation:**
- Context Resolution: Tenant ID automatically resolved from party organization hierarchy (Neo4j graph traversal)
- Cache: Tenant context cached in Redis (<100ms)
- API: X-Tenant-ID header injected by gateway
- Storage: Row-Level Security via `domain_scope` (PostgreSQL), Unity Catalog governance (Delta Lake)

### 5. Party-Centric Security

**Principle:** Authentication identifies WHO (principal). Party Service resolves WHAT/WHERE (party, tenant, permissions, mandate scope).

**Implementation:**
- Auth Service: JWT token with principal ID
- Party Service: Maps principal → party → tenant → permissions via Neo4j graph traversal
- Context: Complete ProcessingContext propagated via HTTP headers
- Business Logic: Access context via ContextHolder

### 6. Agentic Mandate Governance

**Principle:** Every automated action has a complete, verifiable delegation chain back to a human with signing authority. Agents cannot act without a valid, non-expired mandate.

**Implementation:**
- Three-tier hierarchy: HumanMandate → SystemMandate → AgentMandate
- Pre-flight scope validation (<1ms via Redis cache)
- Scope violations auto-suspend the mandate and alert the human owner
- Proof chain records mandate state at time of action

### 7. Event-Driven Integration

**Principle:** Services communicate via events (Kafka), not direct calls (except for context resolution and synchronous action execution).

**Implementation:**
- Product changes → `solution.configured` event
- Workflow approvals → `workflow.approved` event
- Party changes → `party.changed` event
- Cross-service coordination via event choreography

### 8. Operational/Analytics Separation

**Principle:** Operational stores (Neo4j, PostgreSQL, Redis) serve real-time queries. Delta Lake serves analytical and historical queries. Delta Lake is a lagging mirror (<5s CDC sync) — never the source of truth for current state.

**Implementation:**
- Neo4j: graph traversal <5ms p99
- PostgreSQL: kinetic state + proof registry with ACID semantics
- Redis: hot cache <1ms
- Delta Lake: CDC-synced mirror for analytics, temporal history, regulatory reporting

---

## The Ontology Layer

The ontology is the conceptual model that drives everything below it. It defines the nouns (entities), the relationships (edges), the verbs (actions), and the logic (functions).

### Node Types

```
Node
├── Party
│   ├── LegalEntity (Corporation, Partnership, Trust, Sovereign)
│   ├── NaturalPerson
│   ├── FinancialInstitution
│   └── Regulator
├── EntityGroup (UltimateParent, ConsolidatedGroup)
├── Product (ProductDefinition, ProductInstance, ProductBundle)
├── Account (OperatingAccount, VirtualAccount, NotionalPool, PhysicalPool, TradingAccount, CustodyAccount)
├── Transaction (Payment, TradeTransaction, FXTransaction, Fee, InterestPosting, SweepTransaction, Reversal)
├── Channel (DigitalPortal, APIChannel, H2HChannel, SWIFTChannel)
├── Obligation (RegulatoryObligation, ContractualObligation, CreditObligation, SettlementObligation)
├── Mandate (HumanMandate, AgentMandate)
└── VendorSystem (TradeFinanceSystem, SupplyChainFinanceSystem)
```

### Relationship Types

| Relationship | Example | Business Purpose |
|-------------|---------|-----------------|
| `isSubsidiaryOf` | Nexus Global USA → Nexus Global (Canada) | Corporate hierarchy |
| `beneficialOwnerOf` | John Doe (25%) → ABC Corp | UBO identification |
| `operatesOnBehalfOf` | Goldman Sachs → Microsoft Corp | Agency relationships |
| `providesServicesTo` | Commercial Banking → ABC Corp | Product relationships |
| `hasAccount` | Nexus Global USA → OperatingAccount | Account ownership |
| `subscribedTo` | Nexus Global USA → FX Forward | Product subscription |
| `authorizedBy` | AgentMandate → HumanMandate | Delegation chain |
| `vendorHosted` | Trade Finance → VendorSystem | Vendor containment |

### Interfaces (Polymorphism)

| Interface | Implemented By | Purpose |
|-----------|---------------|---------|
| `IHasBalance` | OperatingAccount, TradingAccount, CustodyAccount | Balance queries across account types |
| `IIsSettlementTarget` | OperatingAccount, TradingAccount, CustodyAccount | Payment initiation |
| `IIsPoolMember` | OperatingAccount, VirtualAccount | Cash pool sweeps |
| `IHasPricing` | ProductInstance | Pricing computation |
| `IIsBundleMember` | ProductInstance | Bundle composition |
| `IIsCrossSellTarget` | ProductInstance | Recommendation engine |
| `IIsKYCSubject` | LegalEntity, NaturalPerson | Compliance screening |
| `IIsMandateHolder` | NaturalPerson, FinancialInstitution | Authority validation |

### Action Types (Declared Operations)

Actions are grouped by domain. Each action is declared in the ontology with pre-flight rules, effects, and governance mode.

#### Party & Relationship Actions

| Action | Governance Mode | Description |
|--------|----------------|-------------|
| `AssertRelationship` | PROPOSED | New counterparty relationship requires compliance review |
| `ReviewRelationshipProposal` | IMMEDIATE | Approve/reject pending relationship assertions |
| `ApproveKYCRenewal` | IMMEDIATE | Compliance officer approval |

#### Product Lifecycle Actions

| Action | Governance Mode | Description |
|--------|----------------|-------------|
| `SubmitProductConfiguration` | IMMEDIATE | Submit product instance for approval |
| `ApproveProductConfiguration` | IMMEDIATE | Approver signs off; mandate-validated |
| `ActivateProduct` | IMMEDIATE | Product goes live; proof of activation recorded |
| `DeprecateProduct` | PROPOSED | Product retirement; requires compliance review |
| `ModifyProductPricing` | REVIEWED | Pricing change; executes immediately, async compliance review |

#### Transaction Actions

| Action | Governance Mode | Description |
|--------|----------------|-------------|
| `InitiatePayment` | IMMEDIATE | Time-critical; pre-flight sanctions check |
| `ExecuteFXForward` | IMMEDIATE | Market execution; mandate-governed |
| `DrawdownIntercompanyFacility` | REVIEWED | Executes immediately; async compliance review with compensating action |
| `InitiatePoolSweep` | IMMEDIATE | Intraday liquidity management |

### Functions (Versioned Business Logic)

Functions are versioned, stored in `kinetic.function_definitions`, and evaluated by the platform.

#### Party & Governance Functions

| Function | Purpose |
|----------|---------||
| `deriveEdgeState` | Derives current relationship state from proof chain replay |
| `validateMandateScope` | Pre-flight agent mandate validation (<1ms) |
| `computeSigningAuthority` | Tiered signing limits (solo/dual/board) |

#### Product Functions

| Function | Purpose |
|----------|---------|
| `computeProductEligibility` | KYC, sanctions, and product-specific checks for party-product fit |
| `computeProductPricing` | Pricing from template + tenant override + volume discount |
| `validateBundleComposition` | Bundle integrity check (no circular deps, pricing conflicts) |
| `computeCrossSellRecommendations` | Graph-based recommendations (co-adoption, category affinity) |

#### Transaction Functions

| Function | Purpose |
|----------|---------|
| `computePoolInterest` | Daily interest posting for cash pools |
| `validateTransferPricing` | Arm's-length pricing for intercompany transactions |

---

## The Kinetic Layer

The kinetic layer makes the ontology operational. It stores the state machines that govern how actions execute, how functions evaluate, and how the graph evolves.

### Kinetic Tables (PostgreSQL)

| Table | Purpose |
|-------|---------|
| `kinetic.interfaces` | Interface implementations (polymorphic mapping) |
| `kinetic.action_types` | Declared action definitions (pre-flight rules, effects, governance mode) |
| `kinetic.action_instances` | Action execution history (saga coordinator) |
| `kinetic.function_definitions` | Versioned function definitions |
| `kinetic.business_rules` | Pre-flight rules referenced by action types |
| `kinetic.proposed_edges` | Two-phase write: edges awaiting review |
| `kinetic.review_queue` | Ordered queue of items awaiting review |
| `kinetic.compensating_actions` | Compensation for REVIEWED governance mode failures |

### Proof Registry (PostgreSQL)

| Table | Purpose |
|-------|---------|
| `proof.proof_chains` | One per graph edge; tracks current state + integrity status |
| `proof.proof_records` | Append-only event-sourced records with SHA-256 hash chaining |

### Mandate State (PostgreSQL)

| Table | Purpose |
|-------|---------|
| `mandate.mandates` | Three-tier hierarchy (HumanMandate → SystemMandate → AgentMandate) |

### Cross-Store Saga Pattern

Action execution writes to both Neo4j (graph mutation) and PostgreSQL (proof + action instance). The Saga pattern guarantees consistency:

```
Phase 1: Pre-flight (read-only)
  ├── Evaluate business rules (PostgreSQL)
  ├── Check mandate scope (PostgreSQL + Redis)
  ├── Read graph state (Neo4j — read-only)
  └── If any rule fails → reject, log action_instances (status=BLOCKED)

Phase 2: Forward Operations (write)
  ├── Write action_instances (status=PENDING) → PostgreSQL
  ├── Create proof chain + proof record → PostgreSQL
  ├── Apply graph mutations → Neo4j
  └── Update action_instances (status=COMPLETED) → PostgreSQL

Phase 3: Compensation (if graph write fails)
  ├── Undo graph mutations → Neo4j
  ├── Append PROOF_INVALIDATED to proof chain → PostgreSQL
  └── Update action_instances (status=COMPENSATED) → PostgreSQL
```

A recovery job (every 30s) checks orphaned saga instances and reconciles Neo4j vs PostgreSQL state.

---

## The API Layer

The Entity Platform API is **the sole interface** to the canonical graph. It is not a CRUD REST API — it is an **ontology action surface**.

### Core Principles

1. **Actions, not resources.** Endpoints invoke declared ontology actions, not generic CRUD.
2. **Proof is mandatory.** Every write operation must include a proof payload.
3. **LEI as canonical identity.** Where a LegalEntity exists, LEI is the primary join key.
4. **Projections never write to canonical.** LOB consumers read from projections only.
5. **Temporal queries are first-class.** Every read endpoint supports `?asOf={timestamp}`.

### API Surface

#### Entity Resolution (Read)
```
GET  /entities/{id}                    — resolve by canonical UUID
GET  /entities/by-lei/{lei}            — resolve by LEI
```

#### Graph Traversal (Read)
```
GET  /entities/{id}/ownership-chain    — traverse to UltimateParent
GET  /entities/{id}/beneficial-owners  — UBO resolution
GET  /entities/{id}/regulatory-exposure — Party + Regulator edges
GET  /entities/{id}/relationships      — all edges from node
```

#### Ontology Actions (Write)
```
POST /actions/{actionType}             — execute declared action

Party & Relationship:
     /actions/assert-relationship
     /actions/review-relationship-proposal
     /actions/approve-kyc-renewal

Product Lifecycle:
     /actions/submit-product-configuration
     /actions/approve-product-configuration
     /actions/activate-product
     /actions/deprecate-product
     /actions/modify-product-pricing

Transactions:
     /actions/initiate-payment
     /actions/execute-fx-forward
     /actions/drawdown-intercompany-facility
     /actions/initiate-pool-sweep
```

#### Function Evaluation (Read/Compute)
```
POST /functions/{functionName}/evaluate

Party & Governance:
     /functions/derive-edge-state
     /functions/validate-mandate-scope
     /functions/compute-signing-authority

Product:
     /functions/compute-product-eligibility
     /functions/compute-product-pricing
     /functions/validate-bundle-composition
     /functions/compute-cross-sell-recommendations

Transaction:
     /functions/compute-pool-interest
     /functions/validate-transfer-pricing
```

#### Proof Chain Retrieval (Read)
```
GET  /proof-chains/{chainId}           — full chain with hash verification
GET  /proof-chains/{chainId}/verify    — verify chain integrity
```

#### Mandate Validation (Read)
```
GET  /mandates/{agentId}/validate      — pre-flight scope check (<1ms)
GET  /mandates/{agentId}/chain         — full delegation chain
```

#### Interface Resolution (Read)
```
GET  /interfaces/{name}                — all nodes implementing interface
GET  /interfaces/{name}/nodes/{id}     — check if node implements interface
```

#### Containment Zone (Vendor)
```
POST /containment/ingest               — ingest vendor data
GET  /containment/{vendorSystemId}     — query containment zone
POST /containment/map                  — progressive mapping to canonical terms
```

### Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Entity resolution by ID/LEI | <10ms p99 |
| Multi-hop graph traversal | <5ms p99 |
| Mandate pre-flight validation | <1ms p99 |
| Action execution (end-to-end) | <200ms p99 |
| Proof chain retrieval | <200ms p99 |
| Rate limiting | Configurable per endpoint; default 1000 req/min |
| Pagination | Cursor-based (not offset-based) |
| Idempotency | Idempotency-Key header for all POST endpoints |
| Circuit breaker | Per downstream store; 50% error rate → open for 30s |
| Error taxonomy | Standardized error codes (400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity, 429 Too Many Requests, 500 Internal Server Error, 503 Service Unavailable) |

---

## The Operational Store

### Neo4j — Graph Store (Operational Traversal)

| Concern | Detail |
|---------|--------|
| **Role** | Canonical graph persistence for real-time traversal |
| **Data** | All node types, all edge types, current state only |
| **Latency** | <5ms p99 for multi-hop queries |
| **Queries** | Entity resolution, ownership chains, beneficial ownership, regulatory exposure, interface resolution |
| **Indexes** | `federatedId` (unique), `lei` (unique), `status` (filtered), relationship types |
| **Key Queries** | Ownership chain (variable-length `[:isSubsidiaryOf*]`), UBO resolution (`[:beneficialOwnerOf*]`), regulatory exposure (`[:regulatoryExposure]`), interface lookup (`[:implements]`) |

### PostgreSQL — Kinetic Layer + Proof Registry + Mandates

| Concern | Detail |
|---------|--------|
| **Role** | Operational state for kinetic layer, proof registry, and mandate governance |
| **Data** | Kinetic tables (9), proof registry (2), mandate state (1) = 12 tables |
| **Latency** | <5ms p99 for kinetic queries; <1ms for mandate validation (via Redis cache) |
| **ACID** | Required for two-phase write state machine and saga coordination |
| **Append-only** | Proof records enforced via triggers (UPDATE/DELETE blocked) |
| **Hash chaining** | SHA-256 per record + `previousHash` forming tamper-evident linked list |

### Azure Cache for Redis — Hot Cache

| Concern | Detail |
|---------|--------|
| **Role** | Sub-millisecond cache for operational hot paths |
| **Data** | Entitlements, active mandates, interface implementations, context resolution results |
| **Latency** | <1ms |
| **Invalidation** | Write-through on state changes |
| **Never source of truth** | Always validated against PostgreSQL/Neo4j on cache miss |

---

## The Analytics Layer

### Delta Lake (Databricks on Azure)

| Concern | Detail |
|---------|--------|
| **Role** | Analytics, temporal history, regulatory reporting, LOB projections |
| **Data** | CDC-synced mirror of Neo4j + PostgreSQL; containment zone; LOB projections |
| **Sync** | CDC from Neo4j (APOC triggers → Kafka → Databricks); CDC from PostgreSQL (Debezium → Kafka → Databricks) |
| **Latency** | <5s sync lag |
| **Governance** | Unity Catalog with `tb_canonical` (Channels Technology owned) + LOB catalogs |
| **Time-travel** | Point-in-time reconstruction via Delta Lake versioning |
| **Never source of truth** | Current state always read from operational stores |

### Containment Zone (Delta Lake)

| Concern | Detail |
|---------|--------|
| **Role** | Semantic buffer for vendor-hosted data |
| **Data** | Vendor data in native schema; progressive mapping status tracked |
| **Isolation** | Separate Unity Catalog (`tb_containment`) with separate governance |
| **Mapping** | `Partial` → `Complete` over time as vendor terms map to canonical ontology |

---

## The Governance Layer

### Proof Chain Integrity

- **Append-only enforcement** at storage layer (PostgreSQL triggers)
- **SHA-256 hash chaining** between records (tamper-evident)
- **15-minute integrity sweep** validates chain continuity
- **Current state derived from event replay** — never from a status field

### Agentic Mandate Model

- **Three-tier hierarchy:** HumanMandate → SystemMandate → AgentMandate
- **Complete delegation chain** required for every agent action
- **Pre-flight scope validation** blocks execution (<1ms via Redis)
- **Scope violations** auto-suspend the mandate and alert the human owner

### Zero-Knowledge Proofs (Phase 4)

| Claim | What Proven (public) | What Hidden |
|-------|---------------------|-------------|
| "Agent acted within mandate" | Action was in permitted scope | Full scope definition |
| "Entity not sanctioned" | Screening performed and passed | Which lists checked, PII |
| "Counterparty has valid KYC" | Completed, current, within policy | Documentation contents |
| "Ownership chain verified" | Each link has valid proof | Intermediate ownership % |

### Security Layers

1. **Append-only enforcement** at storage layer
2. **Row-Level Security** via `domain_scope` (enforced at SQL and API layers)
3. **Column-level masking** on sensitive proof fields (auditor-only visibility)
4. **Temporal auditability** — full point-in-time reconstruction

---

## Application Services

The application layer sits above the data platform. Two fundamental business constructs drive everything: **Products** (what we sell) and **Parties** (who we sell to). Every service, every workflow, every API call ultimately resolves to these two constructs and their relationships in the canonical graph.

### Service Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      CLIENT APPLICATIONS                                 │
│         Web UI (Angular) │ Mobile │ API Clients │ Branch                 │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    API GATEWAY (Port 8080)                               │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │ JWT Auth     │→ │ Context          │→ │ Context Injection        │  │
│  │ Filter       │  │ Resolution       │  │ Filter                   │  │
│  └──────────────┘  └────────┬─────────┘  └────────┬─────────────────┘  │
│                             │                      │                    │
│  Injects: X-Processing-Context, X-Tenant-ID, X-Party-ID, X-Request-ID  │
└──────────────────────────────┼──────────────────────┼───────────────────┘
                               │                      │
            ┌──────────────────┼──────────────────────┼───────────────┐
            ▼                  ▼                      ▼               ▼
     ┌──────────────┐ ┌──────────────┐   ┌─────────────────┐ ┌────────────┐
     │ Auth Service │ │Party Service │   │  Business        │ │ Workflow   │
     │   (8084)     │ │   (8083)     │   │  Services        │ │   (8089)   │
     │              │ │              │   │                  │ │            │
     │ JWT +        │ │ Context      │   │ Product,         │ │ Temporal   │
     │ Principal    │ │ Resolution   │   │ Bundle,          │ │ + DMN +    │
     │ Mgmt         │ │ via Neo4j    │   │ Cross-Sell       │ │ Claude MCP │
     └──────────────┘ └──────────────┘   └─────────────────┘ └────────────┘
            │                  │                    │               │
            ▼                  ▼                    ▼               ▼
     ┌──────────────┐ ┌──────────────┐   ┌─────────────────┐ ┌────────────┐
     │  PostgreSQL  │ │    Neo4j     │   │    Neo4j        │ │ PostgreSQL │
     │  (Auth       │ │  (Party      │   │  (Product       │ │  (Kinetic  │
     │   Principals)│ │   Graph)     │   │   Ontology)     │ │   Layer)   │
     └──────────────┘ └──────────────┘   └─────────────────┘ └────────────┘
```

---

### Federated Party Management

**Purpose:** Unified graph-based view of all parties across Commercial Banking, Cash Management, and Wealth Management. This is the WHO — every product subscription, every payment, every relationship traces back to a party.

#### Ontology Alignment

The party domain maps directly to the ontology node types and relationships:

```
Ontology Node Type          Party Service Implementation
─────────────────           ──────────────────────────────
Party                       Base label; all parties have this
├── LegalEntity             Organizations, corporations, partnerships
│   ├── Corporation         Standard business entity
│   ├── Partnership         Multi-party legal structure
│   ├── Trust               Fiduciary arrangement
│   └── Sovereign           Government entity
├── NaturalPerson           Individual humans (UBOs, signers, RMs)
├── FinancialInstitution    Banks, brokers, custodians
└── Regulator               OSFI, FCA, SEC, etc.

EntityGroup                 Consolidated views
├── UltimateParent          Top of ownership hierarchy
└── ConsolidatedGroup       Regulatory reporting boundary
```

**Relationship types that define the party graph:**

| Relationship | Direction | Business Purpose | Proof Chain Required |
|-------------|-----------|-----------------|---------------------|
| `isSubsidiaryOf` | Child → Parent | Corporate hierarchy | ✅ Yes — ownership evidence |
| `beneficialOwnerOf` | Person → Entity | UBO identification | ✅ Yes — beneficial ownership declaration |
| `operatesOnBehalfOf` | Agent → Principal | Agency relationships | ✅ Yes — power of attorney / mandate |
| `hasAccount` | Party → Account | Account ownership | ✅ Yes — account opening documentation |
| `subscribedTo` | Party → ProductInstance | Product subscription | ✅ Yes — signed agreement |
| `employs` | Organization → NaturalPerson | Employment relationship | ✅ Yes — HR record / contract |
| `regulatedBy` | Party → Regulator | Regulatory jurisdiction | ✅ Yes — regulatory filing |
| `authorizedBy` | AgentMandate → HumanMandate | Delegation chain | ✅ Yes — mandate documentation |

#### Entity Resolution Pipeline

Three-stage pipeline to detect, resolve, and merge party records:

```
Stage 1: Detection
  ├── Input: New party record from source system
  ├── Matching: LEI, Tax ID, D-U-N-S, fuzzy name matching
  └── Output: Candidate matches with confidence score

Stage 2: Resolution
  ├── Score ≥ 0.95 → Auto-merge to existing party
  ├── Score 0.70–0.94 → Flag for manual review (review_queue)
  └── Score < 0.70 → Create new party node

Stage 3: Enrichment
  ├── Add source system provenance (SOURCED_FROM relationship)
  ├── Add regulatory identifiers (LEI, Tax ID, D-U-N-S)
  └── Trigger context resolution cache invalidation
```

#### Federated Party Graph (Nexus Global Example)

```
Nexus Global (Canada) [LegalEntity:Corporation, LEI:254900XXXX]
  │
  ├─[:isSubsidiaryOf]──→ Nexus Global (UltimateParent)
  │
  ├─[:hasAccount]──→ OperatingAccount-USA [IHasBalance, IIsSettlementTarget]
  │
  ├─[:hasAccount]──→ OperatingAccount-CA [IHasBalance, IIsSettlementTarget]
  │
  ├─[:subscribedTo]──→ FX Forward PROD-003 [IHasPricing]
  │
  ├─[:subscribedTo]──→ Cash Management PROD-004 [IHasPricing]
  │
  ├─[:employs]──→ John Doe [NaturalPerson]
  │                  │
  │                  ├─[:beneficialOwnerOf]──→ ABC Corp [25%]
  │                  └─[:authorizedBy]──→ AgentMandate-001
  │
  └─[:regulatedBy]──→ OSFI [Regulator]
```

Every edge above has a corresponding proof chain in PostgreSQL. The `subscribedTo` edges, for example, have proof records capturing the signed product agreement, the actor who asserted it, their authority basis, and the hash chain linking to prior state.

#### Context Resolution Architecture

**Purpose:** Transform authentication (WHO) into complete processing context (WHAT/WHERE).

**Data Flow:**
```
JWT (principalId)
  → Party Service (Neo4j graph traversal: principal → party → tenant → permissions)
  → ProcessingContext (tenantId, partyId, permissions, relationships, mandate scope)
  → HTTP Headers (X-Processing-Context, X-Tenant-ID, X-Party-ID, X-Request-ID)
  → Request Scope
  → ContextHolder.getRequiredContext()
```

**Performance:**
- Cold start: ~900ms (Neo4j graph traversal + mandate scope resolution)
- Cached: <100ms (Redis cache, 5-minute TTL)
- Cache hit rate: 95%+ (typical)

**Key Changes from v2:**
- Context resolution now includes **mandate scope** (three-tier hierarchy)
- Cache moved from Caffeine (per-instance) to **Azure Cache for Redis** (shared)
- Tenant resolution via graph hierarchy eliminates manual `tenantId` in documents

---

### Product Catalog Management

**Purpose:** Multi-tenant product design, configuration, approval, and lifecycle management. This is the WHAT — every party subscribes to products, every product has pricing, every product instance has a lifecycle governed by the kinetic layer.

#### Ontology Alignment

The product domain maps directly to ontology node types, interfaces, and kinetic state:

```
Ontology Node Type          Product Service Implementation
─────────────────           ──────────────────────────────
ProductDefinition           Template; reusable across tenants
│   ├── pricing_rules       Base pricing logic
│   ├── configurable_properties  Schema of what can vary
│   ├── terms_and_conditions  Legal framework
│   └── product_category    LOB classification
│
ProductInstance             Tenant-specific instantiation
│   ├── pricing             Computed from template + tenant override
│   ├── features            Subset of configurable_properties
│   └── lifecycle_status    Kinetic property (DRAFT→APPROVED→ACTIVE→DEPRECATED)
│
ProductBundle               Composite offering
    └── CONTAINS → ProductInstance  (relationship, not document)
```

**Interface implementations:**

| Interface | Implemented By | Purpose |
|-----------|---------------|---------|
| `IHasPricing` | ProductInstance | Pricing computation across product types |
| `IIsBundleMember` | ProductInstance | Bundle composition queries |
| `IIsCrossSellTarget` | ProductInstance | Recommendation engine |

#### Product Lifecycle (Kinetic State Machine)

Product instances follow a lifecycle governed by the kinetic layer:

```
DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED → ACTIVE → DEPRECATED
  │         │            │             │          │          │
  │         │            │             │          │          └─ Action: DeprecateProduct
  │         │            │             │          └─ Action: ActivateProduct
  │         │            │             └─ Action: ApproveProductConfiguration
  │         │            └─ Workflow: DMN rules + approver routing
  │         └─ Action: SubmitProductConfiguration
  └─ Action: CreateProductInstance
```

Each state transition is an **ontology action** executed through the Entity Platform API:

| State Transition | Action Type | Governance Mode | Pre-flight Rules |
|-----------------|-------------|----------------|------------------|
| DRAFT → SUBMITTED | `SubmitProductConfiguration` | IMMEDIATE | Tenant validation, pricing within policy |
| SUBMITTED → UNDER_REVIEW | (automatic via workflow) | IMMEDIATE | None |
| UNDER_REVIEW → APPROVED | `ApproveProductConfiguration` | IMMEDIATE | Approver mandate validation, DMN rules pass |
| APPROVED → ACTIVE | `ActivateProduct` | IMMEDIATE | All dependencies resolved |
| ACTIVE → DEPRECATED | `DeprecateProduct` | PROPOSED | Compliance review, customer notification |

#### Cross-Sell & Bundling (Graph Traversal)

Cross-sell recommendations leverage the graph structure — not MongoDB document queries:

```
Query: "What products can we offer to parties similar to Nexus Global?"

MATCH
  (target:Party {id: 'nexus-global'})
  -[:subscribedTo]->(current:ProductInstance)
  -[:BELONGS_TO_CATEGORY]->(cat:ProductCategory)
  <-[:BELONGS_TO_CATEGORY]-(similar:ProductInstance)
  WHERE NOT (target)-[:subscribedTo]->(similar)
  AND similar.lifecycle_status = 'ACTIVE'
RETURN similar, count(*) AS adoptionCount
ORDER BY adoptionCount DESC
```

Bundling uses the same graph traversal:

```
Query: "What products are commonly bundled with Cash Management?"

MATCH
  (bundle:ProductBundle)
  -[:CONTAINS]->(cm:ProductInstance {product_category: 'Cash Management'})
  -[:CONTAINS]->(other:ProductInstance)
WHERE other <> cm
RETURN other.product_name, count(*) AS bundleCount
ORDER BY bundleCount DESC
```

These queries are **impossible with MongoDB** — they require native graph traversal. They become <5ms with Neo4j indexes.

#### Product Catalog (Nexus Global Example)

```
ProductDefinition: FX Forward (PROD-003)
  ├── pricing_rules: { base_spread: 0.5%, volume_discount: true }
  ├── configurable_properties: { tenor, currency_pairs, settlement_date }
  └── product_category: "Foreign Exchange"
       │
       ├─[:INSTANTIATED_AS]──→ ProductInstance: FX Forward - Nexus Global
       │    ├── pricing: { base_spread: 0.45% }  ← tenant override
       │    ├── features: { tenor: [1M, 3M, 6M], currency_pairs: [USD/CAD] }
       │    ├── lifecycle_status: ACTIVE
       │    └── implements: [IHasPricing, IIsBundleMember]
       │
       └─[:INSTANTIATED_AS]──→ ProductInstance: FX Forward - ABC Corp
            ├── pricing: { base_spread: 0.55% }  ← different tenant
            ├── features: { tenor: [1M, 3M], currency_pairs: [USD/EUR] }
            ├── lifecycle_status: APPROVED
            └── implements: [IHasPricing]

ProductBundle: Treasury Suite
  ├─[:CONTAINS]──→ FX Forward (IIsBundleMember)
  ├─[:CONTAINS]──→ Cash Management (IIsBundleMember)
  └─[:CONTAINS]──→ Liquidity Pooling (IIsBundleMember)
```

#### Key Changes from v2

| Aspect | v2 (MongoDB) | v3 (Ontology) |
|--------|-------------|---------------|
| Product templates | MongoDB document | Neo4j `ProductDefinition` node |
| Solution instances | MongoDB document | Neo4j `ProductInstance` node |
| Bundles | MongoDB document with array | Neo4j `ProductBundle` + `CONTAINS` relationships |
| Cross-sell rules | MongoDB document | PostgreSQL `function_definitions` + Neo4j traversal |
| Lifecycle state | MongoDB field | PostgreSQL kinetic state machine |
| Pricing computation | Application logic | PostgreSQL `computeProductEligibility` function |
| Approval workflow | MongoDB + Temporal | PostgreSQL kinetic + Temporal + proof registry |

---

### Intelligent Workflow Orchestration

**Purpose:** Hybrid human-AI approval workflows with regulatory-grade evidentiary chains.

#### Ontology + Kinetic Alignment

Workflows are not standalone processes — they are the execution surface for ontology actions with REVIEWED or PROPOSED governance modes.

```
Ontology Action              Kinetic Implementation
─────────────                ──────────────────────
Action Type (declared)    →  kinetic.action_types
    ├── pre_flight_rules  →  kinetic.business_rules
    ├── governance_mode   →  workflow pattern selection
    └── effects           →  graph mutations + proof records

Action Instance (runtime) →  kinetic.action_instances
    ├── status            →  saga state (PENDING→COMPLETED/COMPENSATED)
    ├── proof_chain_id    →  proof.proof_chains
    └── compensating_action → kinetic.compensating_actions

Review Queue               →  kinetic.review_queue
    ├── item_type         →  proposed_edge | reviewed_action
    ├── review_sla        →  escalation trigger
    └── assigned_reviewer →  mandate scope check
```

#### Workflow Patterns

1. **Rule-Based** — DMN tables evaluate business rules; auto-approve or route to approver
2. **Async Red Flag** — AI agents run in parallel; any red flag terminates immediately
3. **Sync Enrichment** — AI agents run sequentially to add metadata before DMN evaluation
4. **Hybrid** — Combination of the above

#### Workflow Example: Product Configuration Approval

```
1. Product Manager submits configuration
   → POST /actions/submit-product-configuration
   → Action Type governance_mode: IMMEDIATE
   → Pre-flight: tenant validation, pricing within policy
   → Effect: ProductInstance.lifecycle_status = SUBMITTED
   → Proof record appended (actor: Product Manager, authority: ROLE_PRODUCT_MANAGER)

2. Workflow triggered by event
   → Kafka: solution.configured
   → Workflow Service creates Temporal workflow
   → DMN evaluates: pricingVariance = 18.5% > 15% threshold
   → Routes to VP Finance (mandate scope validated)

3. AI agent runs enrichment (Async Red Flag pattern)
   → AgentMandate validated (<1ms via Redis)
   → Agent checks: sanctions, KYC, pricing anomaly
   → No red flags → workflow continues

4. VP Finance approves
   → POST /actions/approve-product-configuration
   → Action Type governance_mode: IMMEDIATE
   → Pre-flight: approver mandate validation
   → Effect: ProductInstance.lifecycle_status = APPROVED
   → Proof record appended (actor: VP Finance, authority: ROLE_APPROVER)

5. Product activated
   → POST /actions/activate-product
   → Effect: ProductInstance.lifecycle_status = ACTIVE
   → Proof record appended
   → CDC sync: Neo4j → Kafka → Delta Lake
```

#### Key Changes from v2

| Aspect | v2 (MongoDB) | v3 (Ontology) |
|--------|-------------|---------------|
| Workflow state | MongoDB collections | PostgreSQL `kinetic.action_instances` |
| Audit trail | MongoDB audit logs | PostgreSQL `proof.proof_records` (append-only, hash-chained) |
| Business rules | DMN engine (in-memory) | PostgreSQL `kinetic.business_rules` + DMN evaluation |
| Agent actions | Claude MCP (unbounded) | Claude MCP + mandate scope validation (<1ms) |
| Review queue | MongoDB collection | PostgreSQL `kinetic.review_queue` |
| Compensation | Manual rollback | PostgreSQL `kinetic.compensating_actions` (saga pattern) |

---

### Core Banking Integration

**Purpose:** Seamless integration with legacy core banking systems.

**Integration Patterns:**
- **Customer Sync:** Core → Party Service (via CDC or batch)
- **Product Routing:** Context enriched with CIF, branch code
- **Transaction Posting:** Product Service → Core Banking API
- **Balance Inquiry:** Real-time queries via adapter

**Key Changes from v2:**
- Core banking party data ingested through **Containment Zone** (vendor isolation)
- Progressive mapping lifts signal from core banking terms to canonical ontology
- Adapter pattern retained for vendor abstraction

---

## Integration Architecture

### Event-Driven Integration (Kafka)

**Topics:**
```
product.catalog.created
product.solution.configured
workflow.submitted
workflow.approved
workflow.rejected
party.synced
party.cic.detected
approval.task.assigned
notification.sent
```

**Event Flow Example: Product Configuration → Workflow**
```
1. Product Service publishes: solution.configured
   { "solutionId": "sol-001", "tenantId": "org-acme-bank-001", "pricingVariance": 18.5 }

2. Workflow Service consumes: solution.configured
   Creates workflow instance with:
   - Template: product-configuration-approval
   - Entity: solution.configured
   - DMN input: pricingVariance = 18.5

3. Workflow Service publishes: workflow.submitted
   { "workflowId": "wf-001", "solutionId": "sol-001" }
```

**CDC Flows (New in v3):**
```
Neo4j → APOC triggers → Kafka → Databricks (Delta Lake mirror)
PostgreSQL → Debezium → Kafka → Databricks (Delta Lake mirror)
```

### RESTful Integration

**Context Resolution (Synchronous):**
```
API Gateway → Party Service
POST /api/v1/context/resolve
Request:
{
  "principalId": "admin",
  "username": "admin@acmebank.com",
  "roles": ["ROLE_ADMIN"],
  "channelId": "WEB"
}

Response (~900ms cold, <100ms cached):
{
  "context": {
    "tenantId": "org-acme-bank-001",
    "partyId": "ind-admin-001",
    "partyType": "INDIVIDUAL",
    "permissions": {...},
    "relationships": [...],
    "mandateScope": {...},
    "valid": true
  },
  "resolutionTimeMs": 900,
  "cached": false
}
```

---

## Security Architecture

### Authentication & Authorization Flow

```
1. Client → Auth Service: POST /api/v1/auth/login
   Request: { "username": "alice@acmebank.com", "password": "***" }
   Response: { "token": "***", "expiresIn": 3600 }

2. Client → API Gateway: Authorization: Bearer ***
   Gateway validates JWT signature and expiration

3. Gateway → Party Service: POST /api/v1/context/resolve
   Request: { "principalId": "alice@acmebank.com", "roles": ["ROLE_ADMIN"] }
   Response: ProcessingContext (tenantId, partyId, permissions, mandateScope)

4. Gateway adds headers:
   X-Processing-Context: eyJ0ZW5hbnRJZC... (Base64 JSON)
   X-Tenant-ID: org-acme-bank-001
   X-Party-ID: ind-admin-001
   X-Request-ID: 123e4567-e89b-12d3-a456-426614174000

5. Business Service extracts context:
   ProcessingContext context = ContextHolder.getRequiredContext();
   String tenantId = context.getTenantId(); // org-acme-bank-001

6. Repository queries filtered by tenant:
   // Neo4j: MATCH (p:Party) WHERE p.tenantId = $tenantId
   // PostgreSQL: WHERE domain_scope @> ARRAY[$tenantId]
```

### Role-Based Access Control (RBAC)

**Roles:**
- `ROLE_ADMIN`: System administration
- `ROLE_PRODUCT_MANAGER`: Product catalog management
- `ROLE_TENANT_ADMIN`: Tenant configuration
- `ROLE_APPROVER`: Workflow approvals
- `ROLE_COMPLIANCE_OFFICER`: Override decisions
- `ROLE_USER`: Read-only access

**Key Changes from v2:**
- RBAC roles become the **HumanMandate tier** in the three-tier mandate hierarchy
- SystemMandate and AgentMandate tiers added for automated operations
- Permission checks now include **mandate scope validation** (not just RBAC)

### Tenant Isolation

**Enforcement Layers:**
1. **Context Resolution:** Tenant ID automatically resolved from party organization hierarchy
2. **Header Injection:** X-Tenant-ID injected by API Gateway on every request
3. **Neo4j:** All queries filtered by `tenantId` property
4. **PostgreSQL:** Row-Level Security via `domain_scope` array column
5. **Delta Lake:** Unity Catalog with separate LOB catalogs; RLS at table level

### Data Encryption

- **At Rest:** AES-256 (Azure Storage + Neo4j + PostgreSQL)
- **In Transit:** TLS 1.3 (all service-to-service communication)
- **Keys:** Azure Key Vault (centralized key management)

---

## Deployment Architecture

### Azure Cloud (Primary)

| Resource | Purpose | Tier |
|----------|---------|------|
| **Azure Cache for Redis** | Hot cache (entitlements, mandates, context) | Enterprise (cluster mode) |
| **Azure Cosmos DB** (→ Neo4j) | Graph database (party graph + product ontology) | Dedicated throughput |
| **Azure Database for PostgreSQL** | Kinetic layer + proof registry + mandates | Business Critical |
| **Azure Databricks** | Delta Lake analytics + LOB projections + containment zone | Premium |
| **Azure Container Apps** | Microservices (Party, Product, Workflow, Auth) | Serverless |
| **Azure Event Hubs** (→ Kafka) | Event streaming (product, workflow, party events) | Dedicated |
| **Azure Key Vault** | Secrets management (DB credentials, API keys) | Standard |
| **Azure Monitor** | Observability (metrics, logs, traces) | Standard |
| **Azure API Management** | API Gateway (JWT validation, context resolution, rate limiting) | Premium |

### On-Premises (Legacy Core)

| System | Purpose | Integration |
|--------|---------|-------------|
| **Core Banking** | Transaction processing, account management | Adapter pattern + Containment Zone |
| **Trade Finance** | Vendor-hosted trade finance operations | Containment Zone + progressive mapping |
| **SWIFT** | Payment messaging | Core Banking adapter |

### Environment Strategy

| Environment | Purpose | Scale |
|-------------|---------|-------|
| **Development** | Individual developer work | Minimal |
| **Staging** | Integration testing, UAT | 50% Production |
| **Production** | Live operations | Full |

---

## Performance & Scalability

### Latency Targets

| Operation | Target | Store |
|-----------|--------|-------|
| Multi-hop graph traversal | <5ms p99 | Neo4j |
| Mandate pre-flight validation | <1ms p99 | Redis + PostgreSQL |
| Context resolution (cold) | <100ms | Neo4j |
| Context resolution (cached) | <10ms | Redis |
| Action execution (end-to-end) | <200ms p99 | Neo4j + PostgreSQL |
| Proof chain retrieval | <200ms p99 | PostgreSQL |
| CDC sync lag | <5s | Neo4j/PostgreSQL → Delta Lake |

### Volume Estimates (Year 1 — Nexus Global)

| Store | Entity | Count | Storage |
|-------|--------|-------|---------|
| **Neo4j** | Nodes | ~28K | ~500MB |
| **Neo4j** | Edges | ~62K | ~1GB |
| **PostgreSQL** | Proof records | ~188K | ~500MB |
| **PostgreSQL** | Kinetic records | ~50K | ~100MB |
| **PostgreSQL** | Mandate records | ~500 | ~10MB |
| **Redis** | Cached entries | ~10K | ~50MB |
| **Delta Lake** | Historical data | ~1M rows/day | ~5GB/day |

### Scaling Strategy

- **Neo4j:** Horizontal read replicas (Causal Cluster); write scaling via sharding if needed
- **PostgreSQL:** Read replicas for analytical queries; partitioning for proof_records by time
- **Redis:** Cluster mode for horizontal scaling
- **Delta Lake:** Automatic scaling via Databricks clusters
- **Services:** Horizontal scaling via Container Apps (KEDA auto-scaling)

---

## Service Catalog

| Service | Port | Primary Store | Secondary Store | Purpose |
|---------|------|--------------|-----------------|---------|
| **API Gateway** | 8080 | — | — | JWT validation, context resolution, rate limiting, routing |
| **Auth Service** | 8084 | PostgreSQL | — | JWT token management, principal CRUD |
| **Party Service** | 8083 | Neo4j | Redis | Party graph management, context resolution, party CRUD |
| **Product Service** | 8081 | Neo4j | PostgreSQL | Product catalog management, solution configuration, pricing |
| **Bundle Service** | 8082 | Neo4j | PostgreSQL | Product bundle management, cross-sell recommendations |
| **Workflow Service** | 8089 | PostgreSQL | Neo4j | Workflow orchestration, DMN evaluation, Temporal integration |
| **Notification Service** | 8086 | PostgreSQL | — | Multi-channel notifications (email, SMS, push, in-app) |
| **Entity Platform API** | 8090 | Neo4j + PostgreSQL | Redis + Delta Lake | Ontology action surface, proof chain retrieval, mandate validation |

---

## Architecture Decision Records

### ADR-001: Ontology-First Architecture

**Status:** Accepted
**Date:** 2026-05-23

**Context:** Previous architecture used MongoDB as the primary data store. This approach lacked native graph traversal, ACID transactional semantics for the kinetic layer, and regulatory-grade evidentiary chains.

**Options Considered:**
| Option | Pros | Cons |
|--------|------|------|
| MongoDB (existing) | Team familiarity, flexible schema | No graph traversal, weak ACID, no proof chains |
| Delta Lake Only | Unified platform, good analytics | No operational graph traversal, no real-time ACID |
| Three-Store (Neo4j + PostgreSQL + Delta Lake) | Graph traversal, ACID, analytics separation, proof chains | More operational complexity |

**Decision:** Three-Store Architecture (Neo4j + PostgreSQL + Delta Lake + Redis)

**Rationale:**
1. **Neo4j** for operational graph traversal (<5ms multi-hop queries)
2. **PostgreSQL** for kinetic layer + proof registry (ACID transactions, append-only enforcement, hash chaining)
3. **Delta Lake** for analytics + temporal history (CDC-synced mirror, never source of truth)
4. **Redis** for sub-millisecond cache (entitlements, mandates, context)

**Consequences:**
- Cross-store consistency requires Saga pattern (implemented in Dim 02 §6)
- Team training needed for Neo4j/Cypher
- CDC pipeline required to sync operational stores to Delta Lake

### ADR-002: PostgreSQL Over QLDB for Proof Registry

**Status:** Accepted
**Date:** 2026-05-22

**Context:** Proof registry requires append-only enforcement, hash chaining, and regulatory examination readiness.

**Options Considered:**
| Option | Pros | Cons |
|--------|------|------|
| PostgreSQL | Team familiarity, Azure-native, co-located with kinetic, works | Manual append-only enforcement via triggers |
| QLDB | Native append-only, regulatory narrative | Additional AWS dependency, team unfamiliarity, separate from kinetic |

**Decision:** PostgreSQL

**Rationale:** Operational simplicity and team familiarity outweigh QLDB's regulatory narrative advantage. Append-only enforcement via triggers is proven and sufficient.

### ADR-003: Saga Pattern for Cross-Store Consistency

**Status:** Accepted
**Date:** 2026-05-22

**Context:** Action execution writes to both Neo4j (graph mutation) and PostgreSQL (proof + action instance). Need to guarantee consistency without distributed transactions.

**Options Considered:**
| Option | Pros | Cons |
|--------|------|------|
| 2PC (XA) | Strong consistency | Neo4j lacks XA support |
| Outbox Pattern | Simple | Doesn't handle cross-store atomicity |
| Saga Pattern | Aligns with ontology's two-phase write model, clear recovery semantics | Complexity, requires compensation logic |

**Decision:** Saga Pattern

**Rationale:** Aligns with ontology's two-phase write model (proposed → reviewed → active). Provides clear recovery semantics via compensating actions.

### ADR-004: Entity Platform API Over CRUD REST

**Status:** Accepted
**Date:** 2026-05-22

**Context:** Need a single, governed interface to the canonical graph.

**Options Considered:**
| Option | Pros | Cons |
|--------|------|------|
| CRUD REST | Simple, familiar | No ontology awareness, no proof enforcement |
| GraphQL | Flexible queries | Complex, no action semantics |
| Ontology Action Surface | Declared actions, proof mandatory, governance-aware | Learning curve |

**Decision:** Ontology Action Surface

**Rationale:** Actions and functions are first-class ontology constructs. The API surface directly reflects the ontology declaration, ensuring governance, proof, and mandate validation are baked in.

---

## Glossary

| Term | Definition |
|------|------------|
| **Canonical Graph** | The single source of truth for entity relationships, stored in Neo4j |
| **Kinetic Layer** | The operational state machine that governs how actions execute and the graph evolves |
| **Proof Registry** | Append-only, hash-chained event log of every relationship change |
| **Mandate** | Three-tier delegation hierarchy (Human → System → Agent) governing automated actions |
| **Ontology Action** | A declared operation with pre-flight rules, effects, and governance mode |
| **Ontology Function** | Versioned business logic, stored and evaluated by the platform |
| **Interface** | Polymorphic capability declaration (e.g., IHasBalance, IIsSettlementTarget) |
| **Containment Zone** | Semantic buffer for vendor-hosted data, isolated from canonical graph |
| **CDC** | Change Data Capture; syncs operational stores to Delta Lake |
| **Saga Pattern** | Cross-store consistency pattern for Neo4j + PostgreSQL atomicity |
| **Two-Phase Write** | Edges proposed in PostgreSQL, reviewed, then promoted to Neo4j |
| **Context Resolution** | Transforming JWT principal → complete ProcessingContext (tenant, party, permissions, mandate scope) |
| **LEI** | Legal Entity Identifier; global standard for entity identification |
| **UBO** | Ultimate Beneficial Owner; person who ultimately owns/controls an entity |
| **DMN** | Decision Model and Notation; standard for business rule modeling |
| **Temporal** | Workflow orchestration engine for durable execution |
| **ZKP** | Zero-Knowledge Proof; verify claims without exposing underlying evidence |

---

## Appendix A: Data Flow — Product Configuration Example

```
1. User configures product in UI
   → POST /api/v1/products/solutions
   → Product Service (Neo4j: create ProductInstance node)
   → Publishes: solution.configured

2. Workflow triggered
   → Workflow Service consumes: solution.configured
   → Evaluates DMN rules (PostgreSQL: business_rules table)
   → Creates workflow instance (PostgreSQL: action_instances table)
   → Publishes: workflow.submitted

3. AI agent runs enrichment
   → Agent mandate validated (Redis + PostgreSQL: mandate.mandates)
   → Agent enriches workflow with metadata
   → Publishes: workflow.enriched

4. Approver reviews
   → DMN evaluates: pricingVariance = 18.5% > 15% threshold
   → Routes to VP Finance
   → Approver approves via UI
   → Workflow Service: workflow.approved

5. Proof chain created
   → Entity Platform API: POST /actions/approve-product-configuration
   → PostgreSQL: proof.proof_records (append-only, hash-chained)
   → Neo4j: ProductInstance status → ACTIVE

6. Analytics updated
   → CDC: Neo4j → Kafka → Databricks (Delta Lake mirror)
   → LOB projections refreshed
```

## Appendix B: Data Flow — Party Context Resolution Example

```
1. User logs in
   → POST /api/v1/auth/login
   → Auth Service: validates credentials (PostgreSQL: auth_principals)
   → Returns: JWT token

2. User makes API call
   → GET /api/v1/products (Authorization: Bearer <JWT>)
   → API Gateway: validates JWT signature
   → API Gateway: calls Party Service for context resolution

3. Context resolution
   → Party Service: POST /api/v1/context/resolve
   → Neo4j: MATCH (p:Principal {id: $principalId})-[:isPartyOf]->(party)
   → Neo4j: MATCH (party)-[:belongsTo]->(tenant)
   → Neo4j: MATCH (party)-[:hasPermission]->(perm)
   → PostgreSQL + Redis: mandate scope validation
   → Returns: ProcessingContext

4. Context injected
   → API Gateway adds headers: X-Processing-Context, X-Tenant-ID, X-Party-ID
   → Product Service extracts context: ContextHolder.getRequiredContext()
   → Query filtered: WHERE tenantId = $tenantId

5. Response returned
   → Product Service: returns tenant-scoped product list
   → API Gateway: forwards response to client
```

## Appendix C: Vendor Containment Zone Example

```
1. Vendor data ingested
   → POST /containment/ingest
   → Vendor system: Trade Finance (PROD-TF-001)
   → Data stored in: tb_containment.catalog (Delta Lake)
   → Mapping status: Partial

2. Progressive mapping
   → Vendor term: "LetterOfCredit"
   → Canonical term: "TradeFinanceInstrument"
   → Mapping: vendorTerm → canonicalTerm (tracked in vendor_mapping_status)

3. Full mapping achieved
   → Mapping status: Complete
   → Vendor data accessible via canonical ontology
   → Containment zone data can be safely joined with canonical graph

4. Vendor isolation
   → Vendor data never directly writes to canonical graph
   → All vendor data passes through containment zone
   → Progressive mapping ensures semantic alignment
   → Separate Unity Catalog (tb_containment) with separate governance
```

---

*End of Master Architecture Document v3.0*
*Next: Implementation planning, Phase 1 scoping, vendor API contract review*
</parameter> </function> </tool_call></parameter> </tool_call></function> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter> </tool_call></parameter